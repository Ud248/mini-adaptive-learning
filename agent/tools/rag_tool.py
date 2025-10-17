from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple, Callable

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore

try:
    # Milvus client (project-local thin wrapper)
    from database.milvus import milvus_client as mc  # type: ignore
except Exception:  # pragma: no cover
    mc = None  # type: ignore

try:
    # Local Vietnamese embedder
    from database.embeddings.local_embedder import embed_text_quick  # type: ignore
except Exception:  # pragma: no cover
    embed_text_quick = None  # type: ignore

try:
    # MongoDB client for image enrichment
    from database.mongodb import mongodb_client as mongo  # type: ignore
except Exception:  # pragma: no cover
    mongo = None  # type: ignore


_DEFAULT_TOPK_SGV = 5
_DEFAULT_TOPK_SGK = 20
_DEFAULT_CACHE_TTL = 900  # seconds


def _load_rag_config() -> Dict[str, Any]:
    """Load RAG config from configs/agent.yaml if available.

    Safe fallback to defaults when yaml or file not present.
    """
    config_path = os.path.join(os.getcwd(), "configs", "agent.yaml")
    cfg: Dict[str, Any] = {}
    if yaml is None:
        return cfg
    try:
        if os.path.isfile(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                cfg = data.get("rag", {}) or {}
    except Exception:
        # ignore config errors, use defaults
        cfg = {}
    return cfg


def _normalize_lesson(name: Optional[str]) -> Optional[str]:
    """
    Normalize lesson text theo cùng logic với insert_sgv_to_milvus.py
    để match với normalized_lesson field trong database
    """
    if not name:
        return None
    
    import re
    
    # Bước 1: Chuyển về lowercase
    text = name.strip().lower()
    
    # Bước 2: Loại bỏ số tiết trong ngoặc
    text = re.sub(r'\(\s*\d+\s*tiết\s*\)', '', text)
    text = re.sub(r'\(\s*\d+\s*\)', '', text)
    text = re.sub(r'\(\s*tiết\s*\)', '', text)
    text = re.sub(r'\(\s*\d+tiết\s*\)', '', text)  # Không có space
    text = re.sub(r'\(\s*\d+tiết\)', '', text)  # Không có space cuối
    
    # Bước 3: Loại bỏ "Bài X." prefix
    text = re.sub(r'^bài\s+\d+\.\s*', '', text)
    
    # Bước 4: Loại bỏ "Chủ đề X." prefix  
    text = re.sub(r'^chủ đề\s+\d+\.\s*', '', text)
    
    # Bước 5: Loại bỏ dấu câu thừa
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Bước 6: Chuẩn hóa khoảng trắng
    text = re.sub(r'\s+', ' ', text)
    
    # Bước 7: Loại bỏ từ phụ
    stop_words = ['tiết', 'bài', 'phần', 'chương', 'mục']
    words = text.split()
    words = [word for word in words if word not in stop_words]
    
    return ' '.join(words).strip()


def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def _to_similarity(distance: float) -> float:
    # Milvus distance varies by metric; for COSINE it might return smaller=closer.
    # Map to similarity in [0,1] using a simple transform.
    # Avoid division by zero; clamp result.
    sim = 1.0 / (1.0 + max(distance, 0.0))
    if sim < 0.0:
        return 0.0
    if sim > 1.0:
        return 1.0
    return sim


class RAGTool:
    def __init__(
        self,
        *,
        milvus: Any | None = None,
        embed_fn: Optional[Callable[[str], Optional[List[float]]]] = None,
        collections: Optional[Dict[str, str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._cfg = {**{
            "topk_sgv": _DEFAULT_TOPK_SGV,
            "topk_sgk": _DEFAULT_TOPK_SGK,
            "cache_ttl_s": _DEFAULT_CACHE_TTL,
        }, **(_load_rag_config() or {}), **(config or {})}

        self._milvus = milvus or mc
        self._embed_fn = embed_fn or (embed_text_quick if embed_text_quick else None)
        self._collections = collections or {
            "sgv": "sgv_collection",
            "sgk": "baitap_collection",
        }

        # Simple in-memory cache
        self._cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

        images_cfg = self._cfg.get("images") or {}
        base_url = images_cfg.get("base_url", "")
        base_url = str(base_url).strip()
        self._image_base_url = str(base_url).rstrip("/") if base_url else ""

    # ------------------------------
    # Public API
    # ------------------------------
    def query(
        self,
        *,
        grade: Optional[int],
        skill: str,
        skill_name: Optional[str],
        topk_sgv: int = _DEFAULT_TOPK_SGV,
        topk_sgk: int = _DEFAULT_TOPK_SGK,
    ) -> Dict[str, Any]:
        # Resolve defaults from config
        topk_sgv = topk_sgv or int(self._cfg.get("topk_sgv", _DEFAULT_TOPK_SGV))
        topk_sgk = topk_sgk or int(self._cfg.get("topk_sgk", _DEFAULT_TOPK_SGK))
        cache_ttl = int(self._cfg.get("cache_ttl_s", _DEFAULT_CACHE_TTL))

        cache_key = self._make_cache_key(grade, skill, skill_name, topk_sgv, topk_sgk)
        cached = self._cache_get(cache_key, cache_ttl)
        if cached is not None:
            return cached

        teacher_context = self._search_sgv(grade, skill, skill_name, topk_sgv)
        textbook_context = self._search_sgk(grade, skill, skill_name, topk_sgk)
        textbook_context = self._enrich_sgk_images(textbook_context)

        result = {
            "teacher_context": teacher_context,
            "textbook_context": textbook_context,
        }
        self._cache_set(cache_key, result)
        return result

    # ------------------------------
    # Internal helpers
    # ------------------------------
    def _make_cache_key(
        self,
        grade: Optional[int],
        skill: str,
        skill_name: Optional[str],
        topk_sgv: int,
        topk_sgk: int,
    ) -> str:
        payload = {
            "grade": grade,
            "skill": skill,
            "skill_name": skill_name,
            "topk_sgv": topk_sgv,
            "topk_sgk": topk_sgk,
        }
        return _md5(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    def _cache_get(self, key: str, ttl: int) -> Optional[Dict[str, Any]]:
        now = time.time()
        item = self._cache.get(key)
        if not item:
            return None
        ts, val = item
        if now - ts > ttl:
            # expired
            self._cache.pop(key, None)
            return None
        return val

    def _cache_set(self, key: str, val: Dict[str, Any]) -> None:
        self._cache[key] = (time.time(), val)

    def _build_expr(self, *, normalized_lesson: Optional[str]) -> Optional[str]:
        if not normalized_lesson:
            return None
        # Query normalized_lesson field để match với database
        return f'normalized_lesson == "{normalized_lesson}"'
    
    def _build_prefix_expr(self, field: str, value: str) -> Optional[str]:
        """
        Build prefix pattern expression for Milvus LIKE queries.
        Milvus only supports prefix patterns (ab%) not wildcards (%ab%).
        """
        if not value or not value.strip():
            return None
        # Use prefix pattern for Milvus compatibility
        return f'{field} like "{value.strip()}%"'

    def _embed_query_text(self, *, skill: str, skill_name: Optional[str], grade: Optional[int]) -> Optional[List[float]]:
        if self._embed_fn is None:
            return None
        parts = [skill_name or skill]
        if grade is not None:
            parts.append(f"lớp {grade}")
        text = " ".join([p for p in parts if p])
        try:
            return self._embed_fn(text)
        except Exception:
            return None

    def _search_sgv(self, grade: Optional[int], skill: str, skill_name: Optional[str], k: int) -> List[Dict[str, Any]]:
        collection = self._collections["sgv"]
        normalized = _normalize_lesson(skill_name)
        expr = self._build_expr(normalized_lesson=normalized)
        rows: List[Dict[str, Any]] = []

        # Stage 1: metadata filter
        try:
            if self._milvus is not None and expr:
                rows = self._milvus.query(
                    collection, expr=expr, output_fields=["id", "lesson", "normalized_lesson", "content", "source"], limit=k
                ) or []
        except Exception:
            rows = []

        # Stage 2: vector search fallback if needed
        if not rows:
            vec = self._embed_query_text(skill=skill, skill_name=skill_name, grade=grade)
            if vec is not None and self._milvus is not None:
                try:
                    hits = self._milvus.search(
                        collection_name=collection,
                        vector_field="embedding",
                        query_vectors=[vec],
                        param={"metric_type": "L2", "params": {"nprobe": 10}},
                        limit=max(k * 3, k),
                        output_fields=["id", "lesson", "normalized_lesson", "content", "source"],
                    ) or []
                    rows = self._format_hits(hits)
                except Exception:
                    rows = []

        # Rerank + dedup
        items = []
        for r in rows:
            text = r.get("content", "")
            lesson = r.get("lesson", "")
            score_sim = r.get("distance")
            if isinstance(score_sim, (int, float)):
                sim = _to_similarity(float(score_sim))
            else:
                sim = 0.5  # neutral if not from vector search
            lesson_match = 1.0 if normalized and normalized == _normalize_lesson(lesson) else 0.0
            grade_match = 0.0  # grade not enforced in schema
            final = 0.6 * sim + 0.3 * lesson_match + 0.1 * grade_match
            items.append({
                "id": str(r.get("id", "")),
                "text": text,
                "source": r.get("source", ""),
                "lesson": lesson,
                "score": float(final),
            })

        return self._rerank_and_trim(items, k)

    def _search_sgk(self, grade: Optional[int], skill: str, skill_name: Optional[str], k: int) -> List[Dict[str, Any]]:
        collection = self._collections["sgk"]
        normalized = _normalize_lesson(skill_name)
        expr = self._build_expr(normalized_lesson=normalized)
        rows: List[Dict[str, Any]] = []

        # Stage 1: metadata filter
        try:
            if self._milvus is not None and expr:
                rows = self._milvus.query(
                    collection,
                    expr=expr,
                    output_fields=["id", "lesson", "normalized_lesson", "question", "answer", "subject", "source"],
                    limit=k,
                ) or []
        except Exception:
            rows = []

        # Stage 2: vector search fallback if needed
        if not rows:
            vec = self._embed_query_text(skill=skill, skill_name=skill_name, grade=grade)
            if vec is not None and self._milvus is not None:
                try:
                    hits = self._milvus.search(
                        collection_name=collection,
                        vector_field="embedding",
                        query_vectors=[vec],
                        param={"metric_type": "L2", "params": {"nprobe": 10}},
                        limit=max(k * 3, k),
                        output_fields=["id", "lesson", "normalized_lesson", "question", "answer", "subject", "source"],
                    ) or []
                    rows = self._format_hits(hits)
                except Exception:
                    rows = []

        # Rerank + dedup
        items = []
        for r in rows:
            question = r.get("question", "")
            answer = r.get("answer", "")
            text = f"Q: {question}\nA: {answer}".strip()
            lesson = r.get("lesson", "")
            score_sim = r.get("distance")
            if isinstance(score_sim, (int, float)):
                sim = _to_similarity(float(score_sim))
            else:
                sim = 0.5
            lesson_match = 1.0 if normalized and normalized == _normalize_lesson(lesson) else 0.0
            grade_match = 0.0
            final = 0.6 * sim + 0.3 * lesson_match + 0.1 * grade_match
            items.append({
                "id": str(r.get("id", "")),
                "text": text,
                "source": r.get("source", ""),
                "lesson": lesson,
                "score": float(final),
            })

        return self._rerank_and_trim(items, k)

    def _format_hits(self, hits: Any) -> List[Dict[str, Any]]:
        # database.milvus.milvus_client.search returns list[list[hit]]
        formatted: List[Dict[str, Any]] = []
        try:
            for hit_list in hits:
                for h in hit_list:
                    # "entity" may be an object with dict-like access. Try to coerce.
                    ent = h.get("entity") if isinstance(h, dict) else None
                    row: Dict[str, Any] = {}
                    if ent is not None:
                        # Pymilvus entity exposes .get(field)
                        try:
                            # Try extracting known fields
                            for f in [
                                "id",
                                "lesson",
                                "normalized_lesson",
                                "content",
                                "source",
                                "question",
                                "answer",
                                "subject",
                            ]:
                                try:
                                    row[f] = ent.get(f)  # type: ignore[attr-defined]
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    # distance/id may be on hit
                    try:
                        if isinstance(h, dict):
                            if "id" in h and not row.get("id"):
                                row["id"] = h.get("id")
                            if "distance" in h:
                                row["distance"] = h.get("distance")
                    except Exception:
                        pass
                    formatted.append(row)
        except Exception:
            return []
        return formatted

    def _rerank_and_trim(self, items: List[Dict[str, Any]], k: int) -> List[Dict[str, Any]]:
        # Deduplicate by text md5; keep max score per hash
        best_by_hash: Dict[str, Dict[str, Any]] = {}
        for it in items:
            text = it.get("text", "")
            h = _md5(text)
            prev = best_by_hash.get(h)
            if prev is None or float(it.get("score", 0.0)) > float(prev.get("score", 0.0)):
                best_by_hash[h] = it
        unique_items = list(best_by_hash.values())
        unique_items.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
        return unique_items[: max(k, 0)]

    def _enrich_sgk_images(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not items or mongo is None:
            return items
        enriched: List[Dict[str, Any]] = []
        for it in items:
            vector_id = it.get("id")
            image_field = None
            try:
                if vector_id:
                    doc = mongo.find_one("textbook_exercises", {"vector_id": vector_id}, projection={"image_question": 1})
                    if doc and doc.get("image_question"):
                        image_field = doc.get("image_question")
            except Exception:
                image_field = None

            def _prefix(u: str) -> str:
                if not u:
                    return u
                # If base URL is not configured, keep original URL
                if not self._image_base_url:
                    return u
                path = u if u.startswith("/") else f"/{u}"
                return f"@{self._image_base_url}{path}"

            if isinstance(image_field, list):
                it["image_question"] = [_prefix(x) for x in image_field if isinstance(x, str)]
            elif isinstance(image_field, str):
                it["image_question"] = _prefix(image_field)
            # else: do not add the field
            enriched.append(it)
        return enriched



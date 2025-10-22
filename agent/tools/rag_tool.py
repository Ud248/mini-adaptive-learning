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

    def _embed_skill_name(self, skill_name: str) -> Optional[List[float]]:
        """Tạo embedding từ skill_name"""
        if self._embed_fn is None:
            return None
        try:
            return self._embed_fn(skill_name)
        except Exception:
            return None

    def _search_sgv(self, grade: Optional[int], skill: str, skill_name: Optional[str], k: int) -> List[Dict[str, Any]]:
        """
        Tìm kiếm SGV theo skill_name
        - Stage 1: Exact match theo metadata (skill_name)
        - Stage 2: Vector search fallback nếu không tìm thấy
        """
        collection = self._collections["sgv"]
        
        if not skill_name:
            return []
        
        rows: List[Dict[str, Any]] = []
        
        # Stage 1: Exact metadata filter
        expr = f'skill_name == "{skill_name}"'
        try:
            if self._milvus is not None:
                rows = self._milvus.query(
                    collection, 
                    expr=expr, 
                    output_fields=["id", "lesson", "skill_name", "content", "source"], 
                    limit=1000  # Lấy tất cả matching documents
                ) or []
                print(f"✓ SGV metadata search: Found {len(rows)} results")
        except Exception as e:
            print(f"⚠️  Error in SGV metadata search: {e}")
            rows = []
        
        # Stage 2: Vector search fallback nếu không có kết quả
        if not rows:
            print(f"⚠️  No metadata results, falling back to vector search...")
            vec = self._embed_skill_name(skill_name)
            if vec is not None and self._milvus is not None:
                try:
                    hits = self._milvus.search(
                        collection_name=collection,
                        vector_field="embedding",
                        query_vectors=[vec],
                        param={"metric_type": "L2", "params": {"nprobe": 10}},
                        limit=max(k * 3, 50),
                        output_fields=["id", "lesson", "skill_name", "content", "source"],
                    ) or []
                    rows = self._format_vector_hits(hits)
                    print(f"✓ SGV vector search: Found {len(rows)} results")
                except Exception as e:
                    print(f"⚠️  Error in SGV vector search: {e}")
                    rows = []
        
        # Chuyển đổi sang format output
        items = []
        for r in rows:
            items.append({
                "id": str(r.get("id", "")),
                "text": r.get("content", ""),
                "source": r.get("source", ""),
                "lesson": r.get("lesson", ""),
                "skill_name": r.get("skill_name", ""),
                "score": 1.0,
            })

        # Dedup và giới hạn số lượng
        return self._rerank_and_trim(items, k)

    def _search_sgk(self, grade: Optional[int], skill: str, skill_name: Optional[str], k: int) -> List[Dict[str, Any]]:
        """
        Tìm kiếm SGK theo skill_name
        - Stage 1: Exact match theo metadata (skill_name)
        - Stage 2: Vector search fallback nếu không tìm thấy
        - Random lấy k câu hỏi
        """
        collection = self._collections["sgk"]
        
        if not skill_name:
            return []
        
        rows: List[Dict[str, Any]] = []
        
        # Stage 1: Exact metadata filter
        expr = f'skill_name == "{skill_name}"'
        try:
            if self._milvus is not None:
                # Lấy nhiều hơn k để có thể random
                rows = self._milvus.query(
                    collection,
                    expr=expr,
                    output_fields=["id", "question_content", "lesson", "skill_name", "source"],
                    limit=max(k * 2, 100),
                ) or []
                print(f"✓ SGK metadata search: Found {len(rows)} results")
        except Exception as e:
            print(f"⚠️  Error in SGK metadata search: {e}")
            rows = []

        # Stage 2: Vector search fallback nếu không có kết quả
        if not rows:
            print(f"⚠️  No metadata results, falling back to vector search...")
            vec = self._embed_skill_name(skill_name)
            if vec is not None and self._milvus is not None:
                try:
                    hits = self._milvus.search(
                        collection_name=collection,
                        vector_field="embedding",
                        query_vectors=[vec],
                        param={"metric_type": "L2", "params": {"nprobe": 10}},
                        limit=max(k * 3, 100),
                        output_fields=["id", "question_content", "lesson", "skill_name", "source"],
                    ) or []
                    rows = self._format_vector_hits(hits)
                    print(f"✓ SGK vector search: Found {len(rows)} results")
                except Exception as e:
                    print(f"⚠️  Error in SGK vector search: {e}")
                    rows = []

        # Chuyển đổi sang format output
        items = []
        for r in rows:
            question_content = r.get("question_content", "")
            text = f"Câu hỏi: {question_content}".strip()
            
            items.append({
                "id": str(r.get("id", "")),
                "text": text,
                "source": r.get("source", ""),
                "lesson": r.get("lesson", ""),
                "skill_name": r.get("skill_name", ""),
                "score": 1.0,
            })

        # Random shuffle và lấy top-k
        import random
        if items:
            random.shuffle(items)
        
        # Dedup và giới hạn số lượng
        return self._rerank_and_trim(items, k)

    def _format_vector_hits(self, hits: Any) -> List[Dict[str, Any]]:
        """
        Format kết quả từ vector search
        Milvus search returns list[list[hit]]
        """
        formatted: List[Dict[str, Any]] = []
        try:
            for hit_list in hits:
                for h in hit_list:
                    # Extract entity data
                    ent = h.get("entity") if isinstance(h, dict) else None
                    row: Dict[str, Any] = {}
                    
                    if ent is not None:
                        # Try extracting known fields
                        try:
                            for f in [
                                "id",
                                "lesson",
                                "skill_name",
                                "content",
                                "source",
                                "question_content",
                            ]:
                                try:
                                    val = ent.get(f)  # type: ignore[attr-defined]
                                    if val is not None:
                                        row[f] = val
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    
                    # Get id and distance from hit
                    try:
                        if isinstance(h, dict):
                            if "id" in h and not row.get("id"):
                                row["id"] = h.get("id")
                            if "distance" in h:
                                row["distance"] = h.get("distance")
                    except Exception:
                        pass
                    
                    if row:  # Only add if we got some data
                        formatted.append(row)
        except Exception as e:
            print(f"⚠️  Error formatting vector hits: {e}")
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



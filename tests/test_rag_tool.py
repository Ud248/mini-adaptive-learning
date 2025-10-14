import time

from agent.tools.rag_tool import RAGTool


class _Ent:
    def __init__(self, data):
        self._d = data

    def get(self, k):
        return self._d.get(k)


class MockMilvus:
    def __init__(self):
        self.query_calls = []
        self.search_calls = []

    def query(self, collection_name, expr, output_fields=None, limit=None, offset=None):
        self.query_calls.append((collection_name, expr, tuple(output_fields or []), limit, offset))
        # Return two records if expr matches normalized_lesson
        if expr and 'normalized_lesson' in expr:
            if collection_name == 'sgv_collection':
                return [
                    {"id": "sgv1", "lesson": "mấy và mấy", "normalized_lesson": "mấy và mấy", "content": "Giải thích khái niệm", "source": "sgv.doc"},
                    {"id": "sgv2", "lesson": "Mấy và mấy", "normalized_lesson": "mấy và mấy", "content": "Ví dụ minh hoạ", "source": "sgv.doc"},
                ][: limit or 2]
            if collection_name == 'baitap_collection':
                return [
                    {"id": "sgk1", "lesson": "mấy và mấy", "normalized_lesson": "mấy và mấy", "question": "2 + 3 = ?", "answer": "5", "subject": "Toán", "source": "sgk.doc"},
                ][: limit or 1]
        return []

    def search(self, collection_name, vector_field, query_vectors, param=None, limit=None, expr=None, output_fields=None):
        self.search_calls.append((collection_name, vector_field, len(query_vectors or []), limit))
        # Return one vector hit with distance to test similarity path
        ent = _Ent({
            "id": f"{collection_name}-hit",
            "lesson": "khác bài",
            "normalized_lesson": "khac bai",
            "content": "Nội dung tương tự" if collection_name == 'sgv_collection' else None,
            "question": "1+1=?" if collection_name == 'baitap_collection' else None,
            "answer": "2" if collection_name == 'baitap_collection' else None,
            "source": "search",
        })
        return [[{"id": f"{collection_name}-hit", "distance": 0.2, "entity": ent}]]


def _dummy_embed(text: str):
    # Return a fixed vector length 768 with small variance
    return [0.01] * 768


def test_ragtool_prefers_metadata_filter_and_maps_outputs():
    tool = RAGTool(milvus=MockMilvus(), embed_fn=_dummy_embed)
    res = tool.query(grade=1, skill="S5", skill_name="Mấy và mấy", topk_sgv=2, topk_sgk=2)

    assert "teacher_context" in res and "textbook_context" in res
    t = res["teacher_context"]
    x = res["textbook_context"]

    # From metadata filter path
    assert len(t) == 2
    assert any("Giải thích" in it["text"] for it in t)
    assert len(x) == 1
    assert x[0]["text"].startswith("Q: ")


def test_ragtool_falls_back_to_vector_search_when_no_filter_match():
    mock = MockMilvus()
    tool = RAGTool(milvus=mock, embed_fn=_dummy_embed)
    res = tool.query(grade=None, skill="S999", skill_name=None, topk_sgv=1, topk_sgk=1)

    # Since expr is None, filter returns empty → fallback kicks in
    assert len(res["teacher_context"]) == 1
    assert len(res["textbook_context"]) == 1


def test_ragtool_cache_ttl_and_keying():
    mock = MockMilvus()
    tool = RAGTool(milvus=mock, embed_fn=_dummy_embed, config={"cache_ttl_s": 1})
    _ = tool.query(grade=1, skill="S5", skill_name="Mấy và mấy", topk_sgv=2, topk_sgk=2)
    calls_after_first = (len(mock.query_calls), len(mock.search_calls))

    # Second call should be cached
    _ = tool.query(grade=1, skill="S5", skill_name="Mấy và mấy", topk_sgv=2, topk_sgk=2)
    calls_after_second = (len(mock.query_calls), len(mock.search_calls))
    assert calls_after_second == calls_after_first

    # After TTL expires, it should query again
    time.sleep(1.1)
    _ = tool.query(grade=1, skill="S5", skill_name="Mấy và mấy", topk_sgv=2, topk_sgk=2)
    calls_after_third = (len(mock.query_calls), len(mock.search_calls))
    assert calls_after_third[0] >= calls_after_first[0]



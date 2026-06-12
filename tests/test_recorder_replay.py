from antigreedy.events import EventStream
from antigreedy.recorder import LLMCache, Recorder, cache_key, read_events


def test_recorder_roundtrip(tmp_path):
    p = tmp_path / "run.jsonl"
    rec = Recorder(p)
    st = EventStream("r", "baseline", 0, sink=rec.emit)
    st.emit("turn", {"agent_id": "A"})
    st.emit("episode_end", {"outcome": "decided"})
    rec.close()
    back = read_events(p)
    assert back == st.events  # replay = identical event sequence

def test_cache_key_sensitivity_and_store(tmp_path):
    k1 = cache_key("m", "p", 0.3, 1)
    assert k1 != cache_key("m", "p2", 0.3, 1) and k1 != cache_key("m2", "p", 0.3, 1)
    c = LLMCache(tmp_path / "cache.json")
    assert c.get(k1) is None
    c.put(k1, {"text": "t", "completion_tokens": 1})
    assert LLMCache(tmp_path / "cache.json").get(k1) == {"text": "t", "completion_tokens": 1}

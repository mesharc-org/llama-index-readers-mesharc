import pytest
from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document

from llama_index.readers.mesharc import MeshArcReader
from tests.fake import FakeMeshArc


def load(mode="scrape", reader_kwargs=None, **load_kwargs):
    client = FakeMeshArc()
    docs = MeshArcReader(client=client, mode=mode, **(reader_kwargs or {})).load_data(**load_kwargs)
    return docs, client


def test_is_a_remote_reader():
    reader = MeshArcReader(client=FakeMeshArc())
    assert isinstance(reader, BaseReader) and reader.is_remote
    assert MeshArcReader.class_name() == "MeshArcReader"


def test_scrape_one_url():
    docs, client = load(url="https://e.test/pricing")
    assert len(docs) == 1 and isinstance(docs[0], Document)
    doc = docs[0]
    assert doc.text.startswith("# Page") and doc.id_ == "https://e.test/pricing"
    assert doc.metadata["url"] == "https://e.test/pricing" and doc.metadata["status"] == 200
    assert doc.metadata["title"] == "Title of https://e.test/pricing" and doc.metadata["mode"] == "scrape"
    assert doc.metadata["verdict"] == "ok" and doc.metadata["page_status"] == "ok"
    assert client.calls == [("scrape", "https://e.test/pricing", {})]


def test_scrape_batch_reads_the_rows_under_pages_and_skips_empty_ones_unless_asked():
    urls = ["https://e.test/a", "https://e.test/blocked", "https://e.test/robots"]
    docs, _ = load(url=urls)
    assert [d.metadata["url"] for d in docs] == ["https://e.test/a"]
    assert docs[0].text == "Text of https://e.test/a." and docs[0].metadata["status"] == 200
    docs, _ = load(url=urls, reader_kwargs={"include_empty": True})
    assert [d.metadata["url"] for d in docs] == urls
    assert docs[1].text == "" and docs[1].metadata["error_code"] == "BLOCKED" and docs[1].metadata["status"] == 403
    assert docs[2].metadata["page_status"] == "robots"


def test_crawl_with_params():
    docs, client = load(mode="crawl", reader_kwargs={"params": {"limit": 2}}, url="https://d.test/")
    assert client.calls[0] == ("crawl", "https://d.test/", {"limit": 2})
    assert [d.metadata["url"] for d in docs] == ["https://d.test/", "https://d.test/a"]
    assert all(d.metadata["crawl_id"] == "crawl_1" for d in docs)
    meta = docs[1].metadata
    assert docs[1].text == "Page a." and meta["page_status"] == "ok"
    assert "status" not in meta and "verdict" not in meta  # a crawl row has only the one-word status


def test_map():
    docs, _ = load(mode="map", url="https://m.test/")
    assert [d.text for d in docs] == ["https://m.test/a", "https://m.test/b"]
    assert docs[0].metadata["lastmod"] == "2026-10-01" and "lastmod" not in docs[1].metadata


def test_changes():
    docs, client = load(mode="changes", project_id="prj_1", run_id="run_2", against="run_0")
    assert client.calls[0] == ("changes", "prj_1", "run_2", "run_0")
    assert [(d.metadata["change"], d.metadata["url"]) for d in docs] == [
        ("added", "https://s.test/new"), ("modified", "https://s.test/price")]
    assert docs[1].text == "Now: https://s.test/price" and docs[1].id_ == "run_2:https://s.test/price"
    assert docs[1].metadata["changed_at"] == "2026-10-15T09:00:00Z"
    assert docs[1].metadata["status"] == 200 and docs[1].metadata["title"] == "Current"
    docs, _ = load(mode="changes", reader_kwargs={"include_removed": True}, project_id="prj_1")
    assert any(d.metadata["change"] == "removed" and d.text == "" for d in docs)


async def test_async_load():
    docs = await MeshArcReader(client=FakeMeshArc()).aload_data(url="https://e.test/")
    assert docs[0].metadata["url"] == "https://e.test/"


@pytest.mark.parametrize("mode, kwargs, message", [
    ("scrape", {}, "needs url"),
    ("changes", {}, "needs project_id"),
    ("crawl", {"url": ["https://a.test/", "https://b.test/"]}, "takes one url"),
])
def test_bad_arguments_are_refused_before_any_request(mode, kwargs, message):
    client = FakeMeshArc()
    with pytest.raises(ValueError, match=message):
        MeshArcReader(client=client, mode=mode).load_data(**kwargs)
    assert client.calls == []


def test_unknown_mode_is_refused():
    with pytest.raises(Exception):
        MeshArcReader(client=FakeMeshArc(), mode="nope")


def test_api_key_is_not_serialised(monkeypatch):
    reader = MeshArcReader(api_key="mesharc_secret_value", mode="crawl", params={"limit": 5})
    dumped = reader.to_dict()
    assert "mesharc_secret_value" not in str(dumped)
    assert dumped["mode"] == "crawl" and dumped["params"] == {"limit": 5}


def test_missing_api_key_is_a_clear_error(monkeypatch):
    monkeypatch.delenv("MESHARC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API key"):
        MeshArcReader()

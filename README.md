# llama-index-readers-mesharc

The LlamaIndex reader for [MeshArc](https://mesharc.dev), the web crawler that turns sites into clean markdown and records what changed between crawls.

`MeshArcReader` loads web pages as LlamaIndex `Document`s, in four modes: scrape, crawl, map and changes.

```bash
pip install llama-index-readers-mesharc
```

You need a MeshArc API key. Make one under **Settings → API keys** at [mesharc.dev](https://mesharc.dev); the free plan includes 1,000 credits with no card. Set it as `MESHARC_API_KEY`, or pass `api_key=`. Reading pages needs a key with **write** access.

## Usage

```python
from llama_index.core import VectorStoreIndex
from llama_index.readers.mesharc import MeshArcReader

# One page, or many read as one batch
docs = MeshArcReader().load_data(url="https://example.com/pricing")
docs = MeshArcReader().load_data(url=["https://example.com/", "https://example.com/about"])

# A whole site, or a section of it
reader = MeshArcReader(mode="crawl", params={"limit": 100, "includePaths": ["/guides/*"]})
docs = reader.load_data(url="https://docs.example.com")
index = VectorStoreIndex.from_documents(docs)

# The URLs a site declares in its sitemaps, without fetching them
urls = MeshArcReader(mode="map").load_data(url="https://docs.example.com")

# What changed on a watched site since the last crawl
changed = MeshArcReader(mode="changes").load_data(project_id="prj_...")
```

| Mode | `load_data` takes | Each Document |
|---|---|---|
| `scrape` | `url`: a URL or a list of URLs | the page's markdown |
| `crawl` | `url`: a site; `params` takes `limit`, `maxDepth`, `includePaths`, `excludePaths` and the rest of the [crawl options](https://mesharc.dev/docs/api) | one per page read |
| `map` | `url`: a site; `params` takes `search` and `limit` | one per URL in the sitemaps, with the URL as its text |
| `changes` | `project_id`, and optionally `run_id` and `against` | one per added or modified page, holding the page as it is now |

**Metadata** on every page: `source` and `url`, `title`, `page_status` (one word: `ok`, `missing`, `blocked`, `captcha`, …), `crawled_at` and `mode`.
- Scraped and changed pages also have `status`, the HTTP status. A crawl's pages don't, because the API leaves it out of crawl results.
- Scraped pages also have `verdict` and `credits`.
- A crawl adds `crawl_id`.
- Changes add `project_id`, `run_id`, `previous_run_id`, `changed_at`, `change` (`added`, `modified`, `removed` or `fields`), `words_before` and `words_after`.

Values are always strings, numbers or booleans.

Pages that came back with no content (blocked, or a 404) are left out. Pass `include_empty=True` to keep them; their `page_status` and `error_code` say why. In `changes` mode, removed pages are left out unless `include_removed=True`.

`changes` mode keeps an index current: load it after each run of a [MeshArc project](https://mesharc.dev/docs), and refresh only the pages that changed. Each Document's `id_` is `run_id:url`.

## Cost

Requests are billed in MeshArc credits, the same as any other API call:
- a plain page read costs 1 credit, and blocked pages and 404s cost nothing;
- a sitemap read costs 1 credit per sitemap file.

See [pricing](https://mesharc.dev/pricing).

## Links

- [MeshArc docs](https://mesharc.dev/docs) and [API reference](https://mesharc.dev/docs/api)
- [The Python SDK](https://github.com/mesharc-org/mesharc-python), which this package uses
- [langchain-mesharc](https://github.com/mesharc-org/langchain-mesharc), the same for LangChain
- [Questions](https://github.com/orgs/mesharc-org/discussions) · security reports to security@mesharc.dev

## License

MIT

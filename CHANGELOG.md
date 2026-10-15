# Changelog

## 0.1.0

The first release.

- `MeshArcReader` loads web pages through MeshArc as LlamaIndex Documents. It has four modes:
  - `scrape`: one URL, or many as a batch;
  - `crawl`: a site, with pages yielded as they land;
  - `map`: the sitemap's URLs;
  - `changes`: the pages a project's run added or modified.

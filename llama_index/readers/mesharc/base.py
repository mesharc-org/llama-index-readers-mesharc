"""MeshArcReader: pages from MeshArc as LlamaIndex Documents."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Literal, Optional, Sequence, Union

from llama_index.core.bridge.pydantic import Field, PrivateAttr
from llama_index.core.readers.base import BasePydanticReader
from llama_index.core.schema import Document

from . import _core


class MeshArcReader(BasePydanticReader):
    """Load web pages through MeshArc as Documents of clean markdown.

    Modes:
        * ``scrape``: one URL, or a list of URLs read as one batch.
        * ``crawl``: a one-shot crawl of a site, pages yielded as they land.
        * ``map``: the URLs the site declares in its sitemaps, one Document
          per URL whose text is the URL itself. Nothing is fetched.
        * ``changes``: what changed in a MeshArc project's latest run (or
          ``run_id``) against the run before it (or ``against``). Each
          added or modified page is a Document of the page as it is now.

    Metadata: ``source``/``url``, ``title``, ``page_status`` (one word:
    ok, missing, blocked, captcha, ...), ``crawled_at`` and ``mode``;
    scraped and changed pages add ``status`` (the HTTP status), scraped
    pages ``verdict`` and ``credits``, crawls ``crawl_id``, and changes
    ``project_id``, ``run_id``, ``previous_run_id``, ``changed_at``,
    ``change`` (added, modified, removed or fields) and
    ``words_before``/``words_after``.

    Example:
        .. code-block:: python

            from llama_index.readers.mesharc import MeshArcReader

            docs = MeshArcReader().load_data(url="https://example.com/pricing")
            docs = MeshArcReader(mode="crawl", params={"limit": 50}).load_data(url="https://docs.example.com")
            changed = MeshArcReader(mode="changes").load_data(project_id="prj_...")
    """

    is_remote: bool = True
    mode: Literal["scrape", "crawl", "map", "changes"] = Field(
        default="scrape", description="scrape, crawl, map or changes.")
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extra arguments for the MeshArc SDK call, e.g. {'limit': 50} for a crawl.")
    include_empty: bool = Field(
        default=False, description="Also return pages that came back without content (blocked, a 404).")
    include_removed: bool = Field(
        default=False, description="For changes: also return removed pages, with no text.")

    _client: Any = PrivateAttr()

    def __init__(self, api_key: Optional[str] = None, client: Any = None, **data: Any) -> None:
        """
        Args:
            api_key: A MeshArc API key; ``MESHARC_API_KEY`` is used when omitted.
            client: A ``mesharc.MeshArc`` client to use instead of making one.
            mode, params, include_empty, include_removed: as the fields describe.
        """
        super().__init__(**data)
        if self.mode not in _core.MODES:
            raise ValueError(f"mode must be one of {', '.join(_core.MODES)}, not {self.mode!r}")
        self._client = _core.make_client(api_key, client)

    @classmethod
    def class_name(cls) -> str:
        return "MeshArcReader"

    def lazy_load_data(  # type: ignore[override]
        self,
        url: Union[str, Sequence[str], None] = None,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        against: Optional[str] = None,
    ) -> Iterable[Document]:
        """
        Args:
            url: The URL (or, for ``scrape``, a list of URLs). Not used by ``changes``.
            project_id: The MeshArc project, for ``changes``.
            run_id: For ``changes``: the run to report on; the latest finished one by default.
            against: For ``changes``: compare with this run instead of the one before.
        """
        _core.check(self.mode, url, project_id)
        for record in _core.load(
            self._client,
            self.mode,
            url=url,
            project_id=project_id,
            run_id=run_id,
            against=against,
            params=self.params,
            include_empty=self.include_empty,
            include_removed=self.include_removed,
        ):
            yield Document(text=record["text"], metadata=record["metadata"], id_=record["id"])

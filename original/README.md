# Original Research Notebook

`original_research_notebook.ipynb` is an unmodified copy of the notebook submitted
as part of the dissertation (`101054037.ipynb`). It is kept here as an archival
record of the research as originally conducted.

It has **not** been edited in any way: no reformatting, no path changes, no
output stripping, no code changes. As a result it:

- references a local `BASE_DIR` path specific to the author's machine and will
  not run outside that environment,
- depends on raw Bloomberg settlement-price CSVs that are not included in this
  repository (see [`data/README.md`](../data/README.md)),
- reflects the coding style and organisation of a single-author dissertation
  notebook rather than the packaged implementation in [`src/tsmom`](../src/tsmom).

The packaged, tested, and documented implementation in [`src/tsmom`](../src/tsmom)
and the walkthrough in [`notebooks/research_analysis.ipynb`](../notebooks/research_analysis.ipynb)
are post-submission software-engineering work built on top of this original
research. They reproduce the same methodology but are not part of the
submitted dissertation.

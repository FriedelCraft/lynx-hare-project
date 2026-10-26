# Source and provenance notes

Sources were checked on 26 October 2026. The derivations and algebra checks in this package are written out independently; citations attribute the established model, response law and dataset context. No published numerical result is claimed to have been reproduced.

| Source | What was verified | How it is used |
|---|---|---|
| [Rosenzweig and MacArthur 1963](https://www.journals.uchicago.edu/doi/abs/10.1086/282272) | Publisher title, authors, year, journal, pages and abstract | Attribution for the predator-prey framework; no claim of having verified the paywalled full article line by line |
| [Holling 1959](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/S0008347X00072692) | Publisher article identity and metadata; a scanned primary article is also available from the University of Hawaii | Attribution for the functional response; the short search-and-handling derivation is presented explicitly in this package |
| [Carpenter's Stan case study](https://mc-stan.org/learn-stan/case-studies/lotka-volterra-predator-prey.html) | Author/date, years, units in thousands, pelt interpretation and the source chain described by the author | Public data reference and observation caveat; no assertion that the transcription is a raw archival census or that the case study used our train/test split |
| [tsibbledata pelt documentation](https://tsibbledata.tidyverts.org/reference/pelt.html) | Annual 1845–1935 pelt records and column definitions | Optional alternative recorded in bibliography only; not silently substituted for the agreed series |
| [Team repository at 7d17deee](https://github.com/FriedelCraft/lynx-hare-project/tree/7d17deee1cb685f016ff16cb6706e8db12ebe6b2) | Shared model, method, configuration and PINN unchanged from the initially reviewed a312f57; current PINN source inspected | Equations, synthetic constants, normalization and forecast origin |
| [Joel's theory section](https://github.com/FriedelCraft/lynx-hare-project/blob/7d17deee1cb685f016ff16cb6706e8db12ebe6b2/report/joel_stability_section.tex) and [handoff](https://github.com/FriedelCraft/lynx-hare-project/blob/7d17deee1cb685f016ff16cb6706e8db12ebe6b2/docs/joel_stability_handoff.md) | New dimensional analysis, dimensionless convention and integration notes | Main scaling now matches x=H/K, y=aP/(rK), s=rt. No blanket verification of all teammate theorems or simulations is claimed |
| [Python Fraction documentation](https://docs.python.org/3/library/fractions.html) | Exact rational arithmetic and integer-pair construction | Small notebook checks avoid binary floating-point rounding |
| [Tectonic command-line reference](https://tectonic-typesetting.github.io/book/latest/ref/v1cli.html) and [cache documentation](https://tectonic-typesetting.github.io/book/latest/getting-started/first-document.html) | Compilation flags and cache-location setting | PDF build tooling only; not a source for mathematical claims |
| Supplied `MAC_F314_Lynx_Hare_Project_Work_Distribution (2).docx`, section 01 Arnav | Arnav's ownership, required deliverables and team dependencies | Determines the scope of this package; supplied privately in the working conversation, not redistributed here |
| Yash's chat supplied as `Pasted text.txt` in this conversation | Background on his initial dummy-data work | Historical context only; repository files provide the implementation evidence |
| Professor's instructions supplied in chat | Mathematical explanation, own effort, credible validation and quantitative comparison requirements | Guides the reasoning and the limits on claims |

The Stan case study documents a transcription chain through Howard, Mahaffy's teaching material and a biology text. Cite the actual case study and CSV used by Advay, retaining that provenance, rather than describing the downloaded numbers as independently verified original Hudson's Bay Company archival measurements. Its original case study is a different modelling analysis; our 1900–1915/1916–1920 split is the team's protocol.

The longer tsibbledata series may differ in provenance, units or coverage. Do not combine it with the 1900–1920 transcription without explicitly checking compatibility and revising the protocol.

## Source URLs useful for team review

- Holling primary scan: https://hahana.soest.hawaii.edu/cmoreserver/summercourse/2010/documents/Holling_1959b.pdf
- Repository model: https://github.com/FriedelCraft/lynx-hare-project/blob/7d17deee1cb685f016ff16cb6706e8db12ebe6b2/src/lynx_hare/model.py
- Repository method: https://github.com/FriedelCraft/lynx-hare-project/blob/7d17deee1cb685f016ff16cb6706e8db12ebe6b2/docs/method.md
- Repository handoff: https://github.com/FriedelCraft/lynx-hare-project/blob/7d17deee1cb685f016ff16cb6706e8db12ebe6b2/docs/team_handoff.md

No historical CSV has been downloaded into this contribution. The synthetic parameter tuple is a worked algebra example copied from the team's configuration, not an observation dataset.

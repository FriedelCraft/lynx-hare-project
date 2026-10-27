# Historical lynx–hare pelt data (1900–1920)

`pelts_1900_1920.csv` is the dataset used for every historical fit and evaluation.
Its columns are `Year,Hare,Lynx`. Values are **thousands of pelts traded by the
Hudson's Bay Company per year**, copied unchanged from the source. There are 21
rows, no missing values and no zeros.

Full provenance, hashes and the transformation log are in
[`provenance.json`](provenance.json). Raw downloads are kept unmodified in `raw/`.

## Source

The data come from the CSV that accompanies the Stan case study suggested in the
work-distribution document (Carpenter, 2018). Carpenter takes the numbers from
Howard (2009), who traces them through Mahaffy's lecture notes to the textbook
*Life: The Science of Biology* (Purves et al.). The original records are Hudson's
Bay Company fur-trade returns.

This is a secondary compilation. No primary archival table is available to us, so
every result built on it should be read as conditional on this series.

## What the numbers mean

These are counts of pelts traded, not population censuses. Trapping effort, fur
prices, trapper behaviour and which posts reported all affect the counts. Hungry
lynx are also easier to trap when hares are scarce (Hewitt, 1921, discussed by
Carpenter). We treat Hare and Lynx as **abundance indices**, and make no claim
about absolute population sizes.

## Cross-check against a second compilation

The tsibbledata `pelt` series (Hudson Bay Company trading records, 1845–1935) is
saved in `raw/tsibbledata_lynxhare.csv` for comparison. Over 1900–1920 it differs
noticeably from the primary series:

| | Correlation with primary | Hare peaks | Lynx peaks |
|---|---|---|---|
| Primary (Stan) | — | 1903, 1913 | 1904, 1915 |
| tsibbledata | Hare 0.32, Lynx 0.81 | 1904, 1912 | 1905, 1914 |

Both show two cycles with lynx lagging hare by about a year, but individual
values disagree. We use the Stan series because the group protocol names it, and
we mention this disagreement as a data limitation. It is not used for fitting.

## Train/test split

| File | Years | Rows | Who may read it |
|---|---|---|---|
| `train_1900_1915.csv` | 1900–1915 | 16 | Any fitting, scaling or tuning code |
| `test_1916_1920.csv` | 1916–1920 | 5 | Only the final scoring step, after forecasts are frozen |

Both files are byte-for-byte copies of rows from `pelts_1900_1920.csv`, written by
`scripts/advay_make_split.py`. Their SHA-256 hashes and the rules are in `split.json`.
`tests/test_historical_data.py` checks that the split reassembles the master file, that
the hashes match, and that the shared loader (`read_training`) sees only 1900–1915.

Point fitting code at the **train file**, not the master file. `read_training` filters by
year, but giving it a file with no test rows means test values can't leak in by accident.

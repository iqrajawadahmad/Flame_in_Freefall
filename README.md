# Flame in Freefall - NASA Microgravity Combustion Intelligence Dashboard

## Run locally
```bash
py -3 -m pip install -r requirements.txt
py -3 -m streamlit run app.py
```
Run these commands in a terminal opened in the project folder, not in `app.py`.

## Data scope and provenance
The bundled `data/nasa_combustion.db` contains five investigation records (PSI-10, PSI-60, PSI-62, PSI-69, PSI-98),
7,506 experimental-run records, 36 parameter summaries, six extracted findings, and 107 linked resources.
All six extracted findings are paraphrases from the PSI-10 ACME final report, with report section and page references;
they are intentionally still `Unclassified`. The other investigations must not be presented as having those findings.
Dataset citations from the NASA PSI records: PSI-10 [10.60555/w4zy-bt45](https://doi.org/10.60555/w4zy-bt45);
PSI-60 [10.60555/mzjm-yv57](https://doi.org/10.60555/mzjm-yv57);
PSI-62 [10.60555/e9xp-ex83](https://doi.org/10.60555/e9xp-ex83);
PSI-69 [10.60555/mbq8-0451](https://doi.org/10.60555/mbq8-0451);
PSI-98 [10.60555/0t15-1z43](https://doi.org/10.60555/0t15-1z43).
The NASA PSI records specify CC0-1.0 for PSI-60, PSI-62, PSI-69, and PSI-98. The PSI-10 record does not state a
specific license, so confirm its reuse terms with PSI before redistributing its data or derived material publicly.

The database has been built from NASA PSI source files, and `data/nasa_combustion.db` takes priority over the
placeholder database. The source bundle currently included under `data/raw/Free_Fall_Data/` is incomplete for
rebuilding the full database: it contains PSI-10 files but does not include all five investigation metadata files,
the FLEX experimental table, or the SAFFIRE-I experimental table. Thus, the shipped database can be explored, but
the full database build is **not reproducible from the currently bundled raw files**. The build script checks for
required inputs before it runs and reports what is missing without replacing the existing database.

To rebuild once the complete PSI source data is available:
```bash
py -3 scripts/build_real_db.py             # add --raw <folder> to use another copy of the PSI data
```
Every cleaning decision is logged in `data/processed_data/data_quality_log.csv`. Run-level records preserve
original text, units, and quality flags. Missing numeric values are never filled with zero.

### Things to confirm before the demo (flagged in the data, NOT silently fixed)
1. FLEX column headers `O`, `N`, `CO` lost their subscript; read as O2, N2, CO2 (fractions sum to ~1).
2. FLEX `Burning rate; mm` has a length unit for a rate (probably mm^2/s). Stored as "unverified".
3. SAFFIRE sample thickness `0.37 cm` is implausible for a fabric (maybe mm). Converted as labelled, flagged.
4. All findings are `Unclassified` (Prevention/Detection/Suppression is a Phase 6 judgement, not made here).
5. PSI-60 and PSI-62 are ground/modelling studies: no experimental table, so no parameters or findings.

Optional evidence files for more analysis, placed in `data/processed_data/`:
- `investigation_scores.csv`: `investigation_id` plus the criteria listed on the Ranking page; scores must be
  evidence-supported 0-5 values and blank means unknown. No scores are supplied by default.
- `engineering_implications.csv`, `research_gaps.csv`: displayed as supplied; the app does not infer their contents.

## Structure
- `app.py` - branded entry point and explicit eight-page navigation.
- `pages/00_Dashboard.py` - mission dashboard. Other files in `pages/` provide investigation explorer,
  parameter analyzer, comparison, calculators, ranking, grounded research summaries, and fire-safety review.
- `scripts/build_real_db.py` - raw PSI files to database. `modules/database.py` - shared database queries.
- `modules/physics_models.py` - shared calculator formulas. `modules/ranking_engine.py` - transparent ranking method.
- `modules/ai_insights.py` - deterministic database summaries; it does not call an LLM.
- `tests/` - run `py -3 -m pytest -q` for physics, data, and page smoke tests.

## Rules
1. Missing data = "Not available", never 0.
2. Never mix parameters with different units in one chart or statistic.
3. No API keys in GitHub (use Streamlit secrets / env vars). The app must work without AI.
4. Show source references wherever findings appear.

## Deploy (Streamlit Community Cloud)
Push the project to a GitHub repository, then create an app at Streamlit Community Cloud using the repository and
`app.py` as the entry point. Include `requirements.txt` and `data/nasa_combustion.db`; no API key is required.
Run the test suite locally before publishing. Do not upload source data unless you have permission to share it.

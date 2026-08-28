# Setup

## Prereqs

- Python 3.10+
- Optional Firebase project for hosted writes
- Optional Kaggle credentials for auxiliary non-World-Cup data refreshes

## Raw Evidence

Approved raw data is kept under:

```text
data/raw/
```

`jfjelstul/worldcup` is the only mirrored external repository. The public
international results CSVs, StatsBomb competition index, openfootball 2026
schedule JSON, and curated 2026 venue CSV are the other approved local raw
sources. EA Sports FC, SOFIFA, FUTBIN, FUTWIZ, and synthetic/demo data are
rejected.

## ML Pipeline

```bash
pip install -r ml/requirements.txt
python ml/scripts/run_pipeline.py
```

Artifacts land in `ml/artifacts/`, including model files, metrics, player
tables, feature tables, plots, and `simulation.parquet`.

## Streamlit App

```bash
pip install -r requirements_app.txt
python scripts/bootstrap.py
python ml/scripts/fetch_2026_squads.py
streamlit run app.py
```

Pages: Player Analysis, Team Analysis, Player Head to Head, Team Head to Head, Match Analysis + Predictor.

## Deployment

- Frontend: Streamlit Cloud pointing at `app.py` with `requirements_app.txt`.
- Backend refresh: Render cron from `render.yaml`, running the ML pipeline and
  Firebase push weekly.

## Verification

```bash
PYTHONPATH=ml/src pytest ml/tests
python scripts/validate_real_data_sources.py
python scripts/bootstrap.py
```

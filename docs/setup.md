# Setup

## Prereqs

- Python 3.10+
- Optional Firebase project for hosted writes
- Optional Kaggle credentials for auxiliary non-World-Cup data refreshes

## Raw Evidence

The requested reference repositories are mirrored under:

```text
data/raw/external_repos/
```

`jfjelstul/worldcup` is the primary historical World Cup source. The Kaggle/public
international results file is still used for auxiliary non-World-Cup fixtures
when `data/raw/results.csv` is available.

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
streamlit run app.py
```

Pages: Dashboard, Predict, Teams, Players, Model, Bracket, Simulator.

## Deployment

- Frontend: Streamlit Cloud pointing at `app.py` with `requirements_app.txt`.
- Backend refresh: Render cron from `render.yaml`, running the ML pipeline and
  Firebase push weekly.

## Verification

```bash
PYTHONPATH=ml/src pytest ml/tests
python scripts/bootstrap.py
```

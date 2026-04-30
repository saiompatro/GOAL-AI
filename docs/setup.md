# Setup

## Prereqs
- Python 3.10+
- Kaggle account + API token (`~/.kaggle/kaggle.json` or env vars)
- Supabase project (free tier is fine)

## 1. Environment
Copy `.env.example` → `.env` at the repo root and fill in Supabase + Kaggle keys.

## 2. Supabase schema
In the Supabase SQL editor, run `supabase/schema.sql` then `supabase/seed.sql`.

## 3. ML pipeline
```bash
cd ml
python -m venv .venv && source .venv/Scripts/activate   # Windows bash
pip install -r requirements.txt
python scripts/run_pipeline.py
```
Artifacts land in `ml/artifacts/` (models, metrics.json, confusion matrix, SHAP plot, model_card.md).

## 4. Push to Supabase
```bash
python scripts/push_to_supabase.py
```
Writes `teams`, `players`, `matches`, `predictions`, `model_runs`, `insights`.

## 5. Streamlit app
From the repo root:
```bash
pip install -r requirements_app.txt
streamlit run app.py
```
Opens at http://localhost:8501. Pages: Dashboard, Predict, Teams, Players, Model.

## 6. On-demand prediction
```bash
python -m goal_ai.predict --home Brazil --away Argentina
```
Writes a row into `predictions` with SHAP drivers; the Streamlit Predict page reads it.

## 7. Deployment
- **Frontend**: Streamlit Cloud — point at `app.py`, set `requirements_app.txt`, add Supabase env vars as secrets.
- **Backend (pipeline + HF jobs)**: Render — deploy `ml/` as a cron job or background worker that runs `scripts/run_pipeline.py` + `scripts/push_to_supabase.py` on a schedule.

## Troubleshooting
- **Kaggle 403**: ensure `KAGGLE_USERNAME` / `KAGGLE_KEY` env vars are set or `~/.kaggle/kaggle.json` exists with 600 perms.
- **Supabase RLS**: `schema.sql` enables RLS with a permissive read policy for anon; service-role writes bypass RLS.
- **Torch install slow/fails**: use CPU wheel `pip install torch --index-url https://download.pytorch.org/whl/cpu`.

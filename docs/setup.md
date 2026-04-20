# Setup

## Prereqs
- Python 3.10+
- Node 18+
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

## 5. Frontend
```bash
cd frontend
npm install
npm run dev
```
Opens at http://localhost:3000.

## 6. On-demand prediction
```bash
python -m goal_ai.predict --home Brazil --away Argentina
```
Writes a row into `predictions` with SHAP drivers; the frontend Predict page reads it.

## Troubleshooting
- **Kaggle 403**: ensure `KAGGLE_USERNAME` / `KAGGLE_KEY` env vars are set or `~/.kaggle/kaggle.json` exists with 600 perms.
- **Supabase RLS**: `schema.sql` enables RLS with a permissive read policy for anon; service-role writes bypass RLS.
- **Torch install slow/fails**: use CPU wheel `pip install torch --index-url https://download.pytorch.org/whl/cpu`.

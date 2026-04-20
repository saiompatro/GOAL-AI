# GOAL AI

ML-first FIFA World Cup match prediction, team insights, and player analysis.

- **Python + XGBoost/LightGBM/PyTorch ensemble** for match outcome prediction
- **SHAP** for per-prediction explanations
- **Hugging Face** summarization for natural-language player/team insights
- **Supabase** for storage
- **Next.js + TypeScript** frontend

## Quick start

```bash
# 1. ML
cd ml
pip install -r requirements.txt
cp ../.env.example ../.env   # fill in Kaggle + Supabase keys
python scripts/run_pipeline.py          # ingest → features → train → evaluate → explain
python scripts/push_to_supabase.py      # push artifacts + sample predictions

# 2. Frontend
cd ../frontend
npm install
npm run dev
```

See `docs/setup.md` for detailed instructions and `docs/research.md` for dataset/model choices.

## Structure
```
ml/          Python pipeline (ingest, features, train, evaluate, explain, HF insights)
supabase/    schema + seed SQL
frontend/    Next.js App Router app (dashboard, predict, teams, players, model)
docs/        research notes, model card, setup
data/        raw + processed (gitignored)
```

## Model choice (summary)
XGBoost primary, compared against LightGBM, a PyTorch FFN, a stacked ensemble, and an LR baseline. Selection by validation log-loss + Brier. Full justification in `docs/model_card.md` (written by the pipeline).

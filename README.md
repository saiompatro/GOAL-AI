# GOAL AI

ML-first FIFA World Cup match prediction, team insights, and player analysis.

- **Python + XGBoost / LightGBM / PyTorch ensemble** for match outcome prediction
- **SHAP** for per-prediction explanations
- **Hugging Face** summarization for natural-language player/team insights
- **Supabase** for storage
- **Streamlit** frontend (Dashboard, Predict, Teams, Players, Model)

Backend deployment target: **Render**. Frontend: **Streamlit Cloud** (or Render web service running `streamlit run app.py`).

## Quick start

```bash
# 1. ML pipeline
cd ml
pip install -r requirements.txt
cp ../.env.example ../.env   # fill in Kaggle + Supabase keys
python scripts/run_pipeline.py          # ingest → features → train → evaluate → explain
python scripts/push_to_supabase.py      # push artifacts + sample predictions

# 2. Streamlit app (from repo root)
cd ..
pip install -r requirements_app.txt
streamlit run app.py
```

See `docs/setup.md` for detailed instructions and `docs/research.md` for dataset/model choices.

## Structure
```
app.py        Streamlit entry point
pages/        Streamlit pages (Dashboard, Predict, Teams, Players, Model)
ml/           Python pipeline (ingest, features, train, evaluate, explain, HF insights)
supabase/     schema + seed SQL
docs/         research notes, model card, setup, graphify
data/         raw + processed (gitignored)
```

## Model choice (summary)
XGBoost primary, compared against LightGBM, a PyTorch FFN, a stacked ensemble, and an LR baseline. Selection by validation log-loss + Brier. Full justification in `docs/model_card.md` (written by the pipeline).

# Contributing

Thanks for helping improve GOAL AI.

## Local setup

```bash
pip install -r requirements_app.txt
pip install -r ml/requirements.txt
python ml/scripts/run_pipeline.py
streamlit run app.py
```

## Data provenance

External reference repositories are mirrored under `data/raw/external_repos/`
for local evidence. The primary World Cup historical source is
`jfjelstul/worldcup`; auxiliary international results and current FIFA-style
ratings remain optional inputs for broader match context.

## Checks

Before opening a pull request, run:

```bash
python -m pytest ml/tests
python scripts/bootstrap.py
```

Keep model/data trade-offs explicit in docs and model cards. Prediction code
should avoid target leakage by using only pre-match information.

# Graphify

Generated for `.` on 2026-04-20. Updated 2026-05-01 (frontend consolidated to Streamlit; Next.js removed).

## System Graph

```mermaid
flowchart LR
    kaggle[Kaggle match + player datasets]
    env[Root .env credentials]

    subgraph ml[ml]
        ingest[goal_ai.ingest.load_raw]
        clean[goal_ai.clean]
        features[goal_ai.features.build_features]
        train[goal_ai.train.train_all]
        evaluate[goal_ai.evaluate]
        explain[goal_ai.explain]
        hf[hf_insights]
        pipeline[scripts/run_pipeline.py]
        push[scripts/push_to_firebase.py]
        artifacts[ml/artifacts]
    end

    subgraph db[Firebase]
        teams[(teams)]
        players[(players)]
        matches[(matches)]
        predictions[(predictions)]
        model_runs[(model_runs)]
        insights[(insights)]
    end

    subgraph web[Streamlit app]
        appentry[app.py]
        dashboard[pages/1_Dashboard.py]
        predict[pages/2_Predict.py]
        teamsPage[pages/3_Teams.py]
        playersPage[pages/4_Players.py]
        modelPage[pages/5_Model.py]
    end

    kaggle --> ingest
    env --> pipeline
    env --> push
    pipeline --> ingest --> clean --> features --> train --> evaluate --> explain --> artifacts
    artifacts --> push
    hf --> push

    push --> teams
    push --> players
    push --> matches
    push --> predictions
    push --> model_runs
    push --> insights

    teams --> appentry
    players --> appentry
    matches --> appentry
    predictions --> appentry
    model_runs --> appentry
    insights --> appentry

    appentry --> dashboard
    appentry --> predict
    appentry --> teamsPage
    appentry --> playersPage
    appentry --> modelPage
```

## Directory Map

```text
.
|-- README.md
|-- app.py
|-- requirements_app.txt
|-- pages/
|   |-- 1_Dashboard.py
|   |-- 2_Predict.py
|   |-- 3_Teams.py
|   |-- 4_Players.py
|   `-- 5_Model.py
|-- docs/
|   |-- setup.md
|   |-- research.md
|   `-- graphify.md
|-- firebase/
|   |-- schema.sql
|   `-- seed.sql
`-- ml/
    |-- config.yaml
    |-- scripts/
    |   |-- run_pipeline.py
    |   `-- push_to_firebase.py
    |-- src/goal_ai/
    |   |-- ingest.py
    |   |-- clean.py
    |   |-- features.py
    |   |-- train.py
    |   |-- evaluate.py
    |   |-- explain.py
    |   |-- predict.py
    |   |-- hf_insights.py
    |   `-- firebase_io.py
    `-- artifacts/
```

## Notes

- Training flow is `ingest -> clean -> features -> train -> evaluate -> explain`.
- `push_to_firebase.py` publishes model outputs, seeded teams/players, predictions, and Hugging Face summaries.
- The Streamlit app (`app.py` + `pages/`) reads from Firebase directly via `firebase-admin`.
- Deployment: Streamlit Cloud (frontend) + Render (backend pipeline / cron).

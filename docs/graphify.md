# Graphify

Generated for `.` on 2026-04-20.

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
        push[scripts/push_to_supabase.py]
        artifacts[ml/artifacts]
    end

    subgraph db[Supabase]
        teams[(teams)]
        players[(players)]
        matches[(matches)]
        predictions[(predictions)]
        model_runs[(model_runs)]
        insights[(insights)]
    end

    subgraph web[frontend]
        data[lib/data.ts]
        dashboard[app/page.tsx]
        predict[app/predict/page.tsx]
        teamsPage[app/teams/page.tsx]
        playersPage[app/players/page.tsx]
        modelPage[app/model/page.tsx]
        demo[lib/demo-data.ts]
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

    teams --> data
    players --> data
    matches --> data
    predictions --> data
    model_runs --> data
    insights --> data
    demo --> data

    data --> dashboard
    data --> predict
    data --> teamsPage
    data --> playersPage
    data --> modelPage
```

## Directory Map

```text
.
|-- README.md
|-- docs/
|   |-- setup.md
|   |-- research.md
|   `-- graphify.md
|-- supabase/
|   |-- schema.sql
|   `-- seed.sql
|-- ml/
|   |-- config.yaml
|   |-- scripts/
|   |   |-- run_pipeline.py
|   |   `-- push_to_supabase.py
|   |-- src/goal_ai/
|   |   |-- ingest.py
|   |   |-- clean.py
|   |   |-- features.py
|   |   |-- train.py
|   |   |-- evaluate.py
|   |   |-- explain.py
|   |   |-- predict.py
|   |   |-- hf_insights.py
|   |   `-- supabase_io.py
|   `-- artifacts/
`-- frontend/
    |-- app/
    |   |-- page.tsx
    |   |-- predict/page.tsx
    |   |-- teams/page.tsx
    |   |-- players/page.tsx
    |   `-- model/page.tsx
    |-- components/
    |-- lib/
    |   |-- data.ts
    |   |-- supabase.ts
    |   `-- demo-data.ts
    `-- types/
```

## Notes

- Training flow is `ingest -> clean -> features -> train -> evaluate -> explain`.
- `push_to_supabase.py` publishes model outputs, seeded teams/players, predictions, and Hugging Face summaries.
- `frontend/lib/data.ts` is the main read layer; it uses Supabase when configured and falls back to demo data when not.

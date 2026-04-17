-- GOAL AI schema
-- Run in Supabase SQL editor.

create extension if not exists "pgcrypto";

create table if not exists teams (
    id uuid primary key default gen_random_uuid(),
    name text unique not null,
    code text,
    confederation text,
    created_at timestamptz default now()
);

create table if not exists players (
    id uuid primary key default gen_random_uuid(),
    team_id uuid references teams(id) on delete cascade,
    name text not null,
    position text,
    overall int,
    attrs jsonb default '{}'::jsonb,
    created_at timestamptz default now()
);
create index if not exists players_team_idx on players(team_id);

create table if not exists matches (
    id uuid primary key default gen_random_uuid(),
    match_date date not null,
    home_id uuid references teams(id),
    away_id uuid references teams(id),
    stage text,
    venue text,
    neutral bool default false,
    home_score int,
    away_score int,
    result text check (result in ('H','D','A') or result is null),
    created_at timestamptz default now()
);
create index if not exists matches_date_idx on matches(match_date);

create table if not exists model_runs (
    id uuid primary key default gen_random_uuid(),
    version text not null,
    algo text not null,
    metrics jsonb not null,
    notes text,
    created_at timestamptz default now()
);

create table if not exists predictions (
    id uuid primary key default gen_random_uuid(),
    match_id uuid references matches(id) on delete cascade,
    model_version text not null,
    p_home numeric not null,
    p_draw numeric not null,
    p_away numeric not null,
    confidence numeric,
    shap jsonb default '[]'::jsonb,
    created_at timestamptz default now()
);
create index if not exists predictions_match_idx on predictions(match_id);

create table if not exists insights (
    id uuid primary key default gen_random_uuid(),
    entity_type text check (entity_type in ('team','player','match')) not null,
    entity_id uuid not null,
    summary_text text not null,
    model text,
    created_at timestamptz default now()
);
create index if not exists insights_entity_idx on insights(entity_type, entity_id);

-- RLS: public read, service-role write
alter table teams enable row level security;
alter table players enable row level security;
alter table matches enable row level security;
alter table model_runs enable row level security;
alter table predictions enable row level security;
alter table insights enable row level security;

do $$
begin
  create policy "public read teams" on teams for select using (true);
  create policy "public read players" on players for select using (true);
  create policy "public read matches" on matches for select using (true);
  create policy "public read model_runs" on model_runs for select using (true);
  create policy "public read predictions" on predictions for select using (true);
  create policy "public read insights" on insights for select using (true);
exception when duplicate_object then null;
end $$;

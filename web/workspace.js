"use strict";
const $ = (id) => document.getElementById(id);
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const num = (n) => Number(n).toLocaleString("en-GB");
const pct = (n) => `${(Number(n) * 100).toFixed(1)}%`;
const initials = (name) =>
  name
    .split(/\s+/)
    .filter((n) => !["FC", "CF", "AC"].includes(n))
    .slice(0, 3)
    .map((n) => n[0])
    .join("")
    .toUpperCase();
const pretty = (value) =>
  value.replaceAll("_", " ").replace(/\b\w/g, (s) => s.toUpperCase());
const money = (n) => `€${Number(n).toFixed(1)}<span class="unit">m</span>`;
const styleKeys = [
  "goals",
  "assists",
  "shots",
  "key_passes",
  "dribbles",
  "tackles",
  "interceptions",
];
let competitions = [],
  context = null,
  routeVersion = 0,
  taskVersion = 0;
let activeController = null;
const pages = {
  overview: ["◫", "Overview"],
  matches: ["◈", "Match Predictor"],
  transfers: ["↗", "Transfer Values"],
  scouting: ["⌕", "Player Scouting"],
};

async function api(url, options = {}) {
  const r = await fetch(url, options);
  const data = await r.json();
  if (!r.ok || data.error)
    throw new Error(
      data.error || `Unable to load data (${r.status}). Please try again.`,
    );
  return data;
}
const link = (slug, page = "overview") => `/competitions/${slug}/${page}`;
const emblem = (c) =>
  `<span class="league-emblem" style="--league:${esc(c.color)}">${esc(c.short)}</span>`;
const tag = (text, cls = "") => `<span class="tag ${cls}">${esc(text)}</span>`;
const form = (values) =>
  `<span class="form" aria-label="Recent results: ${values.join(", ")}">${values.map((v) => `<i class="${v}">${v}</i>`).join("")}</span>`;
const stat = (label, value, caption) =>
  `<div class="stat"><div class="label">${esc(label)}</div><div class="number">${esc(value)}</div><div class="caption">${esc(caption)}</div></div>`;
const loading = (text) =>
  `<div class="loading" role="status">${esc(text)}</div>`;
const empty = (title, text, icon = "◈") =>
  `<div class="empty-state"><span class="tool-icon">${icon}</span><h2>${esc(title)}</h2><p>${esc(text)}</p></div>`;
const options = (items, selected) =>
  items
    .map(
      (n) =>
        `<option value="${esc(n)}"${n === selected ? " selected" : ""}>${esc(n)}</option>`,
    )
    .join("");
const sourceNote = (scout = false) => {
  const source = scout ? context.scout_source : context.player_source;
  return `<div class="data-note neutral"><span>◈</span><div><strong>Observed historical player data</strong> · ${esc(source.note)}<br><span class="notice-count"><a href="${esc(source.source_url || '#')}" target="_blank" rel="noopener noreferrer">${esc(source.source)}</a> · ${esc((source.seasons || []).join(', '))}</span></div></div>`;
};
const plot = (kind, label) =>
  `<details class="chart-details"><summary>${esc(label)} ↗</summary><img class="chart-image" loading="lazy" src="/api/workspaces/${context.competition.slug}/plot/${kind}.png" alt="${esc(label)}"><a class="text-button" href="/api/workspaces/${context.competition.slug}/plot/${kind}.png" download>Download chart ↓</a></details>`;

function renderNav(slug) {
  $("competition-nav").innerHTML = competitions
    .map(
      (c) =>
        `<a href="${link(c.slug)}" class="${c.slug === slug ? "active" : ""}" ${c.slug === slug ? 'aria-current="page"' : ""}><span class="nav-monogram" style="--league:${c.color}">${c.short}</span>${c.name}</a>`,
    )
    .join("");
  document.querySelector("[data-home]").classList.toggle("active", !slug);
}

function pitch() {
  const points = [
    [10, 50],
    [28, 22],
    [28, 72],
    [40, 46],
    [56, 17],
    [55, 74],
    [70, 42],
    [84, 20],
    [85, 74],
    [72, 67],
    [40, 81],
  ];
  return `<div class="pitch-scene" aria-hidden="true"><div class="pitch"><div class="goal-box left"></div><div class="goal-box right"></div>${points.map(([x, y], i) => `<span class="pitch-player ${i > 5 ? "opponent" : ""}" style="left:${x}%;top:${y}%"></span>`).join("")}</div><div class="pitch-note">◈ &nbsp; The game, seen differently.</div></div>`;
}

function hub() {
  document.title = "GOAL AI · Competition hub";
  $("breadcrumb").innerHTML = "Workspace <span>/</span> Competition hub";
  $("content").innerHTML =
    `<div class="page-heading"><div><div class="eyebrow">THE ANALYST’S WORKSPACE</div><h1>Welcome to the game.</h1><p>Your competitions. Your questions. A sharper perspective.</p></div><span class="pill"><span class="status-dot"></span>6 competition workspaces</span></div>
  <section class="hero"><div><div class="eyebrow">FOOTBALL INTELLIGENCE, WITH PURPOSE</div><h1>Look beyond<br>the <span class="accent">scoreline.</span></h1><p>Find the next opportunity. Understand a player’s value. Explore what could happen next — with the numbers to back it up.</p><a class="hero-tag" href="${link("premier-league")}">Explore Premier League <span>↗</span></a></div>${pitch()}</section>
  <div class="section-heading"><div><h2>Pick your competition</h2><p>One dedicated workspace. Three ways to explore the game.</p></div><span class="eyebrow">01 — 06</span></div>
  <div class="competition-grid">${competitions.map((c) => `<a class="competition-card" style="--league:${c.color}" href="${link(c.slug)}"><div class="card-top">${emblem(c)}${tag(c.region)}</div><h3>${c.name}</h3><p>${c.slug === "champions-league" ? "Europe’s biggest stage. A wider perspective." : { "premier-league": "Every match. Every margin. Every opportunity.", "la-liga": "Technical brilliance, measured differently.", "serie-a": "The details behind the tactical battle.", bundesliga: "High intensity. Deeper understanding.", "ligue-1": "Discover the talent behind the headlines." }[c.slug]}</p><div class="card-foot"><span>Predictions · Values · Scouting</span><span class="go">↗</span></div></a>`).join("")}</div>
  <div class="hub-bottom"><span class="tool-icon">◎</span><div><h3>The world’s game, on one stage.</h3><p>Explore the existing World Cup match, team, and player analysis tools.</p></div><a class="button secondary small" href="/world-cup">World Cup 2026 ↗</a></div>`;
}

function leagueShell(page) {
  const c = context.competition,
    s = context.summary;
  document.documentElement.style.setProperty("--accent", c.color);
  document.title = `${c.name} · ${pages[page][1]} | GOAL AI`;
  $("breadcrumb").innerHTML =
    `<a href="/">Competitions</a><span>/</span><a href="${link(c.slug)}">${c.name}</a><span>/</span>${pages[page][1]}`;
  return `<div class="page-heading"><div class="league-heading">${emblem(c)}<div><div class="eyebrow">${c.region.toUpperCase()} / COMPETITION WORKSPACE</div><h1>${c.name}</h1><p>${page === "overview" ? "The full picture. One competition at a time." : { matches: "Turn recent performances into match probabilities.", transfers: "Explore what a player’s numbers could be worth.", scouting: "Find the player behind the playing style." }[page]}</p></div></div><span class="pill">Match data through ${esc(s.through)}</span></div>
  <nav class="tabs" aria-label="${c.name} tools">${Object.entries(pages)
    .map(
      ([key, [icon, name]]) =>
        `<a href="${link(c.slug, key)}" class="${page === key ? "active" : ""}" ${page === key ? 'aria-current="page"' : ""}><span>${icon}</span>${name}</a>`,
    )
    .join("")}</nav>`;
}

function preferredTeams() {
  const ts = context.teams;
  const choose = (fragment) =>
    ts.find((t) => t.toLowerCase().includes(fragment));
  const home =
    choose("arsenal") || choose("barcelona") || choose("madrid") || ts[0];
  const away =
    choose("chelsea") ||
    (choose("madrid") !== home && choose("madrid")) ||
    ts.find((t) => t !== home);
  return [home, away];
}

function overviewPage() {
  const c = context.competition,
    s = context.summary;
  const [home, away] = preferredTeams();
  return `${leagueShell("overview")}<div class="stats-grid">${stat("Historical matches", num(s.matches), `${s.first_season} — ${s.latest_season}`)}${stat("Teams in latest season", context.teams.length, `From ${s.latest_season} results`)}${stat("Player profiles", s.players, `Observed · ${s.player_latest_season}`)}${stat("Analysis tools", "03", "Predict · Value · Discover")}</div>
  <div class="two-col"><section class="panel match-teaser"><div class="panel-head"><h2>Build your next match-up</h2>${tag("MATCH LAB")}</div><p class="desc">Explore win, draw, and loss probabilities from each team’s recent form.</p><div class="team-pair"><div><span class="team-badge">${esc(initials(home))}</span><strong>${esc(home)}</strong></div><span class="vs">VS</span><div><span class="team-badge">${esc(initials(away))}</span><strong>${esc(away)}</strong></div></div><div class="teaser-foot"><p>Hypothetical fixture · 90-minute result</p><a class="button small" href="${link(c.slug, "matches")}">Open match predictor ↗</a></div></section>
  <section class="panel"><div class="panel-head"><h2>Recent in the dataset</h2>${tag(s.latest_season)}</div>${context.recent
    .slice(0, 4)
    .map(
      (m) =>
        `<div class="result-row"><span>${esc(m.home_team)}<small class="result-date">${m.date}</small></span><span class="score">${m.home_score}–${m.away_score}</span><span>${esc(m.away_team)}</span></div>`,
    )
    .join(
      "",
    )}<p class="caption-note">Historical results · ${esc(context.match_source.source)}</p></section></div>
  <div class="section-heading"><div><h2>Your analysis toolkit</h2><p>Go from a question to a different view of the game.</p></div></div>
  <div class="tool-grid">${[
    [
      "matches",
      "◈",
      "Match Predictor",
      "Read the form. Explore the probabilities. See how the model performed on unseen matches.",
      "Random forest",
    ],
    [
      "transfers",
      "↗",
      "Transfer Values",
      "Compare a player’s estimated value with their reference value, or build your own scenario.",
      "Linear regression",
    ],
    [
      "scouting",
      "⌕",
      "Player Scouting",
      "Search a player. Discover similar profiles and groups with a shared playing style.",
      "Similarity + K-means",
    ],
  ]
    .map(
      ([page, icon, title, desc, method]) =>
        `<a class="tool-card" href="${link(c.slug, page)}"><span class="tool-icon">${icon}</span><h3>${title}</h3><p>${desc}</p><div class="card-foot"><span>${method}</span><span class="accent">↗</span></div></a>`,
    )
    .join("")}</div>
  <div class="section-heading"><div><h2>Teams in form</h2><p>Last six recorded matches · sorted by points, then goal difference. Not official standings.</p></div><span class="notice-count">As of ${s.through}</span></div><section class="panel"><div class="table-wrap"><table><thead><tr><th>#</th><th>Club</th><th>Played</th><th>Goals for</th><th>Goals against</th><th>Form · oldest → latest</th><th>Points</th></tr></thead><tbody>${context.form
    .slice(0, 6)
    .map(
      (t, i) =>
        `<tr><td>${i + 1}</td><td class="team-cell">${esc(t.team)}</td><td>${t.played}</td><td>${t.scored}</td><td>${t.conceded}</td><td>${form(t.form)}</td><td class="accent">${t.points}</td></tr>`,
    )
    .join("")}</tbody></table></div></section>
  <div class="spaced">${sourceNote()}</div>`;
}

function matchPage() {
  const [home, away] = preferredTeams();
  return `${leagueShell("matches")}<div class="workspace-layout"><section class="panel control-panel"><div class="panel-head"><h2>The match-up</h2>${tag("90 MIN")}</div><form id="match-form"><div class="field"><label for="home-team">Home team</label><select id="home-team">${options(context.teams, home)}</select></div><div class="field"><label for="away-team">Away team</label><select id="away-team">${options(context.teams, away)}</select></div>${context.competition.slug === "champions-league" ? '<label class="check-field"><input id="neutral" type="checkbox">Neutral venue / final</label>' : ""}<button class="button full" type="submit">Predict match <span>↗</span></button></form><div class="divider"></div><div class="eyebrow">BEHIND THE PREDICTION</div><p class="desc">Random forest trained on this competition’s history. Inputs use the six previous matches: goals scored, goals conceded, form, and observed shooting statistics where available.</p><p class="caption-note">${esc(context.match_source.source)}<br>Through ${context.summary.through}<br>Unseen ${context.summary.latest_season} matches are used for evaluation.</p><p class="caption-note">This is a hypothetical fixture using the latest recorded form. A knockout prediction covers 90 minutes, not qualification.</p></section><div id="tool-result" class="result-stack" aria-live="polite">${empty("Every match starts with a question.", "Choose two teams to see their probabilities, recent form, and the model’s track record.")}</div></div>
  <section class="panel spaced"><div class="panel-head"><h2>Upcoming fixtures</h2>${tag(context.fixtures ? "CACHED FEED" : "NOT CONNECTED")}</div>${
    context.fixtures?.matches?.length
      ? `<p class="desc">football-data.org · refreshed ${esc(context.fixtures.retrieved_at.slice(0, 10))}. Select matching teams above to analyse a fixture.</p><div class="fixture-list">${context.fixtures.matches
          .slice(0, 6)
          .map(
            (m) =>
              `<div class="result-row"><span>${esc(m.homeTeam.name)}</span><span>${esc(m.awayTeam.name)}</span><span>${esc(m.utcDate.slice(0, 10))}</span></div>`,
          )
          .join("")}</div>`
      : '<p class="desc">No upcoming fixture feed is loaded. You can still explore any match-up above. Connect football-data.org and refresh fixtures using the setup instructions in README.md.</p>'
  }</section>`;
}

async function runTask(label, work, render) {
  const currentRoute = routeVersion,
    task = ++taskVersion;
  activeController?.abort();
  activeController = new AbortController();
  const target = $("tool-result");
  target.innerHTML = loading(label);
  const buttons = document.querySelectorAll(".control-panel button");
  buttons.forEach((b) => (b.disabled = true));
  try {
    const data = await work(activeController.signal);
    if (currentRoute !== routeVersion || task !== taskVersion) return;
    target.innerHTML = render(data);
  } catch (e) {
    if (
      currentRoute !== routeVersion ||
      task !== taskVersion ||
      e.name === "AbortError"
    )
      return;
    target.innerHTML = `<div class="error" role="alert">${esc(e.message)} Change the inputs and try again.</div>`;
  } finally {
    if (currentRoute === routeVersion && task === taskVersion)
      buttons.forEach((b) => (b.disabled = false));
  }
}

function metricsHtml(items) {
  return `<div class="metrics">${items.map(([value, label]) => `<div><div class="number">${esc(value)}</div><small>${esc(label)}</small></div>`).join("")}</div>`;
}
function matchResult(d) {
  const labels = { home_win: d.home, draw: "Draw", away_win: d.away };
  const m = d.metrics;
  return `<section class="panel"><div class="prediction-head"><span>HYPOTHETICAL FIXTURE / ${d.neutral ? "NEUTRAL VENUE" : "HOME ADVANTAGE"}</span>${tag("MODEL ESTIMATE")}</div><div class="team-pair"><div><span class="team-badge">${esc(initials(d.home))}</span><strong>${esc(d.home)}</strong><div class="spaced">${form(d.form.home)}</div></div><span class="vs">VS</span><div><span class="team-badge">${esc(initials(d.away))}</span><strong>${esc(d.away)}</strong><div class="spaced">${form(d.form.away)}</div></div></div><div class="probability-bar" aria-hidden="true">${[
    "home_win",
    "draw",
    "away_win",
  ]
    .map((k) => d.prob[k])
    .map((p) => `<span style="width:${p * 100}%"></span>`)
    .join(
      "",
    )}</div><div class="prob-labels">${["home_win", "draw", "away_win"].map((k, i) => `<div><div class="number ${d.pick === k ? "accent" : ""}">${pct(d.prob[k])}</div><span>${["Home win", "Draw", "Away win"][i]}</span></div>`).join("")}</div><div class="model-pick"><span>Most likely outcome</span><strong>${esc(labels[d.pick])}${d.pick === "draw" ? "" : " to win"} · ${pct(d.prob[d.pick])}</strong></div><p class="caption-note">${esc(d.note)}</p></section>
  <section class="panel"><div class="panel-head"><h2>The model’s track record</h2>${tag(`HOLDOUT ${m.test_season}`)}</div><p class="desc">Trained on ${num(m.n_train)} earlier matches, tested on ${num(m.n_test)} later matches. These results come from the held-out model, before refitting for predictions.</p>${metricsHtml(
    [
      [pct(m.accuracy), "Three-way accuracy"],
      [pct(m.baseline), "Always-home-win baseline"],
      [m.log_loss, "Log loss · lower is better"],
    ],
  )}<p class="caption-note">${m.accuracy > m.baseline ? `Accuracy is ${((m.accuracy - m.baseline) * 100).toFixed(1)} percentage points above` : "Accuracy does not exceed"} the home-win baseline. Training ends ${m.train_end}; testing starts ${m.test_start}.</p><div class="mini-bars">${d.importance
    .slice(0, 5)
    .map(
      (f) =>
        `<div class="bar-row"><span>${pretty(f.feature)}</span><div class="bar-track"><div class="bar-fill" style="width:${(f.importance / Math.max(...d.importance.map((x) => x.importance))) * 100}%"></div></div><span>${pct(f.importance)}</span></div>`,
    )
    .join("")}</div>${plot("match", "Show held-out confusion matrix")}</section>
  <section class="panel"><div class="panel-head"><h2>Prediction audit</h2><span class="notice-count">Latest 8 test matches</span></div><div class="table-wrap"><table><thead><tr><th>Match</th><th>Prediction</th><th>Actual</th><th>Result</th></tr></thead><tbody>${d.audit
    .slice(-8)
    .reverse()
    .map(
      (a) =>
        `<tr><td class="team-cell">${esc(a.home_team)} – ${esc(a.away_team)}<small class="result-date">${a.date}</small></td><td>${["Home", "Draw", "Away"][a.predicted]}</td><td>${["Home", "Draw", "Away"][a.target]}</td><td>${tag(a.correct ? "Correct" : "Miss", a.correct ? "imported" : "")}</td></tr>`,
    )
    .join("")}</tbody></table></div></section>`;
}

function playerPicker(scout = false) {
  const players = (scout ? context.scout_players : context.players).filter(
    (p) => !scout || (p.position !== "GK" && p.minutes >= 270),
  );
  const initial =
    players.find((p) => p.player === "Bukayo Saka") ||
    players.find((p) => p.player === "Lamine Yamal") ||
    players[0];
  return `<div class="field"><label for="player-search">Search a player</label><input id="player-search" list="player-options" value="${esc(initial?.player || "")}" autocomplete="off" required><datalist id="player-options">${players.map((p) => `<option value="${esc(p.player)}">${esc(p.team)} · ${p.position}</option>`).join("")}</datalist></div>`;
}
function transferPage() {
  const fields = [
    ["age", "Age", 24],
    ["minutes", "Minutes", 2500],
    ["goals", "Goals", 12],
    ["assists", "Assists", 8],
    ["shots", "Shots", 70],
    ["key_passes", "Key passes", 45],
    ["dribbles", "Dribbles", 50],
    ["tackles", "Tackles", 25],
    ["interceptions", "Interceptions", 15],
  ];
  return `${leagueShell("transfers")}${sourceNote()}<div class="workspace-layout"><section class="panel control-panel"><div class="panel-head"><h2>Player valuation</h2>${tag("€ MILLIONS")}</div><form id="transfer-form">${playerPicker()}<button class="button full">Estimate value ↗</button></form><div class="divider"></div><div class="eyebrow">THE MODEL</div><p class="desc">Linear regression using goals, assists, minutes, age and position. Named-player estimates use a model trained only on earlier seasons. Reference values are dated after the final match.</p><details><summary>Build a custom player <span>＋</span></summary><p class="caption-note">Try a different statistical profile. This uses the same ${context.player_source.kind === "demo" ? "demo-trained" : "competition"} model.</p><form id="custom-form"><div class="field"><label for="custom-position">Position</label><select id="custom-position">${options(["FW", "MF", "DF", "GK"], "FW")}</select></div><div class="field-row">${fields.filter(([key]) => context.player_source.features.includes(key)).map(([key, label, value]) => `<div class="field"><label for="custom-${key}">${label}</label><input id="custom-${key}" name="${key}" type="number" min="${key === "age" ? 14 : key === "minutes" ? 1 : 0}" ${key === "age" ? 'max="50"' : key === "minutes" ? 'max="7000"' : ""} value="${value}" required></div>`).join("")}</div><button class="button full secondary">Estimate custom player ↗</button></form></details></section><div id="tool-result" class="result-stack" aria-live="polite"></div></div>`;
}
function transferResult(d) {
  const m = d.metrics;
  return `<section class="panel valuation"><div class="player-title"><span class="player-avatar">${esc(initials(d.player).slice(0, 2))}</span><div><h2>${esc(d.player)}</h2><p>${esc(d.team)} · ${d.position} · ${d.season}</p></div></div><div class="value-comparison"><div><small>${esc(d.prediction_basis)}</small><div class="number accent">${money(d.predicted_value)}</div></div><div><small>${d.provenance.kind === "demo" ? "SYNTHETIC REFERENCE" : "REFERENCE MARKET VALUE"}</small><div class="number">${d.reference_value === null ? "—" : money(d.reference_value)}</div></div></div>${d.difference !== null ? `<div class="model-pick"><span>Estimate vs reference</span><strong>${d.difference > 0 ? "+" : ""}€${d.difference.toFixed(1)}m ${d.difference >= 0 ? "above" : "below"} reference</strong></div>` : ""}<div class="stat-chips">${[
    ["age", "Age"],
    ["minutes", "Minutes"],
    ["goals", "Goals"],
    ["assists", "Assists"],
  ]
    .map(
      ([k, label]) =>
        `<div><strong>${num(d.stats[k])}</strong><small>${label}</small></div>`,
    )
    .join(
      "",
    )}</div><p class="caption-note">Market values are reference estimates, not completed transfer fees.${d.valuation_date ? ` Statistics through ${esc(d.feature_cutoff)}; reference dated ${esc(d.valuation_date)}. This player-season was excluded from training this estimate.` : " Custom estimates use the model refitted on all observed seasons."}</p></section>
  <section class="panel"><div class="panel-head"><h2>How close does the model get?</h2>${tag(`HOLDOUT ${m.test_season}`)}</div><p class="desc">Evaluation on ${num(m.n_test)} player-seasons, trained on ${num(m.n_train)} earlier observations. ${d.provenance.kind === "demo" ? "These scores measure fit to generated tutorial data." : ""}</p>${metricsHtml(
    [
      [`€${m.mae_eur_m}m`, "Mean absolute error"],
      [m.r2, "R² score"],
      [m.n_test, "Held-out player-seasons"],
    ],
  )}<p class="caption-note">Median-value baseline error: €${m.baseline_mae_eur_m}m. ${m.mae_eur_m < m.baseline_mae_eur_m ? "The model improves on this baseline." : "The model does not improve on this baseline."}</p>${plot("transfer", "Show predicted vs reference values")}</section>
  ${d.history.length ? `<section class="panel"><div class="panel-head"><h2>Season by season</h2>${tag(d.provenance.kind === "demo" ? "DEMO STATS" : "OBSERVED STATS")}</div><div class="table-wrap"><table><thead><tr><th>Season</th><th>Minutes</th><th>Goals</th><th>Assists</th><th>Reference</th></tr></thead><tbody>${d.history.map((r) => `<tr><td>${r.season}</td><td>${num(r.minutes)}</td><td>${r.goals}</td><td>${r.assists}</td><td>€${Number(r.market_value_eur_m).toFixed(1)}m</td></tr>`).join("")}</tbody></table></div></section>` : ""}`;
}

function scoutingPage() {
  return `${leagueShell("scouting")}${sourceNote(true)}<div class="workspace-layout"><section class="panel control-panel"><div class="panel-head"><h2>Find a similar player</h2></div><form id="scout-form">${playerPicker(true)}<div class="field-row"><div class="field"><label for="match-count">Results</label><select id="match-count">${options(["5", "8", "12"], "8")}</select></div><div class="field"><label for="position-filter">Position</label><select id="position-filter"><option value="">All outfield</option><option value="FW">Forwards</option><option value="MF">Midfielders</option><option value="DF">Defenders</option></select></div></div><button class="button full">Find similar players ↗</button></form><div class="divider"></div><div class="eyebrow">STYLE, NOT REPUTATION</div><p class="desc">${context.scout_source.features.length} observed statistics per 90 minutes: ${context.scout_source.features.map(pretty).join(", ")}. ${context.scout_source.scope === "basic" ? "Basic attacking comparison only; this does not measure a complete playing style." : "Standardised distances reveal the closest profiles."}</p><p class="caption-note">Outfield players with at least 270 minutes. K-means groups shared styles. Similarity describes statistical distance; it is not a probability of equal ability.</p></section><div id="tool-result" class="result-stack" aria-live="polite"></div></div>`;
}
function radar(d) {
  const keys = d.features, labels = keys.map(pretty);
  if (keys.length < 3) {
    return `<div class="mini-bars"><h3>Basic attacking profile</h3>${keys.map(k => `<p>${pretty(k)} / 90: <strong>${d.per90[k].toFixed(2)}</strong></p>`).join('')}<p class="caption-note">Advanced scouting statistics are unavailable for this snapshot.</p></div>`;
  }
  const nearest = d.matches[0],
    all = [d, ...d.matches];
  const point = (i, scale) => {
    const a = (i / keys.length) * Math.PI * 2 - Math.PI / 2;
    return [150 + Math.cos(a) * 85 * scale, 137 + Math.sin(a) * 85 * scale];
  };
  const polygon = (scale) =>
    keys.map((_, i) => point(i, scale).join(",")).join(" ");
  const values = (player) =>
    keys
      .map((k, i) =>
        point(
          i,
          player.per90[k] / Math.max(0.01, ...all.map((p) => p.per90[k])),
        ).join(","),
      )
      .join(" ");
  return `<svg viewBox="0 0 300 286" class="radar" role="img" aria-label="Per-90 style comparison of ${esc(d.player)}${nearest ? " and " + esc(nearest.player) : ""}. Each axis is scaled to the maximum among displayed players.">${[0.33, 0.66, 1].map((s) => `<polygon points="${polygon(s)}" fill="none" stroke="#394733" stroke-width="1"/>`).join("")}${keys.map((_, i) => `<line x1="150" y1="137" x2="${point(i, 1)[0]}" y2="${point(i, 1)[1]}" stroke="#303d2b"/>`).join("")}${nearest ? `<polygon points="${values(nearest)}" fill="#97aeb422" stroke="#97aeb4" stroke-width="1.5"/>` : ""}<polygon points="${values(d)}" fill="${context.competition.color}22" stroke="${context.competition.color}" stroke-width="2"/>${labels.map((l, i) => `<text x="${point(i, 1.29)[0]}" y="${point(i, 1.24)[1] + 3}" font-size="9" fill="#acb9a1" text-anchor="middle">${l}</text>`).join("")}<text x="150" y="270" font-size="9" fill="#819174" text-anchor="middle">Per-90 profile · relative to displayed players</text></svg>`;
}
function scoutResult(d) {
  return `<section class="panel"><div class="scout-profile"><div><div class="player-title"><span class="player-avatar">${esc(initials(d.player).slice(0, 2))}</span><div><h2>${esc(d.player)}</h2><p>${esc(d.team)} · ${d.position} · age ${d.age} · ${esc(d.season)}</p></div></div><div class="spaced">${tag(d.cluster)}</div><p class="desc spaced">A profile built around ${esc(d.cluster.split(" · ")[0].toLowerCase())}.</p><p class="caption-note"><span class="accent">● ${esc(d.player)}</span>${d.matches[0] ? `<br><span style="color:#97aeb4">● ${esc(d.matches[0].player)}</span>` : ""}</p><div class="stat-chips">${d.features.slice(0, 4).map((k) => `<div><strong>${d.per90[k].toFixed(2)}</strong><small>${k === "key_passes" ? "Key passes" : pretty(k)} / 90</small></div>`).join("")}</div></div>${radar(d)}</div></section>
  <section class="panel"><div class="panel-head"><div><h2>Closest statistical matches</h2><p class="desc">${d.matches.length} profiles · compare per-90 performance</p></div><a class="button secondary small" id="export-scout" href="${esc(d.export_url)}" download>Export CSV ↓</a></div>${d.matches.length ? `<div class="table-wrap"><table><thead><tr><th>Player</th><th>Similarity</th>${d.features.map(k => `<th>${pretty(k)}/90</th>`).join("")}<th>Style</th></tr></thead><tbody>${d.matches.map((m) => `<tr><td><button class="text-button scout-compare" data-player="${esc(m.player)}">${esc(m.player)}</button><small class="result-date">${esc(m.team)} · ${m.position}</small></td><td><span class="similarity"><span class="bar-track"><span class="bar-fill" style="display:block;width:${m.similarity * 100}%"></span></span>${pct(m.similarity)}</span></td>${d.features.map((k) => `<td>${m.per90[k].toFixed(2)}</td>`).join("")}<td>${esc(m.cluster)}</td></tr>`).join("")}</tbody></table></div>` : '<p class="desc">No players match this position filter. Try another position.</p>'}<p class="caption-note">Click a player to explore their closest matches. Similarity uses a fixed distance scale and stays consistent when you change the result count.</p></section>
  <section class="panel"><div class="panel-head"><h2>Playing-style clusters</h2>${tag("K-MEANS")}</div><p class="desc">Profiles grouped by their standardised per-90 statistics. Group numbers distinguish clusters with similar dominant traits.</p><div class="scout-clusters">${d.clusters.map((c) => tag(`${c.name} · ${c.size} players`)).join("")}</div>${plot("scouting", "Show the full player style map")}</section>`;
}

function bindPage(page) {
  const base = `/api/workspaces/${context.competition.slug}`;
  if (page === "matches")
    $("match-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const body = {
        home: $("home-team").value,
        away: $("away-team").value,
        neutral: $("neutral")?.checked || false,
      };
      runTask(
        "Analysing form and testing the model…",
        (signal) =>
          api(`${base}/match`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
            signal,
          }),
        matchResult,
      );
    });
  if (page === "transfers") {
    const run = () => {
      const player = $("player-search").value;
      runTask(
        "Estimating player value…",
        (signal) =>
          api(`${base}/transfer?player=${encodeURIComponent(player)}`, {
            signal,
          }),
        transferResult,
      );
    };
    $("transfer-form").addEventListener("submit", (e) => {
      e.preventDefault();
      run();
    });
    $("custom-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const body = Object.fromEntries(new FormData(e.target));
      body.position = $("custom-position").value;
      runTask(
        "Estimating your custom profile…",
        (signal) =>
          api(`${base}/transfer`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
            signal,
          }),
        transferResult,
      );
    });
    run();
  }
  if (page === "scouting") {
    const run = () => {
      const q = new URLSearchParams({
        player: $("player-search").value,
        k: $("match-count").value,
        position: $("position-filter").value,
      });
      runTask(
        "Finding the closest playing styles…",
        (signal) => api(`${base}/scouting?${q}`, { signal }),
        scoutResult,
      );
    };
    $("scout-form").addEventListener("submit", (e) => {
      e.preventDefault();
      run();
    });
    $("tool-result").addEventListener("click", (e) => {
      const compare = e.target.closest(".scout-compare");
      if (compare) {
        $("player-search").value = compare.dataset.player;
        run();
      }
    });
    run();
  }
}
async function navigate() {
  const revision = ++routeVersion;
  ++taskVersion;
  activeController?.abort();
  const parts = location.pathname.split("/").filter(Boolean);
  const slug = parts[0] === "competitions" ? parts[1] : null,
    page = parts[2] || "overview";
  document.documentElement.style.setProperty("--accent", "#b7f66b");
  renderNav(slug);
  if (!slug) {
    context = null;
    hub();
    return;
  }
  $("content").innerHTML = loading("Opening competition workspace…");
  try {
    const data = await api(`/api/workspaces/${slug}`);
    if (revision !== routeVersion) return;
    context = data;
    if (!pages[page]) throw new Error("This page does not exist.");
    $("content").innerHTML = {
      overview: overviewPage,
      matches: matchPage,
      transfers: transferPage,
      scouting: scoutingPage,
    }[page]();
    bindPage(page);
  } catch (e) {
    if (revision === routeVersion)
      $("content").innerHTML =
        `<div class="error" role="alert">${esc(e.message)} <a href="/">Return to the competition hub →</a></div>`;
  }
}
document.addEventListener("click", (e) => {
  const a = e.target.closest("a");
  if (
    !a ||
    e.ctrlKey ||
    e.metaKey ||
    e.shiftKey ||
    e.altKey ||
    e.button !== 0 ||
    a.download ||
    a.target
  )
    return;
  const url = new URL(a.href);
  if (
    url.origin === location.origin &&
    (url.pathname === "/" || url.pathname.startsWith("/competitions/"))
  ) {
    e.preventDefault();
    history.pushState({}, "", url.pathname);
    navigate();
    window.scrollTo(0, 0);
    $("content").focus({ preventScroll: true });
  }
});
window.addEventListener("popstate", navigate);
(async () => {
  try {
    competitions = await api("/api/workspaces");
    await navigate();
  } catch (e) {
    $("content").innerHTML =
      `<div class="error" role="alert">${esc(e.message)} Reload this page to reconnect.</div>`;
  }
})();

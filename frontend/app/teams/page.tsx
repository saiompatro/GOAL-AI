import { listInsights, listTeams } from "@/lib/data";

export default async function TeamsPage() {
  const [teams, insights] = await Promise.all([listTeams(), listInsights("team")]);
  const insightByTeamId = new Map(insights.map((insight) => [insight.entityId, insight]));

  return (
    <div className="page-stack">
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Narrative Layer</p>
            <h1>Team insights</h1>
          </div>
          <p className="section-copy">
            These summaries are intended to stay grounded in the offline ML pipeline: they are generated ahead of time
            from Elo, form, and squad-strength signals and cached in Supabase.
          </p>
        </div>
      </section>

      <div className="card-grid card-grid--three">
        {teams.map((team) => {
          const insight = insightByTeamId.get(team.id);
          return (
            <article className="panel" key={team.id}>
              <div className="panel-title-row">
                <h2>{team.name}</h2>
                <span className="pill">{team.confederation ?? "Unknown confed."}</span>
              </div>
              <p className="section-copy">{team.code ?? "No team code"}</p>
              <p className="team-copy">{insight?.summaryText ?? "No insight generated yet."}</p>
              <div className="team-meta">HF model: {insight?.model ?? "—"}</div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

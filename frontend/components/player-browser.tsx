"use client";

import { useMemo, useState } from "react";

import type { Player, Team } from "@/types/models";

interface PlayerBrowserProps {
  players: Player[];
  teams: Team[];
}

function describePlayer(player: Player): string {
  switch (player.position) {
    case "GK":
      return `${player.name} projects as a shot-stopper and distributor, bringing calm handling and a steady base for tournament football.`;
    case "DF":
      return `${player.name} profiles as a defensive anchor with reliable duel-winning and enough passing to start progressive moves.`;
    case "MF":
      return `${player.name} links phases well through midfield and gives the side progression between build-up and final-third control.`;
    default:
      return `${player.name} is the lineup's attacking pressure point, offering movement, finishing, and direct transition threat.`;
  }
}

export function PlayerBrowser({ players, teams }: PlayerBrowserProps) {
  const [selectedTeam, setSelectedTeam] = useState(
    teams.find((team) => team.name === "Brazil")?.name ?? teams[0]?.name ?? "",
  );

  const lineup = useMemo(
    () => players.filter((player) => player.teamName === selectedTeam).slice(0, 11),
    [players, selectedTeam],
  );

  return (
    <div className="page-stack">
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Squad Lens</p>
            <h1>Player analysis</h1>
          </div>
          <p className="section-copy">
            Player cards reuse the original lineup view, but now with typed attribute models so pace, shooting,
            passing, and defending stay consistent across the app.
          </p>
        </div>

        <label className="field field--compact">
          <span>Team</span>
          <select value={selectedTeam} onChange={(event) => setSelectedTeam(event.target.value)}>
            {teams.map((team) => (
              <option key={team.id} value={team.name}>
                {team.name}
              </option>
            ))}
          </select>
        </label>
      </section>

      {!lineup.length ? (
        <section className="panel empty-state">No players were found for this squad.</section>
      ) : (
        <div className="card-grid card-grid--three">
          {lineup.map((player) => (
            <article className="panel panel--player" key={player.id}>
              <div className="player-card__header">
                <div>
                  <h2>{player.name}</h2>
                  <p className="section-copy">{player.teamName}</p>
                </div>
                <span className="pill">{player.position}</span>
              </div>

              <div className="rating-block">{player.overall}</div>

              <div className="detail-list">
                <div className="detail-row">
                  <span>Pace</span>
                  <strong>{player.attrs.pace}</strong>
                </div>
                <div className="detail-row">
                  <span>Shooting</span>
                  <strong>{player.attrs.shooting}</strong>
                </div>
                <div className="detail-row">
                  <span>Passing</span>
                  <strong>{player.attrs.passing}</strong>
                </div>
                <div className="detail-row">
                  <span>Defending</span>
                  <strong>{player.attrs.defending}</strong>
                </div>
              </div>

              <p className="player-card__insight">{describePlayer(player)}</p>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

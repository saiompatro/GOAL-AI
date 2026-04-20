import { PlayerBrowser } from "@/components/player-browser";
import { listPlayers, listTeams } from "@/lib/data";

export default async function PlayersPage() {
  const [players, teams] = await Promise.all([listPlayers(), listTeams()]);

  return <PlayerBrowser players={players} teams={teams} />;
}

import { PredictionWorkbench } from "@/components/prediction-workbench";
import { listPredictions, listTeams } from "@/lib/data";

export default async function PredictPage() {
  const [teams, predictions] = await Promise.all([listTeams(), listPredictions()]);

  return <PredictionWorkbench teams={teams} predictions={predictions} />;
}

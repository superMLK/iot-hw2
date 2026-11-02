import type { StepId } from "../route";
import type { DatasetResult } from "../types/dataset";
import BusinessStep from "./BusinessStep";
import DataStep from "./DataStep";
import DeploymentStep from "./DeploymentStep";
import EvaluationStep from "./EvaluationStep";
import ModelingStep from "./ModelingStep";
import PreparationStep from "./PreparationStep";

export default function StepContent({ data, step }: { data: DatasetResult; step: StepId }) {
  switch (step) {
    case "business":
      return <BusinessStep data={data} />;
    case "data":
      return <DataStep data={data} />;
    case "preparation":
      return <PreparationStep data={data} />;
    case "modeling":
      return <ModelingStep data={data} />;
    case "evaluation":
      return <EvaluationStep data={data} />;
    case "deployment":
      return <DeploymentStep data={data} />;
  }
}

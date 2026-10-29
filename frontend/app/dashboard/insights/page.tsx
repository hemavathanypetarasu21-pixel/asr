import PageHeader from "@/components/dashboard/PageHeader";
import InsightsWorkspace from "@/components/insights/InsightsWorkspace";

export default function InsightsPage() {
  return (
    <>
      <PageHeader
        title="Insights"
        eyebrow="Analyse your recordings"
        description="Open a recording and select Analyse to detect its dialect and translate it to English."
      />
      <InsightsWorkspace />
    </>
  );
}

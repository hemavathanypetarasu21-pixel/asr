import PageHeader from "@/components/dashboard/PageHeader";
import DatasetWorkspace from "@/components/dataset/DatasetWorkspace";

export default function DatasetPage() {
  return (
    <>
      <PageHeader
        title="Dataset"
        eyebrow="Speech datasets"
        description="Clips imported from open speech datasets, with their original transcripts, speaker, split and licence. Read-only."
      />
      <DatasetWorkspace />
    </>
  );
}

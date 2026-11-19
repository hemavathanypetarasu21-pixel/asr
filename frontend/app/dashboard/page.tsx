import ChatWorkspace from "@/components/chat/ChatWorkspace";
import PageHeader from "@/components/dashboard/PageHeader";

export default function ChatPage() {
  return (
    <>
      <PageHeader
        title="Chat"
        eyebrow="Malay + English · Tamil + English"
        description="Pick your language, then speak or upload audio. Recordings are saved for analysis in Insights."
      />
      <ChatWorkspace />
    </>
  );
}

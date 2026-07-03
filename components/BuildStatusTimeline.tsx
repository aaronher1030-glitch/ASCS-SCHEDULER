type BuildStage = "queued" | "running" | "succeeded" | "failed" | "published";

const orderedStages: BuildStage[] = ["queued", "running", "succeeded", "published"];

export function BuildStatusTimeline({ status }: { status: BuildStage }) {
  return (
    <ol style={{ display: "flex", gap: 12, listStyle: "none", padding: 0 }}>
      {orderedStages.map((stage) => {
        const active = orderedStages.indexOf(stage) <= orderedStages.indexOf(status);
        const isFailed = status === "failed" && stage === "running";
        return (
          <li
            key={stage}
            style={{
              padding: "8px 12px",
              borderRadius: 999,
              background: isFailed ? "#EF4444" : active ? "#19B37A" : "#1F2630",
              color: "#E6EDF3",
              textTransform: "capitalize",
            }}
          >
            {stage}
          </li>
        );
      })}
    </ol>
  );
}

type BuildKpiCardsProps = {
  queued: number;
  running: number;
  succeeded: number;
  failed: number;
};

export function BuildKpiCards(props: BuildKpiCardsProps) {
  return (
    <section style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
      <Kpi label="Queued" value={props.queued} />
      <Kpi label="Running" value={props.running} />
      <Kpi label="Succeeded" value={props.succeeded} />
      <Kpi label="Failed" value={props.failed} />
    </section>
  );
}

function Kpi({ label, value }: { label: string; value: number }) {
  return (
    <article style={{ padding: 16, borderRadius: 12, background: "#161B22", color: "#E6EDF3" }}>
      <div style={{ fontSize: 12, opacity: 0.8 }}>{label}</div>
      <strong style={{ fontSize: 24 }}>{value}</strong>
    </article>
  );
}

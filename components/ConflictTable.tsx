export type ConflictRow = {
  code: string;
  message: string;
  severity: string;
  suggestedAction?: string;
};

type ConflictTableProps = {
  rows: ConflictRow[];
};

export function ConflictTable({ rows }: ConflictTableProps) {
  return (
    <table style={{ width: "100%", borderCollapse: "collapse", background: "#161B22", color: "#E6EDF3" }}>
      <thead>
        <tr>
          <th style={th}>Code</th>
          <th style={th}>Severity</th>
          <th style={th}>Message</th>
          <th style={th}>Suggested Action</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, idx) => (
          <tr key={`${row.code}-${idx}`}>
            <td style={td}>{row.code}</td>
            <td style={td}>{row.severity}</td>
            <td style={td}>{row.message}</td>
            <td style={td}>{row.suggestedAction ?? "Review manually"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

const th = { borderBottom: "1px solid #30363D", textAlign: "left" as const, padding: 12 };
const td = { borderBottom: "1px solid #30363D", padding: 12 };

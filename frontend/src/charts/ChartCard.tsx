import { useState } from "react";
import { Card, CardTitle, Skeleton, cx } from "../components/ui";

interface ChartCardProps {
  title: string;
  subtitle?: string;
  howToRead?: string;
  loading?: boolean;
  empty?: boolean;
  tableColumns?: { key: string; label: string }[];
  tableRows?: Record<string, string | number>[];
  children: React.ReactNode;
}

export function ChartCard({ title, subtitle, howToRead, loading, empty, tableColumns, tableRows, children }: ChartCardProps) {
  const [showTable, setShowTable] = useState(false);
  const hasTable = Boolean(tableColumns && tableRows);
  const content = empty ? <div className="h-64 flex flex-col items-center justify-center rounded-lg border border-dashed border-edge p-4 text-center"><div className="mb-2 text-[11px] text-slate-400">No data available yet</div><div className="text-[10px] text-slate-500">Run a prediction to see this chart.</div></div> : loading ? <Skeleton className="h-64" /> : children;
  return (
    <Card className="p-4">
      <CardTitle title={title} sub={subtitle} />
      {howToRead && <p className="mt-1 mb-3 text-[10px] text-mute">{howToRead}</p>}
      <div className="relative">{content}</div>
      {hasTable && (
        <div className="mt-3 flex items-center gap-2"><button onClick={() => setShowTable((v) => !v)} className="text-[10px] text-mute hover:text-white underline-offset-2">{showTable ? "Hide table" : "Table"} <span className="text-[9px]">{showTable ? "▲" : "▼"}</span></button></div>
      )}
      {hasTable && showTable && tableColumns && tableRows && (
        <div className="mt-3 overflow-x-auto"><table className="w-full text-[11px] border-collapse"><thead><tr>{tableColumns.map((c) => <th key={c.key} className="label px-2 py-2 !text-[9px] text-left">{c.label}</th>)}</tr></thead><tbody>{tableRows.map((row, ri) => (
          <tr key={ri} className="border-t border-edge">{tableColumns.map((c) => <td key={c.key} className="px-2 py-2">{row[c.key]}</td>)}</tr>
        ))}</tbody></table></div>
      )}
    </Card>
  );
}

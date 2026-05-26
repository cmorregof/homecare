export function VitalCard({ label, value, unit }: { label: string; value: string | number; unit?: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <p className="text-sm font-medium text-slate-600">{label}</p>
      <div className="mt-2 flex items-end gap-1">
        <p className="text-2xl font-semibold tracking-normal text-ink">{value}</p>
        {unit ? <p className="pb-1 text-xs font-medium text-slate-500">{unit}</p> : null}
      </div>
    </div>
  );
}

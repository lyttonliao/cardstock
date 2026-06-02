export default function KPITile({ title, subtitle, context, subtitleTone, contextTone }: {
  title: string,
  subtitle: string,
  context?: string,
  subtitleTone?: "up" | "down" | "neutral",
  contextTone?: "up" | "down" | "neutral",
}) {
  const subtitleClass =
    subtitleTone === "up" ? "text-bull" :
    subtitleTone === "down" ? "text-bear" :
    "text-fg-1";
  const contextClass =
    contextTone === "up" ? "text-bull" :
    contextTone === "down" ? "text-bear" :
    "text-fg-1";
  return (
    <div className="p-6 border border-border rounded-xl bg-surface">
      <div className="flex flex-col gap-1">
        <p className="text-[13px] text-fg-4 font-display font-semibold">{title}</p>
        <h1 className={`text-3xl font-mono font-bold ${subtitleClass}`}>{subtitle}</h1>
        {context && (
          <p className={`text-xs font-mono text-fg-3 ${contextClass}`}>{context}</p>
        )}
      </div>
    </div>
  )
}
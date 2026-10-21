// One card on the Settings page: a heading, a short explanation and its form
export default function Section({ title, description, aside, children }) {
  return (
    <section className="rounded-xl border border-line bg-surface">
      <div className="flex flex-wrap items-start justify-between gap-2 border-b border-line px-4 py-4 sm:px-5">
        <div className="min-w-0">
          <h3 className="font-display text-[16px] font-bold text-brand-ink">{title}</h3>
          {description && <p className="mt-0.5 text-[13px] text-muted">{description}</p>}
        </div>
        {aside}
      </div>
      {children}
    </section>
  )
}

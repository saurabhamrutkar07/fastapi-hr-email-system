// Temporary page used by every route until that page is built
export default function ComingSoon({ title, description }) {
  return (
    <div>
      <h2 className="font-display text-[22px] font-bold text-brand-ink sm:text-[26px]">{title}</h2>
      <p className="mt-0.5 text-muted">{description}</p>
      <div className="mt-5 rounded-xl border border-dashed border-line bg-surface p-8 text-center text-muted">
        This page is built in a later step.
      </div>
    </div>
  )
}

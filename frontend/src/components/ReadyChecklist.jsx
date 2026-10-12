import { Link } from 'react-router'
import Icon from './Icon'

// The three setup checks from useSetupStatus(). A row that isn't ready links to the page that fixes it.
export default function ReadyChecklist({ setup }) {
  const { items, loading, readyCount, total, allReady } = setup

  return (
    <section className="rounded-xl border border-line bg-surface">
      <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3.5 sm:px-5">
        <h3 className="font-display text-[15.5px] font-bold text-brand-ink">Ready to send</h3>
        {!loading && (
          <span
            className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
              allReady ? 'bg-ok-soft text-ok-text' : 'bg-warn-soft text-warn-text'
            }`}
          >
            {readyCount} of {total}
          </span>
        )}
      </div>

      <ul>
        {items.map((item) => (
          <li key={item.to} className="border-b border-line last:border-b-0">
            {item.api.loading ? (
              <div className="flex items-center gap-3 px-4 py-3.5 sm:px-5" aria-hidden="true">
                <div className="size-6 animate-pulse rounded-full bg-surface-2" />
                <div className="h-3.5 flex-1 animate-pulse rounded bg-surface-2" />
              </div>
            ) : (
              <Link to={item.to} className="flex items-center gap-3 px-4 py-3 hover:bg-surface-2 sm:px-5">
                <span
                  className={`grid size-6 shrink-0 place-items-center rounded-full ${
                    item.ready ? 'bg-ok-soft text-ok-text' : 'bg-warn-soft text-warn-text'
                  }`}
                >
                  <Icon name={item.ready ? 'check' : 'alert'} className="size-3.5" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block font-semibold">{item.title}</span>
                  <span className="block text-[12.5px] text-muted [overflow-wrap:anywhere]">
                    {item.api.error ? "Couldn't check this right now." : item.detail}
                  </span>
                </span>
                <Icon name="chevron" className="size-4 text-muted" />
              </Link>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}

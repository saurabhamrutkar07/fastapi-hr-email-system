const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

// "2026-10-12" -> "12 Oct". Split by hand so the date never shifts with the timezone.
function shortDate(isoDate) {
  const [, month, day] = isoDate.split('-').map(Number)
  return `${day} ${MONTHS[month - 1]}`
}

// Picks a round top for the axis and 2-4 whole-number gridlines: max 31 -> top 40, lines 0 / 20 / 40
function niceScale(max) {
  const rough = max / 3
  const power = 10 ** Math.floor(Math.log10(rough))
  const step = Math.max(1, [1, 2, 5, 10].map((m) => m * power).find((s) => s >= rough))
  const top = Math.ceil(max / step) * step
  const ticks = []
  for (let value = 0; value <= top; value += step) ticks.push(value)
  return { top, ticks }
}

const PLOT_HEIGHT = 180

/*
  Stacked bar per day: green = sent, red = failed on top.
  `days` is the `daily` list from GET /email/stats, oldest first.
*/

export default function EmailsChart({ days }) {
  const max = Math.max(0, ...days.map((d) => d.sent + d.failed))
  const sentTotal = days.reduce((sum, d) => sum + d.sent, 0)
  const failedTotal = days.reduce((sum, d) => sum + d.failed, 0)

  return (
    <section className="rounded-xl border border-line bg-surface">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-3.5 sm:px-5">
        <h3 className="font-display text-[15.5px] font-bold text-brand-ink">Emails per day</h3>
        <div className="flex gap-4 text-[12.5px] text-muted">
          <span className="inline-flex items-center gap-1.5">
            <i className="size-2.5 rounded-sm bg-ok" />
            Sent
          </span>
          <span className="inline-flex items-center gap-1.5">
            <i className="size-2.5 rounded-sm bg-err" />
            Failed
          </span>
        </div>
      </div>

      {max === 0 ? (
        <div className="flex flex-col items-center gap-1 px-5 py-12 text-center">
          <p className="font-semibold">No emails in the last 14 days</p>
          <p className="text-[13px] text-muted">Each day you send, a bar shows up here.</p>
        </div>
      ) : (
        <Bars days={days} max={max} label={`Last ${days.length} days: ${sentTotal} sent, ${failedTotal} failed`} />
      )}
    </section>
  )
}

function Bars({ days, max, label }) {
  const { top, ticks } = niceScale(max)
  const middle = Math.floor((days.length - 1) / 2)

  return (
    <div className="px-4 pb-4 pt-5 sm:px-5" role="img" aria-label={label}>
      <div className="grid grid-cols-[28px_minmax(0,1fr)] gap-2">
        {/* Y axis numbers */}
        <div className="relative text-[11px] tabular-nums text-muted" style={{ height: PLOT_HEIGHT }}>
          {ticks.map((value) => (
            <span key={value} className="absolute right-0 translate-y-1/2" style={{ bottom: `${(value / top) * 100}%` }}>
              {value}
            </span>
          ))}
        </div>

        {/* Gridlines + bars */}
        <div className="relative" style={{ height: PLOT_HEIGHT }}>
          {ticks.map((value) => (
            <div
              key={value}
              className="absolute inset-x-0 border-t border-dashed border-line"
              style={{ bottom: `${(value / top) * 100}%` }}
            />
          ))}
          <div className="absolute inset-0 flex items-end gap-1 sm:gap-1.5">
            {days.map((day) => {
              const total = day.sent + day.failed
              return (
                <div
                  key={day.date}
                  className="flex min-w-0 flex-1 flex-col overflow-hidden rounded-t"
                  style={{ height: `${(total / top) * 100}%` }}
                  title={`${shortDate(day.date)}: ${day.sent} sent, ${day.failed} failed`}
                >
                  <div className="bg-err" style={{ height: total ? `${(day.failed / total) * 100}%` : 0 }} />
                  <div className="flex-1 bg-ok" />
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* X axis: first, middle and last day */}
      <div className="mt-1.5 flex justify-between pl-9 text-[11px] text-muted" aria-hidden="true">
        <span>{shortDate(days[0].date)}</span>
        <span>{shortDate(days[middle].date)}</span>
        <span>{shortDate(days[days.length - 1].date)}</span>
      </div>
    </div>
  )
}

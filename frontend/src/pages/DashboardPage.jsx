import { Link } from "react-router";
import { dashboardApi } from "../api/dashboard";
import { useAuth } from "../auth/context";
import Button, {ButtonLink} from "../components/Button";
import Alert from "../components/Alert";
import Icon from "../components/Icon";
import useApi from "../hooks/useApi";
import EmailsChart from '../components/EmailsChart'
import ReadyChecklist from '../components/ReadyChecklist'
import RecentSends from '../components/RecentSends'

function greeting(){
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 17) return 'Good afternoon'
    return 'Good evening'
}

const formatNumber = (n) => n.toLocaleString('en-IN')

export default function DashboardPage(){
    const { user } = useAuth()
    const stats = useApi(dashboardApi.stats)
    const firstName = user?.name?.split(" ")[0]??''

    return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-display text-[22px] font-bold text-brand-ink sm:text-[26px]">
            {greeting()}
            {firstName && `, ${firstName}`}
          </h2>
          <p className="mt-0.5 text-muted">Your outreach over the last 14 days.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <ButtonLink to="/contacts" variant="secondary">
            Import contacts
          </ButtonLink>
          <ButtonLink to="/send">
            <Icon name="send" />
            Send email
          </ButtonLink>
        </div>
      </div>

      <StatCards stats={stats} />
      
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
        <div className="flex min-w-0 flex-col gap-4">
          {stats.data ? <EmailsChart days={stats.data.daily} /> : !stats.error && <ChartSkeleton />}
          <RecentSends />
        </div>
        <div className="min-w-0">
          <ReadyChecklist />
        </div>
      </div>
    </div>
  )
}

function StatCards({ stats }){
    if (stats.error){
        return(
            <div className="flex flex-col items-start gap-3">
                <Alert>Couldn't load your numbers. {stats.error}</Alert>
                <Button variant="secondary" onClick={stats.reload}>
                Try again
                </Button>
            </div>
        )
    }
    const d = stats.data 
    const cards = d 
        ? [
            { label: 'Emails sent', value: formatNumber(d.total), note: 'last 14 days' },
            {
                label: 'Sent successfully',
                value: formatNumber(d.sent),
                note: d.success_rate === null ? 'nothing sent yet' : `${d.success_rate.toFixed(1)}% success rate`,
                tone: d.success_rate === null ? undefined : 'ok',
            },
            {
                label: 'Failed',
                value: formatNumber(d.failed),
                note: d.failed > 0 ? <Link to="/history" className="font-semibold text-link hover:underline">See what went wrong</Link> : 'none',
                tone: d.failed > 0 ? 'err' : undefined,
            },
            { label: 'HR contacts', value: formatNumber(d.contacts_total), note: 'ready to email' },  
        ]
        : null 

    return(
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {cards
            ? cards.map((card) => <StatCard key={card.label} {...card} />)
            : [1, 2, 3, 4].map((n) => <StatCardSkeleton key={n} />)}
        </div>
             
    )
}

const NOTE_TONES = { ok: 'text-ok-text', err: 'text-err-text' }

function StatCard({label, value, note, tone}) {
    return (
        <div className="min-w-0 rounded-xl border border-line bg-surface px-4 py-3.5 sm:px-5 sm:py-4">
            <p className="text-[12.5px] font-semibold text-muted">{label}</p>
            <p className="mt-1 font-display text-[28px] font-bold leading-tight tabular-nums">{value}</p>
            <p className={`mt-0.5 text-[12.5px] ${NOTE_TONES[tone] ?? 'text-muted'}`}>{note}</p>
        </div>
    )
}

function StatCardSkeleton() {
    return(
        <div className="rounded-xl border border-line bg-surface px-4 py-3.5 sm:px-5 sm:py-4" aria-hidden="true">
            <div className="h-3 w-20 animate-pulse rounded bg-surface-2" />
            <div className="mt-3 h-7 w-14 animate-pulse rounded bg-surface-2" />
            <div className="mt-2 h-3 w-24 animate-pulse rounded bg-surface-2" />
        </div>
    )
    
}

function ChartSkeleton() {
  return (
    <div className="rounded-xl border border-line bg-surface p-5" aria-hidden="true">
      <div className="h-4 w-32 animate-pulse rounded bg-surface-2" />
      <div className="mt-5 h-[180px] animate-pulse rounded bg-surface-2" />
    </div>
  )
}

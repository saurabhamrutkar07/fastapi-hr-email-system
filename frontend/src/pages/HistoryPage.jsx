import { useEffect, useState } from 'react'
import { getErrorMessage } from '../api/client'
import { historyApi } from '../api/history'
import { useAuth } from '../auth/context'
import Alert from '../components/Alert'
import Button, { ButtonLink } from '../components/Button'
import EmailDetail from '../components/history/EmailDetail'
import HistoryList from '../components/history/HistoryList'
import Icon from '../components/Icon'
import Input from '../components/Input'
import Modal from '../components/Modal'
import Pagination, { PAGE_SIZES } from '../components/Pagination'
import Select from '../components/Select'


const SEARCH_DELAY_MS = 300

// Every email sent, newest first. Filtering and paging happen on the backend, since history keeps growing.
export default function HistoryPage(){
    const { user } = useAuth()
    const isAdmin = user.role === 'admin'

    const [search, setSearch] = useState('')
    const [query, setQuery] = useState('') // `search` once typing pauses
    const [status, setStatus] = useState('')
    const [days, setDays] = useState('')
    const [page, setPage] = useState(1)
    const [pageSize, setPageSize] = useState(PAGE_SIZES[0])
    const [result, setResult] = useState({ data: null, error: '', loading: true })
    const [attempt, setAttempt] = useState(0)
    const [opened, setOpened] = useState(null)

    // Ask the backend only after the user stops typing, not on every key 
    useEffect(() => {
    const timer = setTimeout(() => setQuery(search.trim()), SEARCH_DELAY_MS)
    return () => clearTimeout(timer)
    }, [search])

    useEffect(() => {
    let cancelled = false
    setResult((prev) => ({ ...prev, error: '', loading: true }))
    historyApi
      .list({
        status: status || undefined,
        q: query || undefined,
        days: days || undefined,
        limit: pageSize,
        offset: (page - 1) * pageSize,
      })
      .then((data) => !cancelled && setResult({ data, error: '', loading: false }))
      .catch((err) => !cancelled && setResult({ data: null, error: getErrorMessage(err), loading: false }))
    // Ignore an answer that arrives after the filters changed again
    return () => {
      cancelled = true
    }
  }, [status, query, days, page, pageSize, attempt])

    // Any change to the filters starts again from page 1
    const changeFilter = (setter) => (event) => {
        setter(event.target.value)
        setPage(1)
    }


    function clearFilters() {
            setSearch('')
            setQuery('')
            setStatus('')
            setDays('')
            setPage(1)
        }

    const filtered = Boolean(query || status || days)
    const data = result.data

    return (
       <div className="flex flex-col gap-5">
            <div>
                <h2 className= "font-display text-[22px] font-bold text-brand-ink sm:text-[26px]">History</h2>
                <p className="mt-0.5 text-muted">
                    {isAdmin ? 'Every email sent from ColdReach, by everyone.' : 'Every email you’ve sent and how it went.'}
                </p>
            </div>

            <div className="flex flex-col gap-2.5 sm:flex-row">
                <label className="relative min-w-0 flex-1">
                <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted">
                    <Icon name="search" />
                </span>
                <Input
                    type="search"
                    value={search}
                    onChange={changeFilter(setSearch)}
                    placeholder="Search name, company or email"
                    aria-label="Search history"
                    className="pl-10"
                />
                </label>
                <div className="grid grid-cols-2 gap-2.5 sm:flex">
                    <Select value={status} onChange={changeFilter(setStatus)} aria-label="Filter by status" className="sm:w-36">
                        <option value="">All statuses</option>
                        <option value="SUCCESS">Sent</option>
                        <option value="FAILED">Failed</option>
                    </Select>
                    <Select value={days} onChange={changeFilter(setDays)} aria-label="Filter by date" className="sm:w-40">
                        <option value="">All time</option>
                        <option value="7">Last 7 days</option>
                        <option value="30">Last 30 days</option>
                        <option value="90">Last 90 days</option>
                    </Select>
                </div>
            </div>

            <section className="min-w-0 overflow-hidden rounded-xl border border-line bg-surface">
                {result.error ? (
                <div className="flex flex-col items-start gap-3 p-4 sm:p-5">
                    <Alert>Couldn’t load your history. {result.error}</Alert>
                    <Button variant="secondary" onClick={() => setAttempt((n) => n + 1)}>
                    Try again
                    </Button>
                </div>
                ) : !data ? (
                <div className="h-64 animate-pulse bg-surface-2" aria-hidden="true" />
                ) : data.total === 0 ? (
                <div className="flex flex-col items-center gap-3 px-4 py-12 text-center">
                    <p className="font-semibold">{filtered ? 'No emails match' : 'No emails sent yet'}</p>
                    <p className="text-[13.5px] text-muted">
                    {filtered ? 'Try other filters.' : 'Emails you send show up here with how each one went.'}
                    </p>
                    {filtered ? (
                    <Button variant="secondary" onClick={clearFilters}>
                        Clear filters
                    </Button>
                    ) : (
                    <ButtonLink to="/send">Send emails</ButtonLink>
                    )}
                </div>
                ) : (
                <div className={result.loading ? 'opacity-60' : ''}>
                    <HistoryList items={data.items} showSender={isAdmin} onOpen={setOpened} />
                    <Pagination
                    page={page}
                    pageSize={pageSize}
                    total={data.total}
                    onPageChange={setPage}
                    onPageSizeChange={(size) => {
                        setPageSize(size)
                        setPage(1)
                    }}
                    />
                </div>
                )}
            </section>

            <Modal
                open={Boolean(opened)}
                onClose={() => setOpened(null)}
                title={opened?.contact_name ?? opened?.recipient_email ?? 'Email'}
                description={opened?.company ?? undefined}
            >
                {opened && <EmailDetail requestId={opened.request_id} showSender={isAdmin} />}
            </Modal>
       </div> 


    )
}

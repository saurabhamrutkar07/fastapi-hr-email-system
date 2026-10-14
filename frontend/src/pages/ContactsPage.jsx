import { useMemo, useState } from "react";
import { contactsApi } from "../api/contacts";
import { useAuth } from "../auth/context";
import Alert from "../components/Alert";
import Button from "../components/Button";
import ContactList, { contactEmails, contactPhones } from "../components/ContactList";
import Icon from "../components/Icon";
import Input from '../components/Input'
import Pagination, { PAGE_SIZES } from "../components/Pagination";
import Select from "../components/Select";
import useApi from "../hooks/useApi";

const formatNumber = (n) => n.toLocaleString('en-IN')

export default function ContactsPage() {
    const { user } = useAuth()
    const isAdmin = user?.role === 'admin'
    const contacts = useApi(contactsApi.list)

    const [search, setSearch] = useState('')
    const [company, setCompany] = useState('')
    const [page,setPage] = useState(1)
    const [pageSize, setPageSize] = useState(PAGE_SIZES[0])    

    // Newest first (a bigger id was added later)
    const all = useMemo(() => [...(contacts.data ?? [])].sort((a, b) => b.id - a.id), [contacts.data])
  
    // Company names for the dropdown, A to Z, each once 
    const companies = useMemo(
        () => [...new Set(all.map((c) => c.company).filter(Boolean))].sort((a,b)=> a.localeCompare(b)),
        [all] 
    )

    // Search looks at name, title, company, every email and every phone 
    const matches = useMemo(() => {
        const words = search.trim().toLowerCase()
        return all.filter((c) => {
            if (company && c.company !== company) return false
            if (!words) return true
            const text = [c.name, c.title, c.company, ...contactEmails(c), ...contactPhones(c)].join(' ').toLowerCase()
            return text.includes(words)
        })
    }, [all, search, company])

    // If the list shrinks (a search, a smaller page count), never show a page past the end 
    const pageCount = Math.max(1,Math.ceil(matches.length/pageSize))
    const currentPage = Math.min(page,pageCount)
    const pageItems = matches.slice((currentPage - 1) * pageSize, currentPage * pageSize)

    // Any change to what is shown starts again from page 1 
    function changeSearch(value) {
        setSearch(value)
        setPage(1)
    }

    function changeCompany(value) {
        setCompany(value)
        setPage(1)
    }
    function changePageSize(value) {
        setPageSize(value)
        setPage(1)
    }
    function clearFilters() {
        changeSearch('')
        setCompany('')
    }

    const filtered = Boolean(search.trim()|| company)

    return(
        <div className="flex flex-col gap-5">
            <div>
                <h2 className="font-display text-[22px] font-bold text-brand-ink sm:text-[26px]">HR Contacts</h2>
                <p className="mt-0.5 text-muted">
                    {contacts.data
                    ? `${formatNumber(all.length)} recruiters across ${formatNumber(companies.length)} companies.`
                    : 'Recruiters you can email.'}
                </p>
            </div>
        
            {contacts.error ? (
                <div className="flex flex-col items-start gap-3">
                <Alert>Couldn't load contacts. {contacts.error}</Alert>
                <Button variant="secondary" onClick={contacts.reload}>
                    Try again
                </Button>
                </div>
            ) : (
                <>
                <div className="flex flex-col gap-2.5 sm:flex-row">
                    <label className="relative min-w-0 flex-1">
                    <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted">
                        <Icon name="search" />
                    </span>
                    <Input
                        type="search"
                        value={search}
                        onChange={(e) => changeSearch(e.target.value)}
                        placeholder="Search name, company or email"
                        aria-label="Search contacts"
                        className="pl-10"
                    />
                    </label>
                    <Select
                    value={company}
                    onChange={(e) => changeCompany(e.target.value)}
                    aria-label="Filter by company"
                    className="sm:w-56"
                    disabled={!contacts.data}
                    >
                    <option value="">All companies</option>
                    {companies.map((name) => (
                        <option key={name} value={name}>
                        {name}
                        </option>
                    ))}
                    </Select>
                </div>

                <section className="overflow-hidden rounded-xl border border-line bg-surface">
                    {contacts.loading ? (
                    <ListSkeleton />
                    ) : all.length === 0 ? (
                    <EmptyState title="No contacts yet" text="Recruiters added by you or your team show up here." />
                    ) : matches.length === 0 ? (
                    <EmptyState
                        title="No contacts match"
                        text={search.trim() ? `Nothing found for "${search.trim()}".` : 'No contacts at this company.'}
                        action={
                        <Button variant="secondary" onClick={clearFilters}>
                            Clear filters
                        </Button>
                        }
                    />
                    ) : (
                    <>
                        {filtered && (
                        <p className="border-b border-line px-4 py-2.5 text-[13px] text-muted sm:px-5">
                            {formatNumber(matches.length)} of {formatNumber(all.length)} contacts match.
                        </p>
                        )}
                        <ContactList contacts={pageItems} showAdded={isAdmin} />
                        <Pagination
                        page={currentPage}
                        pageSize={pageSize}
                        total={matches.length}
                        onPageChange={setPage}
                        onPageSizeChange={changePageSize}
                        />
                    </>
                    )}
                </section>
                </>
            )}

        </div>
    )
}

function EmptyState({title, text, action}) {

    return(
        <div className="flex flex-col items-center gap-1 px-5 py-12 text-center">
            <span className="mb-2 grid size-11 place-items-center rounded-full bg-surface-2 text-muted">
                <Icon name="users" className="size-5" />
            </span>
            <p className="font-semibold">{title}</p>
            <p className="text-[13px] text-muted">{text}</p>
            {action && <div className="mt-3">{action}</div>}
        </div>     
    )
}

function ListSkeleton() {
    return(
        <ul aria-hidden="true">
            {[1, 2, 3, 4, 5].map((n) => (
                <li key={n} className="flex items-center gap-3 border-b border-line px-4 py-3.5 last:border-b-0 sm:px-5">
                <div className="size-9 shrink-0 animate-pulse rounded-full bg-surface-2" />
                <div className="flex flex-1 flex-col gap-2">
                    <div className="h-3.5 w-40 max-w-full animate-pulse rounded bg-surface-2" />
                    <div className="h-3 w-56 max-w-full animate-pulse rounded bg-surface-2" />
                </div>
                </li>
            ))}
        </ul>
    )
    
}
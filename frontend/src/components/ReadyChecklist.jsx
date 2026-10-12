import { Link } from 'react-router'
import { dashboardApi } from '../api/dashboard'
import useApi from '../hooks/useApi'
import { formatDate } from '../utils/format'
import Icon from './Icon'

/*
  Sending needs three things set up. Each row checks one of them:
    email account (SMTP) -> GET /smtp-credentials/
    default template     -> GET /email-template/
    active resume        -> GET /resumes/
  A row that isn't ready links to the page that fixes it.
*/
export default function ReadyChecklist() {
  const smtp = useApi(dashboardApi.smtp)
  const templates = useApi(dashboardApi.templates)
  const resumes = useApi(dashboardApi.resumes)

  const defaultTemplate = templates.data?.find((t) => t.is_default)
  const activeResume = resumes.data?.find((r) => r.is_active)

  const items = [
    {
      api: smtp,
      ready: Boolean(smtp.data?.is_active),
      title: !smtp.data ? 'Connect your email account' : smtp.data.is_active ? 'Email account connected' : 'Email account is turned off',
      detail: smtp.data ? `${smtp.data.email_address} via ${smtp.data.smtp_server}` : 'Emails go out from your own Gmail.',
      to: '/settings',
    },
    {
      api: templates,
      ready: Boolean(defaultTemplate),
      title: defaultTemplate ? 'Default template set' : templates.data?.length ? 'Choose a default template' : 'Write your first template',
      detail: defaultTemplate ? defaultTemplate.name : 'This is the email each recruiter receives.',
      to: '/templates',
    },
    {
      api: resumes,
      ready: Boolean(activeResume),
      title: activeResume ? 'Active resume' : 'Upload your resume',
      detail: activeResume
        ? `Version ${activeResume.version_number} · uploaded ${formatDate(activeResume.uploaded_at)}`
        : 'It is attached to every email.',
      to: '/resumes',
    },
  ]

  const loading = items.some((item) => item.api.loading)
  const readyCount = items.filter((item) => item.ready).length

  return (
    <section className="rounded-xl border border-line bg-surface">
      <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3.5 sm:px-5">
        <h3 className="font-display text-[15.5px] font-bold text-brand-ink">Ready to send</h3>
        {!loading && (
          <span
            className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
              readyCount === items.length ? 'bg-ok-soft text-ok-text' : 'bg-warn-soft text-warn-text'
            }`}
          >
            {readyCount} of {items.length}
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

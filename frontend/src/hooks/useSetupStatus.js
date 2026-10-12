import { dashboardApi } from "../api/dashboard";
import { formatDate } from "../utils/format";
import useApi from "./useApi";

/*
  Sending needs three things set up. Each item checks one of them:
    email account (SMTP) -> GET /smtp-credentials/
    default template     -> GET /email-template/
    active resume        -> GET /resumes/
  Returns the items for the checklist plus a summary the page uses for its layout:
    { items, loading, readyCount, total, allReady, nextStep }
*/

export default function useSetupStatus(){
    const smtp = useApi(dashboardApi.smtp)
    const templates = useApi(dashboardApi.templates)
    const resumes = useApi(dashboardApi.resumes)
    
    const defaultTemplate = templates.data?.find((t)=> t.is_default)
    const activeResume = resumes.data?.find((r)=> r.is_active)

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
        }
    ]

    const loading = items.some((item) => item.api.loading)
  const readyCount = items.filter((item) => item.ready).length

  return {
    items,
    loading,
    readyCount,
    total: items.length,
    allReady: readyCount === items.length,
    // The first thing still to do, for the welcome banner's button
    nextStep: items.find((item) => !item.ready && !item.api.loading),
  }
}
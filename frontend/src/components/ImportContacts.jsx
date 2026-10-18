import { useState } from "react";
import { contactsApi } from "../api/contacts";
import { getErrorMessage } from "../api/client";
import Alert from "./Alert";
import Button from "./Button";
import Icon from "./Icon";

// What the backend accepts (see hr_contact_excel_service.py)
const EXTENSIONS = ['.xlsx', '.xls', '.xlsm', '.xlsb', '.ods', '.csv']
const COLUMNS = ['Name', 'Email', 'Contact Number', 'Company', 'Position', 'Openings']
const SAMPLE_ROW = ['Priya Sharma', 'priya.sharma@zoho.com', '+91 98765 43210', 'Zoho', 'Talent Acquisition Lead', '2']
const MAX_ERRORS_SHOWN = 20

// Saves a one-row CSV with the right headers, built in the browser
function downloadSample() {
    const csv = `${COLUMNS.join(',')}\n${SAMPLE_ROW.join(',')}\n`
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }))
    const link = document.createElement('a')
    link.href = url
    link.download = 'hr-contacts-sample.csv'
    link.click()
    URL.revokeObjectURL(url)        
}

// "Row 4: ..." or "Priya Sharma: ...". `error` is text, or a list of { msg } from the backend's checks
function describeError({row, name, error}) {
    const where = row ? `Row ${row}` : name || 'A contact'
    const what = Array.isArray(error) ? error.map((e) => e.msg).join('; ') : error
    return `${where}: ${what}`
}

/*
    Upload an Excel / CSV list of recruiters (admins only), then show what happened.
    Calls onImported(result) as soon as any contact was saved, and onClose() for Cancel / Done.
*/
export default function ImportContacts({ onImported, onClose }) {
    const [file, setFile] = useState(null)
    const [error, setError] = useState('')
    const [uploading, setUploading] = useState(false)
    const [result, setResult] = useState(null)
    
    function chooseFile(event) {
        const picked = event.target.files[0]
        event.target.value = '' // lets the same file be picked again after a fix
        if (!picked) return 
        const extension = picked.name.slice(picked.name.lastIndexOf('.')).toLowerCase()
        if (!EXTENSIONS.includes(extension)){
            setFile(null)
            setError(`${picked.name} isn’t an Excel or CSV file. Use ${EXTENSIONS.join(', ')}.`)
            return
        }
        setError('')
        setFile(picked)
    }

    async function handleUpload() {
        setError('')
        setUploading(true)
        try{
            const summary = await contactsApi.importFile(file)
            setResult(summary)
            if (summary.created_contacts + summary.existing_contacts > 0) onImported(summary)
        }catch(err){
            // Every row was rejected: the backend answers 400 with the same summary
            const detail = err.response?.data?.detail
            if (detail?.status === 'validation_failed') setResult(detail)
            else setError(getErrorMessage(err))
        }finally{
            setUploading(false)
        }
    }

    function startOver() {
        setFile(null)
        setResult(null)        
    }

    if (result){
        const imported = (result.created_contacts ?? 0) + (result.existing_contacts ?? 0)
        return (
            <>
                <div className="flex flex-col gap-4 px-5 py-4">
                    <Alert tone={imported ? 'success' : 'error'}>
                        {imported
                        ? `Imported ${imported === 1 ? '1 contact' : `${imported} contacts`} from ${result.file_name}.`
                        : `Nothing was imported from ${result.file_name}.`}
                    </Alert>
                    <dl className="grid grid-cols-2 gap-2 text-[13.5px] sm:grid-cols-3">
                        <Start label="New contacts" value={result.created_contacts} />
                        <Start label="Already saved" value={result.existing_contacts} />
                        <Start label="Emails added" value={result.emails_added} />
                        <Start label="Phones added" value={result.phones_added} />
                        <Start label="Rows skipped" value={result.errors.length} />
                    </dl>
                    {result.errors.length > 0 && (
                        <div>
                        <p className="mb-1.5 text-[13px] font-semibold">Skipped rows</p>
                        <ul className="max-h-48 overflow-y-auto rounded-lg border border-line text-[13px]">
                            {result.errors.slice(0, MAX_ERRORS_SHOWN).map((item, i) => (
                            <li key={i} className="border-b border-line px-3 py-2 last:border-b-0">
                                {describeError(item)}
                            </li>
                            ))}
                        </ul>
                        {result.errors.length > MAX_ERRORS_SHOWN && (
                            <p className="mt-1 text-xs text-muted">
                            And {result.errors.length - MAX_ERRORS_SHOWN} more. Fix these rows and upload the file again.
                            </p>
                        )}
                        </div>
                    )}
                    </div>
                    <div className="flex justify-end gap-2 border-t border-line px-5 py-4">
                    <Button type="button" variant="secondary" onClick={startOver}>
                        Import another file
                    </Button>
                    <Button type="button" onClick={onClose}>
                        Done
                    </Button>
                </div>
            </>
        )
    }

    return (
        <>
            <div className="flex flex-col gap-4 px-5 py-4">
                <Alert>{error}</Alert>

                <label className="flex cursor-pointer flex-col items-center gap-1 rounded-xl border-2 border-dashed border-line px-4 py-7 text-center hover:border-primary hover:bg-surface-2">
                <Icon name="upload" className="size-6 text-muted" />
                {file ? (
                    <>
                    <span className="font-semibold break-all">{file.name}</span>
                    <span className="text-[13px] text-muted">{Math.max(1, Math.round(file.size / 1024))} KB · click to choose another</span>
                    </>
                ) : (
                    <>
                    <span className="font-semibold">Choose an Excel or CSV file</span>
                    <span className="text-[13px] text-muted">{EXTENSIONS.join(' ')}</span>
                    </>
                )}
                <input type="file" accept={EXTENSIONS.join(',')} onChange={chooseFile} className="sr-only" />
                </label>

                <div className="rounded-lg bg-surface-2 px-3.5 py-3 text-[13px]">
                <p className="font-semibold">The first row must have these columns</p>
                <p className="mt-0.5 text-muted">{COLUMNS.join(' · ')}</p>
                <p className="mt-1.5 text-muted">
                    Extra emails or phones can go in more columns or the rows below a contact.{' '}
                    <button type="button" onClick={downloadSample} className="font-semibold text-link hover:underline">
                    Download a sample
                    </button>
                </p>
                </div>
            </div>
            <div className="flex justify-end gap-2 border-t border-line px-5 py-4">
                <Button type="button" variant="secondary" onClick={onClose}>
                Cancel
                </Button>
                <Button type="button" loading={uploading} disabled={!file} onClick={handleUpload}>
                Upload
                </Button>
            </div>
        </>
    )
}

function Start({ label, value}) {
    return (
        <div className="rounded-lg border border-line px-3 py-2">
            <dt className="text-[12px] text-muted">{label}</dt>
            <dd className="font-display text-[20px] font-bold tabular-nums">{value ?? 0}</dd>
        </div>
    )
}
import Icon from "./Icon";
import Select from "./Select";

export const PAGE_SIZES = [25,50,75,100]

/* 
    "Showing 26–50 of 120", a rows-per-page picker and Prev / Next buttons.
    `page` starts at 1. The parent keeps page and pageSize in its state.
*/

export default function Pagination({page, pageSize, total, onPageChange,onPageSizeChange }) {
    const pageCount = Math.max(1,Math.ceil(total/pageSize))
    const first = total === 0 ? 0 : (page - 1) * pageSize + 1
    const last = Math.min(page * pageSize, total)

    return(
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-4 py-3 text-[13px] text-muted sm:px-5">
            <span className="tabular-nums">
                Showing {first}–{last} of {total}
            </span>
            <div className="flex items-center gap-3">
                <label className="flex items-center gap-2">
                    <span className="hidden sm:inline">Rows per page</span>
                    <Select
                        value = {pageSize}
                        onChange = {(e)=> onPageSizeChange(Number(e.target.value))}
                        aria-label="Rows per page"    
                        className="py-1.5"
                    >
                        {PAGE_SIZES.map((size) => (
                            <option key={size} value={size}>
                                {size}
                            </option>
                        ))}  
                    </Select>
                </label>
                <div className="flex gap-1.5">
                    <PageButton label="Previous page" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
                        <Icon name="chevron" className="size-4 rotate-180" />
                    </PageButton>

                    <PageButton label="Next page" disabled={page >= pageCount} onClick={() => onPageChange(page+1)}>
                        <Icon name="chevron" className="size-4" />
                    </PageButton>
                </div>
            </div> 
        </div>
    )
    
}

function PageButton({label, children,...props}) {
    return(
        <button 
        {...props}
        aria-label={label}
        className="grid size-9 place-items-center rounded-lg border border-line bg-surface text-fg hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-40"
        >
            {children}
        </button>
    )
    
}
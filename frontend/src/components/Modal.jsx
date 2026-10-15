import { useEffect, useRef } from "react";
import Icon from "./Icon";

/*
    A popup over the page; on phones it slides up from the bottom as a sheet. 
    Built on the browser's <dialog>, which keeps keyboard focus inside and closes on Esc.
        <Modal open={isOpen} onClose={() => setOpen(false)} title="Add contact">...</Modal> 
*/
export default function Modal({open, onClose, title, description, children }){
    const dialogRef = useRef(null)

    // <dialog> is opened and closed through its own methods, not a prop 
    useEffect(() => {
        const dialog = dialogRef.current 
        if (open && !dialog.open) dialog.showModal()
        if (!open && dialog.open) dialog.close()
    }, [open])

    return (
        <dialog 
            ref={dialogRef}
            onClose={onClose}
            // A click on the dark backdrop lands on the <dialog> itself, not on the panel inside it
            onClick={(e) => e.target === e.currentTarget && onClose()}
            className="m-auto w-full max-w-lg rounded-2xl border border-line bg-surface p-0 text-fg backdrop:bg-black/50 max-sm:mb-0 max-sm:max-h-[92dvh] max-sm:max-w-none max-sm:rounded-b-none"
        >
            <div className="flex items-start justify-between gap-3 border-b border-line px-5 py-4">
                <div className="min-w-0">
                    <h3 className="font-display text-[17px] font-bold text-brand-ink">{title}</h3>
                    {description && <p className="mt-0.5 text-[13px] text-muted">{description}</p>}
                </div>
                <button
                    type="button"
                    onClick={onClose}
                    aria-label="Close"
                    className="grid size-8 shrink-0 place-items-center rounded-lg text-muted hover:bg-surface-2 hover:text-fg"      
                >
                    <Icon name="x"/>   
                </button>
            </div>
            {open && children}
        </dialog>
    )
}
// ColdReach mark : envelope with an outring arrow. Colours come from the 
//  --mark-* / --logo-* variables in index.css. so it adapts to dark mode.
export function LogoMark({className = 'size-8'}){
    return (
        <svg viewBox="0 0 32 32" aria-hidden="true" className={`shrink-0 ${className}`}>
        <rect className="fill-mark-bg" width="32" height="32" rx="8" />
        <rect className="fill-mark-fg" x="6" y="10.5" width="17" height="13" rx="2.2" />
        <path
            className="fill-none stroke-mark-bg"
            d="M7.2 11.8l7.3 5.4 7.3-5.4"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
        />
        <circle className="fill-logo-dot stroke-mark-bg" cx="23.6" cy="10" r="5.3" strokeWidth="1.8" />
        <path
            className="fill-none stroke-logo-arrow"
            d="M21.7 11.9l3.7-3.7M22.6 8.2h2.8V11"
            strokeWidth="1.7"
            strokeLinecap="round"
            strokeLinejoin="round"
        />
        </svg>

    )
}

// nameClassName lets the sidebar hide the word "ColdReach" in tablet (rail) mode
export default function Logo({nameClassName = ''}){
    return(
       <div className="flex items-center gap-2.5 font-display text-[17px] font-bold text-brand-ink">
        <LogoMark />
        <span className={nameClassName}>
            Cold<span className="text-primary">Reach</span>
        </span>
        </div> 
    )
}
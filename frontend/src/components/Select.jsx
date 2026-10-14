// A dropdown with the same look as Input. Takes every normal <select> prop; pass <option>s as children.
export default function Select({className='',...props}){
    return (
        <select
            {...props}
            className= {`rounded-lg border border-line bg-surface px-3 py-2.5 text-fg outline-none focus:border-primary focus:ring-3 focus:ring-primary-soft ${className}`}
        />
    )
}
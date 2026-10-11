import { useState } from "react";
import Input from "./Input";
// Password box wih a Show ? Hide button

function PasswordInput(props) {
    const [visible, setVisible] = useState(false)
  return (
    <div className="relative">
        <Input {...props} type={visible ? 'text': 'password'} className="pr-16"/>
        <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        className="absolute right-2 top-1/2 -translate-y-1/2 rounded px-1.5 py-1 text-[12.5px] font-semibold text-link"
        aria-label= {visible ? 'Hide password' : 'Show Password'}
        >
            {visible ? 'Hide': 'Show'}
        </button>
    </div>
  )
}

export default PasswordInput
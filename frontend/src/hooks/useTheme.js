import { useState } from "react";

// Reads the theme that index.html already put on <html>, flips it.
export default function useTheme(){
    const [theme, setTheme] = useState(() => document.documentElement.dataset.theme || 'light')

    function toggleTheme() {
        const next = theme === 'dark' ? 'light' : 'dark'
        document.documentElement.dataset.theme = next

        try{
            localStorage.setItem('theme', next)
        } catch{
            // storage blocked (private mode) - theme still works for this visit
        }
        setTheme(next)
    }

    return {theme, toggleTheme}
} 


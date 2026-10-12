import { useEffect, useState } from "react";
import { getErrorMessage } from "../api/client";

/*
    Loads data when the component appear and tracks the three states every screen 
    
        const stats = useApi(dashboardApi.stats)
        stats.loading -> true while waiting 
        stats.error -> a readable message, or ''
        stats.data -> the response body once it arrives 
        stats.reload() -> fetch again (for a "Try again" button)
    
*/

export default function useApi(load){
    const [state, setState] = useState({data:null, error:'', loading:true})
    const [attempt, setAttempt] = useState(0)

    useEffect(()=> {
        let cancelled = false 
        load()
        .then((data)=> {
            if(!cancelled) setState({data, error:'',loading:false})
        })
        .catch((err) => {
            if(!cancelled) setState({data:null, error:getErrorMessage(err), loading:false})
        })
    // Ignore an answer that arrives after the component has gone (or after reload)
    return () => {
        cancelled = true 
    }
    // Run again only when reload() is called; `load` is a fixed api function 
    // eslint-disable-next-line react-hooks/exhaustive-deps 
    }, [attempt])

    function reload(){
        setState((prev) => ({...prev, error:'', loading:true}))
        setAttempt((n)=> n+1)
    }
    return {...state,reload}
}

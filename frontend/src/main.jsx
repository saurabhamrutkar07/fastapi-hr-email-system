import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import './index.css'
import App from './App.jsx'
import { authApi } from './api/auth.js'
import { getErrorMessage } from './api/client.js'

if (import.meta.env.DEV) Object.assign(window, { authApi, getErrorMessage })

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)

import { Route, Routes } from 'react-router'
import { RequireAdmin, RequireAuth, RequireGuest } from './auth/guards'
import AppLayout from './layouts/AppLayouts'
import AuthLayout from './layouts/AuthLayout'
import ComingSoon from './pages/ComingSoon'
import LoginPage from './pages/auth/LoginPage'
import SignupPage from './pages/auth/SignupPage'
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage'
import OAuthSuccessPage from './pages/auth/OAuthSuccessPage'
import DashboardPage from './pages/DashboardPage'
import ContactsPage from './pages/ContactsPage'
import SettingsPage from './pages/SettingsPage'
import TemplatesPage from './pages/TemplatesPage'
import TemplateEditorPage from './pages/TemplateEditorPage'
import ResumesPage from './pages/ResumesPage'
import SendPage from './pages/SendPage'

export default function App() {
  return (
    <Routes>
      {/* Sign in / sign up pages: only for signed-out users. Navy panel + form, no sidebar */}
      <Route element={<RequireGuest />}>
        <Route element={<AuthLayout />}>
          <Route path="login" element={<LoginPage />} />
          <Route path="signup" element={<SignupPage />} />
          <Route path="forgot-password" element={<ForgotPasswordPage />} />
          <Route path='oauth-success' element={<OAuthSuccessPage/>}/>

        </Route>
      </Route>

      {/* Everything else needs a signed-in user and gets the sidebar / top bar / bottom nav */}
      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="contacts" element={<ContactsPage />} />
          <Route path="send" element={<SendPage />} />
          <Route path="history" element={<ComingSoon title="History" description="Every send attempt and the mail server's reply." />} />
          <Route path="templates" element={<TemplatesPage />} />
          <Route path="templates/new" element={<TemplateEditorPage />} />
          <Route path="templates/:id" element={<TemplateEditorPage />} />
          <Route path="resumes" element={<ResumesPage />} />
          <Route path="settings" element={<SettingsPage />} />

          <Route element={<RequireAdmin />}>
            <Route path="admin/users" element={<ComingSoon title="Users" description="Manage roles and who can sign in." />} />
          </Route>

          <Route path="*" element={<ComingSoon title="Page not found" description="Check the address or pick a page from the menu." />} />
        </Route>
      </Route>
    </Routes>
  )
}

import { Route, Routes } from 'react-router'
import AppLayout from './layouts/AppLayouts'
import ComingSoon from './pages/ComingSoon'

export default function App() {
  return (
    <Routes>
      {/* Every page inside this Route gets the sidebar / top bar / bottom nav */}
      <Route element={<AppLayout />}>
        <Route index element={<ComingSoon title="Dashboard" description="Your outreach over the last 14 days." />} />
        <Route path="contacts" element={<ComingSoon title="HR Contacts" description="Recruiters you can email." />} />
        <Route path="send" element={<ComingSoon title="Send Email" description="Send a cold email with your resume attached." />} />
        <Route path="history" element={<ComingSoon title="History" description="Every send attempt and the mail server's reply." />} />
        <Route path="templates" element={<ComingSoon title="Templates" description="Write once. Variables are filled in for each recruiter." />} />
        <Route path="resumes" element={<ComingSoon title="Resumes" description="The active version is attached to every email." />} />
        <Route path="settings" element={<ComingSoon title="Settings" description="Your profile and the email account you send from." />} />
        <Route path="admin/users" element={<ComingSoon title="Users" description="Manage roles and who can sign in." />} />
        <Route path="*" element={<ComingSoon title="Page not found" description="Check the address or pick a page from the menu." />} />
      </Route>
    </Routes>
  )
}

import GmailSection from '../components/settings/GmailSection'
import PasswordSection from '../components/settings/PasswordSection'
import ProfileSection from '../components/settings/ProfileSection'

export default function SettingsPage() {
  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <div>
        <h2 className="font-display text-[22px] font-bold text-brand-ink sm:text-[26px]">Settings</h2>
        <p className="mt-0.5 text-muted">Your profile, the Gmail you send from and your password.</p>
      </div>

      <GmailSection />
      <ProfileSection />
      <PasswordSection />
    </div>
  )
}

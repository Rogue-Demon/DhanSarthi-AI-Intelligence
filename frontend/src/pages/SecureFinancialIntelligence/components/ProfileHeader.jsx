/**
 * ProfileHeader — Read-only user identity display with security badges.
 */
export default function ProfileHeader({ profile }) {
  const initials = profile.name
    ? profile.name
        .split(' ')
        .map((w) => w[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : '??'

  return (
    <header className="secure-fi-header">
      <div className="secure-fi-header__left">
        <div className="secure-fi-header__avatar">{initials}</div>
        <div>
          <div className="secure-fi-header__name">{profile.name}</div>
          <div className="secure-fi-header__meta">
            {profile.email} · {profile.persona} · {profile.country}
          </div>
        </div>
      </div>
      <div className="secure-fi-header__badges">
        <span className="secure-fi-badge secure-fi-badge--readonly">🔒 Read-Only</span>
        <span className="secure-fi-badge secure-fi-badge--shield">🛡️ Secure View</span>
      </div>
    </header>
  )
}

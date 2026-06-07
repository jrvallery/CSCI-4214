const baseNavItems = [
  { id: 'home', label: 'Home' },
  { id: 'form', label: 'Assessment' },
  { id: 'findShop', label: 'Find a Shop' },
];

export default function Header({ currentPage, onNavigate, currentUser, onLogout }) {
  const navItems = currentUser
    ? [...baseNavItems, { id: 'history', label: 'History' }]
    : baseNavItems;

  return (
    <header className="header">
      <div className="header-content">
        <button
          type="button"
          className="brand"
          onClick={() => onNavigate('home')}
          aria-label="SkiWare home"
        >
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 20 L12 4 L21 20 Z" />
              <path d="M8.5 13 L12 7 L15.5 13" />
            </svg>
          </span>
          SkiWare
        </button>

        <nav className="header-nav" aria-label="Primary">
          {navItems.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`nav-link ${currentPage === item.id ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="header-actions">
          {currentUser ? (
            <>
              <button
                type="button"
                className="btn-ghost"
                onClick={() => onNavigate('user')}
              >
                {currentUser.name.split(' ')[0]}
              </button>
              <button type="button" className="btn-primary" onClick={onLogout}>
                Sign Out
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                className="btn-ghost"
                onClick={() => onNavigate('signIn')}
              >
                Sign In
              </button>
              <button
                type="button"
                className="btn-primary"
                onClick={() => onNavigate('createAccount')}
              >
                Create Account
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

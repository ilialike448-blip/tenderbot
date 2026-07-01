type Tab = 'home' | 'team' | 'analytics';

interface Props {
  active: Tab;
  onChange: (t: Tab) => void;
}

export default function BottomNav({ active, onChange }: Props) {
  return (
    <div className="bottom-nav">
      <button className={`nav-item${active === 'home' ? ' active' : ''}`} onClick={() => onChange('home')}>
        <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" /></svg>
        <span className="nav-label">Главная</span>
      </button>
      <button className={`nav-item${active === 'team' ? ' active' : ''}`} onClick={() => onChange('team')}>
        <svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>
        <span className="nav-label">Команда</span>
      </button>
      <button className={`nav-item${active === 'analytics' ? ' active' : ''}`} onClick={() => onChange('analytics')}>
        <svg viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" /><line x1="6" y1="20" x2="6" y2="14" /></svg>
        <span className="nav-label">Аналитика</span>
      </button>
    </div>
  );
}

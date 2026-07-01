import { User } from '../api/types';

interface Props {
  user: User;
  unreadCount: number;
  onNotifClick: () => void;
  onAdminClick?: () => void;
}

const ROLE_LABELS: Record<string, string> = {
  admin: 'Руководитель тендерного отдела',
  lead: 'Старший менеджер',
  member: 'Менеджер',
};

export default function Header({ user, unreadCount, onNotifClick, onAdminClick }: Props) {
  const label = user.position || ROLE_LABELS[user.role] || 'Сотрудник';

  return (
    <div className="header">
      <div className="header-top">
        <div className="av av-lg header-avatar" style={{ background: `linear-gradient(135deg, ${user.color}99, ${user.color})` }}>
          {user.initials}
        </div>
        <div className="header-info">
          <div className="header-name truncate">
            {user.first_name}{user.last_name ? ` ${user.last_name}` : ''}
          </div>
          <div className="header-role truncate">{label}</div>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {onAdminClick && (
            <button className="notif-btn" onClick={onAdminClick} title="Управление">
              <span style={{ fontSize: 14 }}>⚙️</span>
            </button>
          )}
          <button className="notif-btn" onClick={onNotifClick}>
            <span style={{ fontSize: 15 }}>🔔</span>
            {unreadCount > 0 && <div className="notif-dot" />}
          </button>
        </div>
      </div>
    </div>
  );
}

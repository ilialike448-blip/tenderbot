import { retrieveLaunchParams, miniApp, viewport } from '@telegram-apps/sdk-react';
import { useEffect, useState } from 'react';
import { api, setInitData } from './api/client';
import { User } from './api/types';
import Header from './components/Header';
import BottomNav from './components/BottomNav';
import TopTabs from './components/TopTabs';
import PendingScreen from './screens/PendingScreen';
import Dashboard from './screens/Dashboard';
import Tasks from './screens/Tasks';
import AIAuto from './screens/AIAuto';
import Team from './screens/Team';
import Analytics from './screens/Analytics';
import AdminPanel from './screens/AdminPanel';

type BottomTab = 'home' | 'team' | 'analytics';
type TopTab = 'dashboard' | 'tasks' | 'ai';

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [bottomTab, setBottomTab] = useState<BottomTab>('home');
  const [topTab, setTopTab] = useState<TopTab>('dashboard');
  const [showAdmin, setShowAdmin] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    // Expand to full screen
    try {
      const lp = retrieveLaunchParams();
      setInitData(lp.initDataRaw ?? '');
      miniApp.ready();
      viewport.expand();
    } catch {
      // Outside Telegram (dev mode) — use empty initData
      setInitData('');
    }
    loadUser();
  }, []);

  useEffect(() => {
    if (user?.status === 'approved') {
      loadUnread();
      const t = setInterval(loadUnread, 30_000);
      return () => clearInterval(t);
    }
  }, [user?.status]);

  async function loadUser() {
    try {
      const me = await api.me();
      setUser(me);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  }

  async function loadUnread() {
    try {
      const { count } = await api.notifications.unreadCount();
      setUnreadCount(count);
    } catch {}
  }

  if (loading) {
    return (
      <div className="app">
        <div className="state-center">
          <div className="skeleton" style={{ width: 48, height: 48, borderRadius: '50%' }} />
          <div className="skeleton" style={{ width: 140, height: 16, marginTop: 12 }} />
        </div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="app">
        <div className="state-center">
          <div className="state-icon">⚠️</div>
          <div className="state-title">Ошибка</div>
          <div className="state-text">{error || 'Отправь /start боту и открой приложение снова.'}</div>
          <button className="btn btn-primary" onClick={loadUser} style={{ marginTop: 16 }}>
            Повторить
          </button>
        </div>
      </div>
    );
  }

  // Pending / Rejected / Blocked gate
  if (user.status !== 'approved') {
    return (
      <div className="app">
        <PendingScreen status={user.status} />
      </div>
    );
  }

  // Admin panel overlay
  if (showAdmin) {
    return (
      <div className="app">
        <Header user={user} unreadCount={unreadCount} onNotifClick={() => {}} />
        <AdminPanel onBack={() => setShowAdmin(false)} />
      </div>
    );
  }

  const renderContent = () => {
    if (bottomTab === 'team') return <Team user={user} />;
    if (bottomTab === 'analytics') return <Analytics />;

    // bottomTab === 'home'
    if (topTab === 'tasks') return <Tasks user={user} />;
    if (topTab === 'ai') return <AIAuto user={user} />;
    return <Dashboard user={user} />;
  };

  return (
    <div className="app">
      <Header
        user={user}
        unreadCount={unreadCount}
        onNotifClick={() => {}}
        onAdminClick={user.role === 'admin' ? () => setShowAdmin(true) : undefined}
      />

      {bottomTab === 'home' && (
        <TopTabs
          active={topTab}
          onChange={setTopTab}
        />
      )}

      <div className="screen-content">
        {renderContent()}
      </div>

      <BottomNav active={bottomTab} onChange={setBottomTab} />
    </div>
  );
}

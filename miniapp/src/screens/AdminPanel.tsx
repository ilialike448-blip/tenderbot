import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { User } from '../api/types';

const STATUS_LABEL: Record<string, string> = {
  pending: 'Ожидает', approved: 'Одобрен', rejected: 'Отклонён', blocked: 'Заблокирован',
};
const ROLE_LABEL: Record<string, string> = {
  admin: 'Руководитель', lead: 'Старший', member: 'Менеджер',
};

type Tab = 'pending' | 'all';

interface Props { onBack: () => void; }

export default function AdminPanel({ onBack }: Props) {
  const [tab, setTab] = useState<Tab>('pending');
  const [pending, setPending] = useState<User[]>([]);
  const [all, setAll] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState<number | null>(null);

  useEffect(() => { load(); }, []);

  async function load() {
    setLoading(true);
    try {
      const [p, a] = await Promise.all([api.admin.pending(), api.admin.users()]);
      setPending(p);
      setAll(a);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Ошибка загрузки');
    } finally { setLoading(false); }
  }

  async function approve(id: number) {
    setActing(id);
    try { await api.admin.approve(id); await load(); }
    catch (e: unknown) { alert(e instanceof Error ? e.message : 'Ошибка'); }
    finally { setActing(null); }
  }

  async function reject(id: number) {
    setActing(id);
    try { await api.admin.reject(id); await load(); }
    catch (e: unknown) { alert(e instanceof Error ? e.message : 'Ошибка'); }
    finally { setActing(null); }
  }

  async function block(id: number) {
    if (!confirm('Заблокировать пользователя?')) return;
    setActing(id);
    try { await api.admin.block(id); await load(); }
    catch (e: unknown) { alert(e instanceof Error ? e.message : 'Ошибка'); }
    finally { setActing(null); }
  }

  async function changeRole(id: number, current: string) {
    const roles = ['member', 'lead', 'admin'].filter(r => r !== current);
    const next = roles[0];
    if (!confirm(`Сменить роль на «${ROLE_LABEL[next]}»?`)) return;
    setActing(id);
    try { await api.admin.setRole(id, next); await load(); }
    catch (e: unknown) { alert(e instanceof Error ? e.message : 'Ошибка'); }
    finally { setActing(null); }
  }

  const list = tab === 'pending' ? pending : all;

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <button className="btn btn-ghost" onClick={onBack} style={{ padding: '6px 12px', fontSize: 13 }}>
          ← Закрыть
        </button>
        <span style={{ fontWeight: 600, fontSize: 15 }}>⚙️ Управление доступом</span>
      </div>

      <div className="filter-row" style={{ marginBottom: 12 }}>
        <button
          className={`filter-chip${tab === 'pending' ? ' active-blue' : ''}`}
          onClick={() => setTab('pending')}
        >
          Заявки {pending.length > 0 && `(${pending.length})`}
        </button>
        <button
          className={`filter-chip${tab === 'all' ? ' active-blue' : ''}`}
          onClick={() => setTab('all')}
        >
          Все пользователи
        </button>
      </div>

      {loading && (
        <>
          {[0,1,2].map(i => (
            <div key={i} className="skeleton" style={{ height: 80, borderRadius: 12, marginBottom: 8 }} />
          ))}
        </>
      )}

      {!loading && list.length === 0 && (
        <div className="state-center" style={{ padding: '32px 0' }}>
          <div className="state-icon">{tab === 'pending' ? '📭' : '👥'}</div>
          <div className="state-title">
            {tab === 'pending' ? 'Нет заявок' : 'Нет пользователей'}
          </div>
        </div>
      )}

      {list.map(u => (
        <div key={u.telegram_id} className="card" style={{ marginBottom: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <div className="av av-sm" style={{ background: `${u.color}33`, color: u.color }}>
              {u.initials}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 600, fontSize: 13 }} className="truncate">
                {u.first_name} {u.last_name || ''}
              </div>
              <div style={{ fontSize: 10, color: 'var(--text2)' }}>
                {u.username ? `@${u.username} · ` : ''}{u.telegram_id}
              </div>
            </div>
            <div style={{ textAlign: 'right', flexShrink: 0 }}>
              <div style={{ fontSize: 10, color: 'var(--text2)' }}>{ROLE_LABEL[u.role]}</div>
              <div style={{
                fontSize: 10, fontWeight: 600,
                color: u.status === 'approved' ? 'var(--green)' :
                  u.status === 'pending' ? 'var(--orange)' : 'var(--red)'
              }}>
                {STATUS_LABEL[u.status]}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {u.status === 'pending' && (
              <>
                <button
                  className="btn btn-green"
                  style={{ fontSize: 11, padding: '5px 12px', minHeight: 0 }}
                  disabled={acting === u.telegram_id}
                  onClick={() => approve(u.telegram_id)}
                >
                  ✅ Одобрить
                </button>
                <button
                  className="btn btn-danger"
                  style={{ fontSize: 11, padding: '5px 12px', minHeight: 0 }}
                  disabled={acting === u.telegram_id}
                  onClick={() => reject(u.telegram_id)}
                >
                  ❌ Отклонить
                </button>
              </>
            )}
            {u.status === 'approved' && (
              <>
                <button
                  className="btn btn-ghost"
                  style={{ fontSize: 11, padding: '5px 12px', minHeight: 0 }}
                  disabled={acting === u.telegram_id}
                  onClick={() => changeRole(u.telegram_id, u.role)}
                >
                  Сменить роль
                </button>
                <button
                  className="btn btn-danger"
                  style={{ fontSize: 11, padding: '5px 12px', minHeight: 0 }}
                  disabled={acting === u.telegram_id}
                  onClick={() => block(u.telegram_id)}
                >
                  Блок
                </button>
              </>
            )}
            {(u.status === 'rejected' || u.status === 'blocked') && (
              <button
                className="btn btn-green"
                style={{ fontSize: 11, padding: '5px 12px', minHeight: 0 }}
                disabled={acting === u.telegram_id}
                onClick={() => approve(u.telegram_id)}
              >
                Восстановить
              </button>
            )}
          </div>
        </div>
      ))}
    </>
  );
}

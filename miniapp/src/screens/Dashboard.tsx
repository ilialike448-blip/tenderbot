import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { DashboardData, TeamMember, User } from '../api/types';

const STATUS_BADGE: Record<string, string> = {
  new: 'badge-new', in_work: 'badge-wip', review: 'badge-review', done: 'badge-done',
};
const STATUS_LABEL: Record<string, string> = {
  new: 'Новая', in_work: 'В работе', review: 'Проверка', done: 'Готово',
};

interface Props { user: User; }

export default function Dashboard({ user }: Props) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => { load(); }, []);

  async function load() {
    setLoading(true); setError('');
    try { setData(await api.dashboard()); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : 'Ошибка'); }
    finally { setLoading(false); }
  }

  if (loading) return <DashboardSkeleton />;
  if (error) return (
    <div className="state-center">
      <div className="state-icon">⚠️</div>
      <div className="state-title">Ошибка загрузки</div>
      <div className="state-text">{error}</div>
      <button className="btn btn-primary" onClick={load} style={{ marginTop: 16 }}>Повторить</button>
    </div>
  );
  if (!data) return null;

  const { summary, team, processes, tenders_in_work } = data;

  return (
    <>
      {/* Summary */}
      <div className="summary-row">
        <div className="sum-box sum-green"><div className="sum-num">{summary.done}</div><div className="sum-label">Выполнено</div></div>
        <div className="sum-box sum-blue"><div className="sum-num">{summary.in_work}</div><div className="sum-label">В работе</div></div>
        <div className="sum-box sum-orange"><div className="sum-num">{summary.new}</div><div className="sum-label">Новые</div></div>
      </div>

      {/* Team */}
      <div className="section-row">
        <span className="section-title">Команда · неделя</span>
        {['admin', 'lead'].includes(user.role) && (
          <button className="section-action">+ добавить</button>
        )}
      </div>

      {team.length === 0 ? (
        <div className="state-center" style={{ padding: '24px 0' }}>
          <div className="state-text">Сотрудники не добавлены</div>
        </div>
      ) : (
        team.map(m => <EmpCard key={m.telegram_id} member={m} />)
      )}

      {/* Two-col: Processes + In Work */}
      <div className="two-col" style={{ marginTop: 12 }}>
        <div>
          <div className="section-title" style={{ marginBottom: 6 }}>Процессы</div>
          {processes.length === 0 && <div className="state-text" style={{ fontSize: 12 }}>Нет активных</div>}
          {processes.map(p => (
            <div key={p.id} className="card" style={{ padding: '7px 8px', marginBottom: 5 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text)' }} className="truncate">{p.title}</div>
              <div style={{ fontSize: 10, color: 'var(--text2)', marginTop: 2 }}>
                {p.first_name ? `${p.first_name} · ` : ''}{p.due_date ? relDate(p.due_date) : '—'}
              </div>
              <span className={`badge ${STATUS_BADGE[p.status] || 'badge-new'}`} style={{ marginTop: 4, fontSize: 9 }}>
                {STATUS_LABEL[p.status] || p.status}
              </span>
            </div>
          ))}
        </div>

        <div>
          <div className="section-title" style={{ marginBottom: 6 }}>В работе</div>
          {tenders_in_work.length === 0 && <div className="state-text" style={{ fontSize: 12 }}>Нет тендеров</div>}
          {tenders_in_work.map(t => (
            <div key={t.external_number} className="card" style={{ padding: '7px 8px', marginBottom: 5, borderLeft: '2px solid var(--blue)' }}>
              <div style={{ fontSize: 9, color: 'var(--blue)', fontWeight: 600 }}>
                №{t.external_number?.slice(0, 10)}…
              </div>
              <div style={{ fontSize: 10, color: 'var(--text)', fontWeight: 500, marginTop: 2 }} className="truncate">
                {t.name}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 2 }}>
                <span style={{ fontSize: 9, color: 'var(--text2)' }}>
                  {t.taken_by_name ? t.taken_by_name.split(' ')[0] : '—'}
                </span>
                <span style={{ fontSize: 9, color: 'var(--green)', fontWeight: 600 }}>
                  {t.nmc ? `${(t.nmc / 1_000_000).toFixed(1)} млн` : '—'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

function EmpCard({ member: m }: { member: TeamMember }) {
  return (
    <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
      <div className={`sdot ${m.is_active ? 'sdot-green' : m.in_work > 0 ? 'sdot-orange' : 'sdot-gray'}`} />
      <div className="av av-md" style={{ background: `${m.color}33`, color: m.color }}>
        {m.initials}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)' }} className="truncate">
          {m.first_name} {m.last_name || ''}
        </div>
        <div style={{ fontSize: 10, color: 'var(--text2)' }}>{m.position || m.role}</div>
        {m.active_tender_num && (
          <div style={{ fontSize: 9, color: 'var(--text2)', marginTop: 2 }} className="truncate">
            <span style={{ color: m.color }}>№{m.active_tender_num.slice(0, 8)}…</span>
            {' · '}{m.active_tender_name?.slice(0, 20)}
          </div>
        )}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4, flexShrink: 0 }}>
        <div style={{ display: 'flex', gap: 3 }}>
          <span className="pill pill-g">{m.done}✓</span>
          <span className="pill pill-b">{m.in_work}▶</span>
          <span className="pill pill-o">{m.new_count}→</span>
        </div>
        <button className="btn btn-ghost" style={{ padding: '2px 8px', fontSize: 10, minHeight: 0 }}>
          детали ›
        </button>
      </div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <>
      <div className="summary-row">
        {[0,1,2].map(i => <div key={i} className="skeleton" style={{ height: 60, borderRadius: 10 }} />)}
      </div>
      {[0,1,2].map(i => (
        <div key={i} className="skeleton" style={{ height: 72, borderRadius: 12, marginBottom: 8 }} />
      ))}
    </>
  );
}

function relDate(iso: string): string {
  try {
    const d = new Date(iso);
    const today = new Date();
    const diff = Math.round((d.getTime() - today.getTime()) / 86400000);
    if (diff === 0) return 'сегодня';
    if (diff === 1) return 'завтра';
    if (diff === -1) return 'вчера';
    return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
  } catch { return iso; }
}

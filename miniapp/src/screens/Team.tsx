import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { TeamMember, User } from '../api/types';

const CROWNS = ['🏆', '🥈', '🥉'];
const CROWN_COLORS = ['val-gold', 'val-silver', 'val-bronze'];
const CROWN_CSS: Record<string, string> = {
  'val-gold': 'var(--orange)', 'val-silver': 'var(--blue)', 'val-bronze': 'var(--purple)',
};

interface Props { user: User; }

export default function Team({ user }: Props) {
  const [data, setData] = useState<{ members: TeamMember[]; top3: TeamMember[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<TeamMember | null>(null);
  const [period, _setPeriod] = useState('week');

  useEffect(() => { load(); }, []);

  async function load() {
    setLoading(true); setError('');
    try { setData(await api.team(period)); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : 'Ошибка'); }
    finally { setLoading(false); }
  }

  if (selected) {
    return (
      <EmployeeDetail
        member={selected}
        user={user}
        onBack={() => setSelected(null)}
      />
    );
  }

  if (loading) return <TeamSkeleton />;
  if (error) return (
    <div className="state-center">
      <div className="state-icon">⚠️</div>
      <div className="state-text">{error}</div>
      <button className="btn btn-primary" onClick={load} style={{ marginTop: 12 }}>Повторить</button>
    </div>
  );
  if (!data) return null;

  const { members, top3 } = data;

  return (
    <>
      <div className="section-title" style={{ marginBottom: 8 }}>Топ недели</div>

      {top3.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', color: 'var(--text2)', fontSize: 13 }}>
          Нет данных
        </div>
      ) : (
        <div className="top3">
          {/* Place silver first (left), gold second (center), bronze third (right) — matching mockup */}
          {[top3[1], top3[0], top3[2]].map((m, i) => {
            if (!m) return <div key={i} />;
            const rank = m === top3[0] ? 0 : m === top3[1] ? 1 : 2;
            const colorKey = CROWN_COLORS[rank];
            return (
              <div
                key={m.telegram_id}
                className={`top-card${rank === 0 ? ' gold' : ''}`}
                onClick={() => setSelected(m)}
                style={{ cursor: 'pointer' }}
              >
                <div style={{ fontSize: 18 }}>{CROWNS[rank]}</div>
                <div className="av av-sm" style={{ margin: '5px auto', background: `${m.color}33`, color: m.color }}>
                  {m.initials}
                </div>
                <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text)' }}>{m.first_name}</div>
                <div style={{ fontSize: 17, fontWeight: 700, margin: '3px 0', color: CROWN_CSS[colorKey] }}>
                  {m.tenders_count}
                </div>
                <div style={{ fontSize: 9, color: 'var(--text2)' }}>тендеров</div>
              </div>
            );
          })}
        </div>
      )}

      <div className="section-title" style={{ marginBottom: 8 }}>Все сотрудники</div>

      {members.length === 0 && (
        <div className="state-center" style={{ padding: '24px 0' }}>
          <div className="state-text">Нет одобренных сотрудников</div>
        </div>
      )}

      {members.map(m => (
        <div
          key={m.telegram_id}
          className="card"
          style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', marginBottom: 6 }}
          onClick={() => setSelected(m)}
        >
          <div className={`sdot ${m.is_active ? 'sdot-green' : m.in_work > 0 ? 'sdot-orange' : 'sdot-gray'}`} />
          <div className="av av-sm" style={{ background: `${m.color}33`, color: m.color }}>{m.initials}</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)' }} className="truncate">
              {m.first_name} {m.last_name || ''}
            </div>
            <div style={{ fontSize: 10, color: 'var(--text2)' }}>{m.position || m.role}</div>
            <div style={{ display: 'flex', gap: 3, marginTop: 3 }}>
              <span className="pill pill-g">{m.done}✓</span>
              <span className="pill pill-b">{m.in_work}▶</span>
              <span className="pill pill-o">{m.new_count}→</span>
            </div>
          </div>
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--green)' }}>
              {m.tenders_count}
            </div>
            <div style={{ fontSize: 9, color: 'var(--text2)' }}>тендеров</div>
          </div>
        </div>
      ))}
    </>
  );
}

function EmployeeDetail({ member: m, user, onBack }: { member: TeamMember; user: User; onBack: () => void }) {
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <button className="btn btn-ghost" onClick={onBack} style={{ padding: '6px 12px', fontSize: 13 }}>
          ← Назад
        </button>
        <span style={{ fontWeight: 600, fontSize: 15, flex: 1 }} className="truncate">
          {m.first_name} {m.last_name || ''}
        </span>
      </div>

      <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        <div className="av" style={{ width: 52, height: 52, fontSize: 18, background: `${m.color}33`, color: m.color }}>
          {m.initials}
        </div>
        <div>
          <div style={{ fontWeight: 600, fontSize: 15 }}>{m.first_name} {m.last_name || ''}</div>
          <div style={{ fontSize: 12, color: 'var(--text2)', marginTop: 2 }}>{m.position || m.role}</div>
          <div style={{ display: 'flex', gap: 4, marginTop: 6 }}>
            <span className="pill pill-g">{m.done}✓</span>
            <span className="pill pill-b">{m.in_work}▶</span>
            <span className="pill pill-o">{m.new_count}→</span>
            <span className="pill" style={{ background: 'var(--bg-green)', color: 'var(--green)' }}>
              {m.tenders_count} тендеров
            </span>
          </div>
        </div>
      </div>

      {m.active_tender_num && (
        <div className="card" style={{ borderLeft: '2px solid var(--blue)', marginBottom: 12 }}>
          <div style={{ fontSize: 10, color: 'var(--text2)' }}>Активный тендер</div>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--blue)', marginTop: 3 }}>
            №{m.active_tender_num}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text)', marginTop: 2 }}>{m.active_tender_name}</div>
        </div>
      )}

      {user.role !== 'member' && (
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost" style={{ flex: 1, fontSize: 12 }}>
            Изменить роль
          </button>
          <button className="btn btn-danger" style={{ fontSize: 12 }}>
            Деактивировать
          </button>
        </div>
      )}
    </>
  );
}

function TeamSkeleton() {
  return (
    <>
      <div className="top3" style={{ marginBottom: 14 }}>
        {[0,1,2].map(i => <div key={i} className="skeleton" style={{ height: 110, borderRadius: 12 }} />)}
      </div>
      {[0,1,2,4].map(i => (
        <div key={i} className="skeleton" style={{ height: 70, borderRadius: 12, marginBottom: 6 }} />
      ))}
    </>
  );
}

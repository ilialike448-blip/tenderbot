import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { AnalyticsData } from '../api/types';

type Period = 'week' | 'month' | 'quarter';

const PERIODS: { key: Period; label: string }[] = [
  { key: 'week', label: 'Неделя' },
  { key: 'month', label: 'Месяц' },
  { key: 'quarter', label: 'Квартал' },
];

const RATING_EMOJI: Record<string, string> = { fire: '🔥', ok: '✅', warn: '⚠️' };

function fmt(n: number | null | undefined): string {
  if (n == null) return '—';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} млн`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)} тыс`;
  return String(Math.round(n));
}

export default function Analytics() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [period, setPeriod] = useState<Period>('week');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => { load(period); }, [period]);

  async function load(p: Period) {
    setLoading(true); setError('');
    try { setData(await api.analytics(p)); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : 'Ошибка'); }
    finally { setLoading(false); }
  }

  return (
    <>
      <div className="filter-row" style={{ marginBottom: 12 }}>
        {PERIODS.map(p => (
          <button
            key={p.key}
            className={`filter-chip${period === p.key ? ' active-blue' : ''}`}
            onClick={() => setPeriod(p.key)}
          >
            {p.label}
          </button>
        ))}
      </div>

      {loading && <AnalyticsSkeleton />}
      {error && (
        <div className="state-center">
          <div className="state-icon">⚠️</div>
          <div className="state-text">{error}</div>
          <button className="btn btn-primary" onClick={() => load(period)} style={{ marginTop: 12 }}>
            Повторить
          </button>
        </div>
      )}

      {!loading && !error && data && (
        <>
          <div className="stat-grid">
            <div className="stat-card">
              <div className="stat-lbl">Тендеров взято</div>
              <div className="stat-val" style={{ color: 'var(--text)' }}>{data.summary.tenders_taken}</div>
              <div className="stat-sub">из {data.summary.ai_found} найденных AI</div>
            </div>
            <div className="stat-card">
              <div className="stat-lbl">Сумма договоров</div>
              <div className="stat-val text-green">{fmt(data.summary.total_sum)}</div>
              <div className="stat-sub">₽ всего</div>
            </div>
            <div className="stat-card">
              <div className="stat-lbl">Себестоимость AI</div>
              <div className="stat-val text-blue">{fmt(data.summary.total_cost)}</div>
              <div className="stat-sub">₽ расчёт Claude</div>
            </div>
            <div className="stat-card">
              <div className="stat-lbl">Прибыль прогноз</div>
              <div className="stat-val text-orange">{fmt(data.summary.profit_forecast)}</div>
              <div className="stat-sub">
                {data.summary.margin_pct != null ? `~${data.summary.margin_pct}% маржа` : '₽'}
              </div>
            </div>
          </div>

          <div className="section-title" style={{ marginBottom: 8 }}>По тендерам</div>

          {data.per_tender.length === 0 && (
            <div className="state-center" style={{ padding: '24px 0' }}>
              <div className="state-icon">📊</div>
              <div className="state-title">Нет данных</div>
              <div className="state-text">Возьмите тендеры в работу через раздел AI авто.</div>
            </div>
          )}

          {data.per_tender.map(t => (
            <div key={t.external_number} className="card" style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 600 }} className="truncate">{t.name}</div>
                  <div style={{ fontSize: 10, color: 'var(--text3)', marginTop: 2 }}>
                    №{t.external_number?.slice(0, 12)}… · {t.assignee_name || '—'}
                  </div>
                </div>
                <span style={{ fontSize: 16, marginLeft: 8, flexShrink: 0 }}>
                  {RATING_EMOJI[t.rating || 'ok'] || '❓'}
                </span>
              </div>

              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                <span className="pill tp-sum">{fmt(t.nmc)} ₽</span>
                <span className="pill" style={{ background: '#1a1a3a', color: 'var(--blue)' }}>
                  с/с {fmt(t.cost_estimate)}
                </span>
                {t.profit != null && (
                  <span className="pill" style={{ background: 'var(--bg-orange)', color: 'var(--orange)' }}>
                    +{fmt(t.profit)}
                  </span>
                )}
                {t.margin_percent != null && (
                  <span className="pill" style={{ background: 'var(--bg-green)', color: 'var(--green)' }}>
                    {Math.round(t.margin_percent)}%
                  </span>
                )}
              </div>

              {t.analyzed_at && (
                <div style={{ fontSize: 10, color: 'var(--green)', marginTop: 6 }}>
                  ⚡ Прогноз Claude · обновлён {fmtDate(t.analyzed_at)}
                </div>
              )}
            </div>
          ))}
        </>
      )}
    </>
  );
}

function AnalyticsSkeleton() {
  return (
    <>
      <div className="stat-grid">
        {[0,1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 80, borderRadius: 12 }} />)}
      </div>
      {[0,1,2].map(i => (
        <div key={i} className="skeleton" style={{ height: 90, borderRadius: 12, marginBottom: 8 }} />
      ))}
    </>
  );
}

function fmtDate(iso: string): string {
  try { return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }); }
  catch { return iso; }
}

import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Tender, User } from '../api/types';

type Filter = 'all' | 'hot' | 'ok' | 'risk';

const FILTERS: { key: Filter; label: string }[] = [
  { key: 'all', label: 'Все' },
  { key: 'hot', label: '🔥 Топ' },
  { key: 'ok', label: '✅ Подходят' },
  { key: 'risk', label: '⚠️ Риски' },
];

const RATING_EMOJI: Record<string, string> = {
  fire: '🔥', ok: '✅', warn: '⚠️',
};

interface Props { user: User; }

export default function AIAuto({ user }: Props) {
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [filter, setFilter] = useState<Filter>('all');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<Tender | null>(null);
  const [taking, setTaking] = useState<string | null>(null);

  useEffect(() => { load(); }, [filter]);

  async function load() {
    setLoading(true); setError('');
    try { setTenders(await api.tenders.list(filter)); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : 'Ошибка'); }
    finally { setLoading(false); }
  }

  async function handleRefresh() {
    setRefreshing(true);
    try { await api.tenders.refresh(); await load(); }
    catch (e: unknown) { alert(e instanceof Error ? e.message : 'Ошибка обновления'); }
    finally { setRefreshing(false); }
  }

  async function handleTake(number: string) {
    setTaking(number);
    try {
      await api.tenders.take(number);
      // Haptic feedback
      try { window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success'); } catch {}
      await load();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Ошибка');
    } finally { setTaking(null); }
  }

  if (selected) {
    return (
      <TenderDetail
        tender={selected}
        onBack={() => { setSelected(null); load(); }}
        onTake={handleTake}
        taking={taking === selected.external_number}
      />
    );
  }

  const hot = tenders.filter(t => t.rating === 'fire').length;
  const ok = tenders.filter(t => t.rating === 'ok').length;
  const risk = tenders.filter(t => t.rating === 'warn').length;

  return (
    <>
      {/* AI Status Header */}
      <div style={{
        background: 'var(--bg-green)', border: '0.5px solid #1a4020', borderRadius: 10,
        padding: '10px 12px', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 10
      }}>
        <div className="sdot sdot-green ai-dot" style={{ width: 10, height: 10 }} />
        <div style={{ flex: 1 }}>
          <div style={{ color: 'var(--green)', fontSize: 12, fontWeight: 600 }}>Claude анализирует ЕИС</div>
          <div style={{ color: 'var(--text2)', fontSize: 10, marginTop: 2 }}>
            {tenders.length > 0 ? `${tenders.length} тендеров загружено` : 'Нет данных · запустите парсер'}
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="summary-row" style={{ marginBottom: 10 }}>
        <div className="sum-box sum-fire"><div className="sum-num">{hot}</div><div className="sum-label">Топовые 🔥</div></div>
        <div className="sum-box sum-ok"><div className="sum-num">{ok}</div><div className="sum-label">Подходят ✅</div></div>
        <div className="sum-box sum-risk"><div className="sum-num">{risk}</div><div className="sum-label">С рисками ⚠️</div></div>
      </div>

      {/* Filters */}
      <div className="filter-row">
        {FILTERS.map(f => (
          <button
            key={f.key}
            className={`filter-chip${filter === f.key ? ' active-green' : ''}`}
            onClick={() => setFilter(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="section-row">
        <span className="section-title">Найдено сегодня</span>
        <button
          className="section-action"
          onClick={handleRefresh}
          disabled={refreshing}
          style={{ color: 'var(--green)' }}
        >
          {refreshing ? '…' : '↻ обновить'}
        </button>
      </div>

      {loading && <AIAutoSkeleton />}
      {error && (
        <div className="state-center">
          <div className="state-icon">⚠️</div>
          <div className="state-text">{error}</div>
          <button className="btn btn-primary" onClick={load} style={{ marginTop: 12 }}>Повторить</button>
        </div>
      )}
      {!loading && !error && tenders.length === 0 && (
        <div className="state-center">
          <div className="state-icon">🤖</div>
          <div className="state-title">Тендеров нет</div>
          <div className="state-text">Запустите парсер через бота командой /parse, затем /analyze</div>
        </div>
      )}

      {tenders.map(t => (
        <TenderCard
          key={t.external_number}
          tender={t}
          onDetails={() => setSelected(t)}
          onTake={() => handleTake(t.external_number)}
          taking={taking === t.external_number}
        />
      ))}
    </>
  );
}

function TenderCard({ tender: t, onDetails, onTake, taking }: {
  tender: Tender; onDetails: () => void; onTake: () => void; taking: boolean;
}) {
  const taken = t.portal_status === 'in_work';
  const emoji = RATING_EMOJI[t.rating || 'ok'] || '❓';
  const marginPct = t.margin_percent;
  const marginClass = marginPct && marginPct >= 35 ? 'margin-high' : 'margin-mid';

  return (
    <div className={`card${taken ? ' card-taken' : ''}`} style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 8 }}>
        <span style={{ fontSize: 18, flexShrink: 0, marginTop: 2 }}>{emoji}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', lineHeight: 1.3 }}>{t.name}</div>
          <div style={{ fontSize: 10, color: 'var(--text3)', marginTop: 3 }}>
            №{t.external_number} · {t.law || '44-ФЗ'}
          </div>
        </div>
        {marginPct != null && (
          <div className={`margin-badge ${marginClass}`} style={{ flexShrink: 0 }}>
            {Math.round(marginPct)}%
          </div>
        )}
      </div>

      <div className="tender-grid">
        <div className="tg-item">
          <div className="tg-label">Сумма договора</div>
          <div className="tg-value text-green">{t.nmc ? `${(t.nmc / 1_000_000).toFixed(1)} млн ₽` : '—'}</div>
        </div>
        <div className="tg-item">
          <div className="tg-label">Срок поставки</div>
          <div className="tg-value text-blue">{t.delivery_days ? `${t.delivery_days} дн.` : '—'}</div>
        </div>
        <div className="tg-item">
          <div className="tg-label">Регион</div>
          <div className="tg-value">{[t.region, t.federal_district].filter(Boolean).join(' · ') || '—'}</div>
        </div>
        <div className="tg-item">
          <div className="tg-label">Маржа Claude</div>
          <div className="tg-value text-green">{marginPct != null ? `~${Math.round(marginPct)}%` : '—'}</div>
        </div>
      </div>

      {t.cert_requirements && t.cert_requirements.length > 0 && (
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 }}>
          {t.cert_requirements.map((c, i) => (
            <span key={i} style={{
              background: '#2a1a00', color: 'var(--orange)', padding: '2px 6px',
              borderRadius: 4, fontSize: 10
            }}>{c}</span>
          ))}
          {t.typical_participants && (
            <span style={{ fontSize: 10, color: 'var(--text3)' }}>· ~{t.typical_participants} участника</span>
          )}
        </div>
      )}

      {taken ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="av av-sm" style={{ background: 'var(--bg-blue)', color: 'var(--blue)' }}>
            {(t.taken_by_name || '?')[0]}
          </div>
          <span style={{ color: 'var(--blue)', fontSize: 11, flex: 1 }}>
            {t.taken_by_name} взял(а) в работу
          </span>
          <span style={{ fontSize: 10, color: 'var(--text3)' }}>
            {t.taken_at ? fmtDate(t.taken_at) : ''}
          </span>
        </div>
      ) : (
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            className="btn btn-green"
            style={{ flex: 1, fontSize: 12 }}
            onClick={onTake}
            disabled={taking}
          >
            {taking ? '…' : '✅ Взять в работу'}
          </button>
          <button className="btn btn-ghost" style={{ fontSize: 12 }} onClick={onDetails}>
            Подробнее →
          </button>
        </div>
      )}
    </div>
  );
}

function TenderDetail({ tender: t, onBack, onTake, taking }: {
  tender: Tender; onBack: () => void;
  onTake: (n: string) => void; taking: boolean;
}) {
  const taken = t.portal_status === 'in_work';
  const emoji = RATING_EMOJI[t.rating || 'ok'] || '❓';

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <button className="btn btn-ghost" onClick={onBack} style={{ padding: '6px 12px', fontSize: 13 }}>
          ← Назад
        </button>
        <span style={{ fontWeight: 600, fontSize: 15, flex: 1 }} className="truncate">
          {emoji} Детали тендера
        </span>
      </div>

      <div className="card" style={{ marginBottom: 10 }}>
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 6 }}>{t.name}</div>
        <div style={{ fontSize: 11, color: 'var(--text3)', marginBottom: 12 }}>
          №{t.external_number} · {t.law || '44-ФЗ'}
        </div>

        <div className="tender-grid">
          <div className="tg-item">
            <div className="tg-label">Сумма</div>
            <div className="tg-value text-green">{t.nmc ? `${(t.nmc / 1_000_000).toFixed(2)} млн ₽` : '—'}</div>
          </div>
          <div className="tg-item">
            <div className="tg-label">Маржа</div>
            <div className="tg-value text-green">{t.margin_percent != null ? `${Math.round(t.margin_percent)}%` : '—'}</div>
          </div>
          <div className="tg-item">
            <div className="tg-label">Себестоимость</div>
            <div className="tg-value text-blue">{t.cost_estimate ? `${(t.cost_estimate / 1_000_000).toFixed(2)} млн` : '—'}</div>
          </div>
          <div className="tg-item">
            <div className="tg-label">Заказчик</div>
            <div className="tg-value" style={{ fontSize: 10 }}>{t.customer || '—'}</div>
          </div>
          <div className="tg-item">
            <div className="tg-label">Регион</div>
            <div className="tg-value">{t.region || '—'}</div>
          </div>
          <div className="tg-item">
            <div className="tg-label">Срок</div>
            <div className="tg-value">{t.delivery_days ? `${t.delivery_days} дн.` : '—'}</div>
          </div>
        </div>
      </div>

      {t.analysis_text && (
        <div className="card" style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 10, color: 'var(--green)', fontWeight: 600, marginBottom: 6 }}>
            ⚡ AI анализ Claude
          </div>
          <div style={{ fontSize: 12, color: 'var(--text2)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
            {t.analysis_text}
          </div>
        </div>
      )}

      {t.source_url || t.url ? (
        <button
          className="btn btn-ghost btn-full"
          style={{ marginBottom: 10, fontSize: 12 }}
          onClick={() => {
            const url = t.source_url || t.url;
            if (url) window.Telegram?.WebApp?.openLink?.(url);
          }}
        >
          Открыть на ЕИС →
        </button>
      ) : null}

      {!taken && (
        <button
          className="btn btn-green btn-full"
          onClick={() => onTake(t.external_number)}
          disabled={taking}
        >
          {taking ? 'Обрабатываю…' : '✅ Взять в работу'}
        </button>
      )}

      {taken && (
        <div className="card" style={{ background: '#0d1a2a', borderColor: '#1a3a5f' }}>
          <div style={{ color: 'var(--blue)', fontSize: 13 }}>
            ✅ Взят в работу · {t.taken_by_name}
          </div>
        </div>
      )}
    </>
  );
}

function AIAutoSkeleton() {
  return (
    <>
      {[0,1,2].map(i => (
        <div key={i} className="skeleton" style={{ height: 180, borderRadius: 12, marginBottom: 10 }} />
      ))}
    </>
  );
}

function fmtDate(iso: string): string {
  try { return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }); }
  catch { return iso; }
}

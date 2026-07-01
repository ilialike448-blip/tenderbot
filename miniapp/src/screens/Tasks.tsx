import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Task, User } from '../api/types';
// User is used in Props interfaces below

type Filter = 'all' | 'new' | 'in_work' | 'review' | 'done';

const FILTERS: { key: Filter; label: string }[] = [
  { key: 'all', label: 'Все' },
  { key: 'in_work', label: 'В работе' },
  { key: 'new', label: 'Новые' },
  { key: 'review', label: 'Проверка' },
  { key: 'done', label: 'Готово' },
];

const STATUS_BADGE: Record<string, string> = {
  new: 'badge-new', in_work: 'badge-wip', review: 'badge-review', done: 'badge-done',
};
const STATUS_LABEL: Record<string, string> = {
  new: 'Новая', in_work: 'В работе', review: 'Проверка', done: 'Готово',
};
const PRIORITY_COLORS: Record<string, string> = {
  high: 'var(--red)', med: 'var(--orange)', low: 'var(--text3)',
};
const PRIORITY_LABELS: Record<string, string> = {
  high: 'Высокий', med: 'Средний', low: 'Низкий',
};

interface Props { user: User; }

export default function Tasks({ user }: Props) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<Filter>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  useEffect(() => { load(filter); }, [filter]);

  async function load(f: Filter) {
    setLoading(true); setError('');
    try { setTasks(await api.tasks.list(f)); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : 'Ошибка'); }
    finally { setLoading(false); }
  }

  const active = tasks.filter(t => t.status !== 'done');
  const done = tasks.filter(t => t.status === 'done');

  const summary = {
    done: tasks.filter(t => t.status === 'done').length,
    in_work: tasks.filter(t => t.status === 'in_work').length,
    new_count: tasks.filter(t => t.status === 'new').length,
  };

  if (selectedTask) {
    return (
      <TaskDetail
        task={selectedTask}
        user={user}
        onBack={() => { setSelectedTask(null); load(filter); }}
      />
    );
  }

  if (showCreate) {
    return (
      <CreateTaskForm
        onBack={() => { setShowCreate(false); load(filter); }}
      />
    );
  }

  return (
    <>
      <div className="summary-row">
        <div className="sum-box sum-green"><div className="sum-num">{summary.done}</div><div className="sum-label">Выполнено</div></div>
        <div className="sum-box sum-blue"><div className="sum-num">{summary.in_work}</div><div className="sum-label">В работе</div></div>
        <div className="sum-box sum-orange"><div className="sum-num">{summary.new_count}</div><div className="sum-label">Новые</div></div>
      </div>

      <div className="filter-row">
        {FILTERS.map(f => (
          <button
            key={f.key}
            className={`filter-chip${filter === f.key ? ' active-blue' : ''}`}
            onClick={() => setFilter(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="section-row">
        <span className="section-title">
          Задачи{filter !== 'all' ? ` · ${FILTERS.find(f => f.key === filter)?.label}` : ' · все'}
        </span>
        <button className="section-action" onClick={() => setShowCreate(true)}>+ создать</button>
      </div>

      {loading && <TasksSkeleton />}
      {error && (
        <div className="state-center">
          <div className="state-icon">⚠️</div>
          <div className="state-text">{error}</div>
          <button className="btn btn-primary" onClick={() => load(filter)} style={{ marginTop: 12 }}>
            Повторить
          </button>
        </div>
      )}

      {!loading && !error && active.length === 0 && done.length === 0 && (
        <div className="state-center">
          <div className="state-icon">📋</div>
          <div className="state-title">Задач нет</div>
          <div className="state-text">Нажми «+ создать» чтобы добавить задачу.</div>
        </div>
      )}

      {active.map(t => (
        <TaskCard key={t.id} task={t} onClick={() => setSelectedTask(t)} />
      ))}

      {done.length > 0 && (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '12px 0 8px' }}>
            <div className="divider" style={{ flex: 1 }} />
            <span style={{ fontSize: 10, color: 'var(--text2)' }}>Завершённые</span>
            <div className="divider" style={{ flex: 1 }} />
          </div>
          {done.map(t => (
            <TaskCard key={t.id} task={t} onClick={() => setSelectedTask(t)} done />
          ))}
        </>
      )}
    </>
  );
}

function TaskCard({ task: t, onClick, done = false }: { task: Task; onClick: () => void; done?: boolean }) {
  const assigneeName = [t.assignee_first, t.assignee_last].filter(Boolean).join(' ');

  return (
    <div
      className="card"
      style={{ opacity: done ? 0.65 : 1, cursor: 'pointer', marginBottom: 8 }}
      onClick={onClick}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', flex: 1, lineHeight: 1.3,
          textDecoration: done ? 'line-through' : 'none' }}>
          {t.title}
        </div>
        <span className={`badge ${STATUS_BADGE[t.status]}`} style={{ marginLeft: 8, flexShrink: 0 }}>
          {STATUS_LABEL[t.status]}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, fontSize: 10, color: 'var(--text2)', marginBottom: 8 }}>
        <span>👤 {assigneeName || '—'}</span>
        <span>📅 {t.due_date ? fmtDate(t.due_date) : '—'}</span>
        <span>⏱ {fmtTime(t.time_spent_min)}</span>
        <span style={{ color: PRIORITY_COLORS[t.priority] }}>
          ● {PRIORITY_LABELS[t.priority]}
        </span>
      </div>

      <div className="progress-bar-wrap">
        <div
          className={`progress-bar-fill${done ? ' done' : ''}`}
          style={{ width: `${t.progress_pct}%` }}
        />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, fontSize: 10 }}>
        <span style={{ color: done ? 'var(--green)' : 'var(--text2)' }}>{t.progress_pct}%</span>
        {t.tender_number && (
          <span style={{ color: 'var(--blue)' }}>🏷 №{t.tender_number.slice(0, 10)}…</span>
        )}
      </div>
    </div>
  );
}

function TaskDetail({ task: t, user, onBack }: { task: Task; user: User; onBack: () => void }) {
  const [status, setStatus] = useState(t.status);
  const [progress, setProgress] = useState(t.progress_pct);
  const [saving, setSaving] = useState(false);

  const canEdit = user.role !== 'member' || t.assignee_id === user.telegram_id;

  async function save() {
    setSaving(true);
    try {
      await api.tasks.update(t.id, { status, progress_pct: progress });
      onBack();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Ошибка');
    } finally { setSaving(false); }
  }

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <button className="btn btn-ghost" onClick={onBack} style={{ padding: '6px 12px', fontSize: 13 }}>
          ← Назад
        </button>
        <span style={{ fontWeight: 600, fontSize: 15, flex: 1 }} className="truncate">{t.title}</span>
      </div>

      <div className="card" style={{ marginBottom: 12 }}>
        <div className="form-group">
          <label className="form-label">Статус</label>
          {canEdit ? (
            <div className="filter-row" style={{ flexWrap: 'wrap' }}>
              {(['new', 'in_work', 'review', 'done'] as const).map(s => (
                <button
                  key={s}
                  className={`filter-chip${status === s ? ' active-blue' : ''}`}
                  onClick={() => setStatus(s)}
                >
                  {STATUS_LABEL[s]}
                </button>
              ))}
            </div>
          ) : (
            <span className={`badge ${STATUS_BADGE[status]}`}>{STATUS_LABEL[status]}</span>
          )}
        </div>

        <div className="form-group">
          <label className="form-label">Прогресс: {progress}%</label>
          {canEdit ? (
            <input
              type="range" min={0} max={100} value={progress}
              onChange={e => setProgress(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--blue)' }}
            />
          ) : (
            <div className="progress-bar-wrap">
              <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
            </div>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 12, color: 'var(--text2)' }}>
          <div>👤 Исполнитель<br /><span style={{ color: 'var(--text)', fontWeight: 600 }}>
            {[t.assignee_first, t.assignee_last].filter(Boolean).join(' ') || '—'}
          </span></div>
          <div>📅 Дедлайн<br /><span style={{ color: 'var(--text)', fontWeight: 600 }}>
            {t.due_date ? fmtDate(t.due_date) : '—'}
          </span></div>
          <div>⏱ Затрачено<br /><span style={{ color: 'var(--text)', fontWeight: 600 }}>
            {fmtTime(t.time_spent_min)}
          </span></div>
          <div>🏷 Тендер<br /><span style={{ color: 'var(--blue)', fontWeight: 600 }}>
            {t.tender_number ? `№${t.tender_number.slice(0, 10)}…` : '—'}
          </span></div>
        </div>
      </div>

      {canEdit && (
        <button className="btn btn-primary btn-full" onClick={save} disabled={saving}>
          {saving ? 'Сохраняю…' : 'Сохранить изменения'}
        </button>
      )}
    </>
  );
}

function CreateTaskForm({ onBack }: { onBack: () => void }) {
  const [title, setTitle] = useState('');
  const [priority, setPriority] = useState('med');
  const [dueDate, setDueDate] = useState('');
  const [saving, setSaving] = useState(false);

  async function submit() {
    if (!title.trim()) return;
    setSaving(true);
    try {
      await api.tasks.create({ title: title.trim(), priority, due_date: dueDate || undefined });
      onBack();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Ошибка');
    } finally { setSaving(false); }
  }

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <button className="btn btn-ghost" onClick={onBack} style={{ padding: '6px 12px', fontSize: 13 }}>
          ← Назад
        </button>
        <span style={{ fontWeight: 600, fontSize: 15 }}>Новая задача</span>
      </div>

      <div className="form-group">
        <label className="form-label">Название *</label>
        <input
          className="form-input"
          placeholder="Что нужно сделать?"
          value={title}
          onChange={e => setTitle(e.target.value)}
          autoFocus
        />
      </div>

      <div className="form-group">
        <label className="form-label">Приоритет</label>
        <div className="filter-row">
          {(['low', 'med', 'high'] as const).map(p => (
            <button
              key={p}
              className={`filter-chip${priority === p ? ' active-blue' : ''}`}
              onClick={() => setPriority(p)}
            >
              <span style={{ color: PRIORITY_COLORS[p] }}>●</span> {PRIORITY_LABELS[p]}
            </button>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Дедлайн</label>
        <input
          type="date"
          className="form-input"
          value={dueDate}
          onChange={e => setDueDate(e.target.value)}
          style={{ colorScheme: 'dark' }}
        />
      </div>

      <button className="btn btn-primary btn-full" onClick={submit} disabled={saving || !title.trim()}>
        {saving ? 'Создаю…' : 'Создать задачу'}
      </button>
    </>
  );
}

function TasksSkeleton() {
  return (
    <>
      {[0,1,2].map(i => (
        <div key={i} className="skeleton" style={{ height: 110, borderRadius: 12, marginBottom: 8 }} />
      ))}
    </>
  );
}

function fmtDate(iso: string): string {
  try { return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }); }
  catch { return iso; }
}

function fmtTime(min: number): string {
  if (!min) return '0 мин';
  if (min < 60) return `${min} мин`;
  return `${Math.floor(min / 60)}ч ${min % 60}мин`;
}

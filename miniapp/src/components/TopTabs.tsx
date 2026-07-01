type Tab = 'dashboard' | 'tasks' | 'ai';

interface Props {
  active: Tab;
  onChange: (t: Tab) => void;
}

export default function TopTabs({ active, onChange }: Props) {
  return (
    <div className="top-tabs">
      <button
        className={`top-tab${active === 'dashboard' ? ' active-blue' : ''}`}
        onClick={() => onChange('dashboard')}
      >
        Главная
      </button>
      <button
        className={`top-tab${active === 'tasks' ? ' active-blue' : ''}`}
        onClick={() => onChange('tasks')}
      >
        Задачи
      </button>
      <button
        className={`top-tab${active === 'ai' ? ' active-green' : ''}`}
        onClick={() => onChange('ai')}
      >
        ⚡ AI авто
      </button>
    </div>
  );
}

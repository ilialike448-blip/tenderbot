interface Props {
  status: 'pending' | 'rejected' | 'blocked';
}

export default function PendingScreen({ status }: Props) {
  if (status === 'pending') {
    return (
      <div className="state-center" style={{ height: '100vh' }}>
        <div className="state-icon">⏳</div>
        <div className="state-title">Заявка отправлена</div>
        <div className="state-text">
          Ожидайте подтверждения руководителя.<br />
          Вы получите уведомление, когда доступ будет открыт.
        </div>
      </div>
    );
  }

  if (status === 'rejected') {
    return (
      <div className="state-center" style={{ height: '100vh' }}>
        <div className="state-icon">❌</div>
        <div className="state-title">Доступ отклонён</div>
        <div className="state-text">Обратитесь к руководителю за разъяснениями.</div>
      </div>
    );
  }

  return (
    <div className="state-center" style={{ height: '100vh' }}>
      <div className="state-icon">🚫</div>
      <div className="state-title">Доступ заблокирован</div>
      <div className="state-text">Обратитесь к руководителю.</div>
    </div>
  );
}

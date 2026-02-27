export default function BottomNav({ page, setPage, isAdmin }) {
  const items = [
    { id: 'dashboard', icon: '🏠', label: 'Главная' },
    { id: 'operation', icon: '➕', label: 'Операция' },
    { id: 'history',   icon: '📋', label: 'История' },
    { id: 'debts',     icon: '🔴', label: 'Долги' },
    { id: 'report',    icon: '📊', label: 'Сводка' },
  ]
  if (isAdmin) items.push({ id: 'admin', icon: '⚙️', label: 'Управление' })

  return (
    <nav className="bottom-nav">
      {items.map((item) => (
        <button
          key={item.id}
          className={`nav-item ${page === item.id ? 'active' : ''}`}
          onClick={() => setPage(item.id)}
        >
          <span className="nav-icon">{item.icon}</span>
          <span>{item.label}</span>
        </button>
      ))}
    </nav>
  )
}

export default function BottomNav({ page, setPage, userRole }) {
  const isJunior = userRole === 'junior'
  const isAdmin = userRole === 'admin'

  const items = [
    { id: 'dashboard', icon: '🏠', label: 'Главная' },
  ]
  if (!isJunior) items.push({ id: 'operation', icon: '➕', label: 'Операция' })
  items.push(
    { id: 'history', icon: '📋', label: 'История' },
    { id: 'debts',   icon: '🔴', label: 'Долги' },
    { id: 'report',  icon: '📊', label: 'Сводка' },
  )
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

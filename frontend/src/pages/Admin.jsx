import { useEffect, useState } from 'react'
import client from '../api/client'
import Loader from '../components/Loader'
import Toast from '../components/Toast'

function fmt(n) {
  return new Intl.NumberFormat('ru-RU').format(n) + ' ₽'
}

function CreateIpModal({ onClose, onCreated }) {
  const [name, setName] = useState('')
  const [capital, setCapital] = useState('')
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  const handleCreate = async () => {
    if (!name.trim()) return setToast('Введите название ИП')
    const cap = parseInt(capital, 10)
    if (!cap || cap < 0) return setToast('Введите начальный капитал')
    setLoading(true)
    try {
      const res = await client.post('/admin/ips', { name: name.trim(), initial_capital: cap })
      onCreated(res.data)
    } catch (e) {
      setToast('❌ ' + (e.response?.data?.detail || 'Ошибка'))
      setLoading(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.5)', display: 'flex', alignItems: 'flex-end', zIndex: 200 }}>
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      <div style={{ background: 'var(--bg)', borderRadius: '20px 20px 0 0', padding: '24px 16px', width: '100%' }}>
        <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 16 }}>➕ Создать ИП</div>
        <div className="input-group">
          <label className="input-label">Название ИП</label>
          <input className="input-field" placeholder="Анна, Василий..." value={name} onChange={e => setName(e.target.value)} />
        </div>
        <div className="input-group">
          <label className="input-label">Начальный капитал (на Р/С)</label>
          <input className="input-field" type="number" inputMode="numeric" placeholder="1000000" value={capital} onChange={e => setCapital(e.target.value)} />
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={onClose} style={{ flex: 1 }}>Отмена</button>
          <button className="btn btn-primary" onClick={handleCreate} disabled={loading} style={{ flex: 1 }}>
            {loading ? '⏳' : '✅ Создать'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Admin({ currentUser }) {
  const [tab, setTab] = useState('users')   // 'users' | 'ips'
  const [users, setUsers] = useState([])
  const [ips, setIps] = useState([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState(null)
  const [showCreateIp, setShowCreateIp] = useState(false)

  const loadData = () => {
    setLoading(true)
    Promise.all([
      client.get('/admin/users'),
      client.get('/admin/ips'),
    ]).then(([uRes, ipRes]) => {
      setUsers(uRes.data)
      setIps(ipRes.data)
    }).catch(() => setToast('❌ Нет прав доступа'))
      .finally(() => setLoading(false))
  }

  useEffect(loadData, [])

  const toggleRole = async (user) => {
    const newRole = user.role === 'admin' ? 'user' : 'admin'
    try {
      await client.patch(`/admin/users/${user.id}/role`, { role: newRole })
      setUsers(prev => prev.map(u => u.id === user.id ? { ...u, role: newRole } : u))
      setToast(`✅ Роль ${user.display_name} изменена`)
    } catch (e) {
      setToast('❌ ' + (e.response?.data?.detail || 'Ошибка'))
    }
  }

  if (loading) return <div className="page-content"><Loader /></div>

  return (
    <div className="page-content">
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      {showCreateIp && (
        <CreateIpModal
          onClose={() => setShowCreateIp(false)}
          onCreated={(ip) => { setIps(prev => [...prev, ip]); setShowCreateIp(false); setToast(`✅ ИП «${ip.name}» создано`) }}
        />
      )}

      <div className="page-header">⚙️ Управление</div>

      {/* Переключатель вкладок */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <button className={`btn ${tab === 'users' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTab('users')} style={{ flex: 1 }}>
          👥 Пользователи
        </button>
        <button className={`btn ${tab === 'ips' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTab('ips')} style={{ flex: 1 }}>
          🏦 ИП
        </button>
      </div>

      {/* Пользователи */}
      {tab === 'users' && (
        <>
          <div className="hint" style={{ marginBottom: 12 }}>
            Всего: {users.length} пользователей
          </div>
          {users.map(u => (
            <div key={u.id} className="user-item">
              <div className="user-avatar">{(u.display_name || '?')[0].toUpperCase()}</div>
              <div className="user-info">
                <div className="user-name">
                  {u.display_name}
                  {u.id === currentUser?.id && <span style={{ fontSize: 11, color: 'var(--hint)', marginLeft: 6 }}>(вы)</span>}
                </div>
                <div className="user-meta">Баланс: {fmt(u.cash_balance)}</div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                <span className={`user-role ${u.role}`}>
                  {u.role === 'admin' ? '👑 Админ' : '👤 Юзер'}
                </span>
                {u.id !== currentUser?.id && (
                  <button
                    className="btn btn-secondary btn-sm"
                    style={{ width: 'auto', padding: '4px 10px' }}
                    onClick={() => toggleRole(u)}
                  >
                    Сменить
                  </button>
                )}
              </div>
            </div>
          ))}
        </>
      )}

      {/* ИП */}
      {tab === 'ips' && (
        <>
          <button className="btn btn-primary" style={{ marginBottom: 16 }} onClick={() => setShowCreateIp(true)}>
            ➕ Создать ИП
          </button>
          {ips.length === 0 && <div className="card text-center"><div className="hint">ИП не созданы</div></div>}
          {ips.map(ip => (
            <div key={ip.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ fontWeight: 700, fontSize: 16 }}>{ip.name}</div>
                <div className="hint" style={{ fontSize: 12 }}>ID: {ip.id}</div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, marginTop: 10 }}>
                <div><div className="card-title">Р/С</div><div style={{ fontWeight: 700 }}>{fmt(ip.bank_balance)}</div></div>
                <div><div className="card-title">Наличные</div><div style={{ fontWeight: 700 }}>{fmt(ip.cash_balance)}</div></div>
                <div><div className="card-title">Нач. капитал</div><div style={{ fontWeight: 700 }}>{fmt(ip.initial_capital)}</div></div>
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  )
}

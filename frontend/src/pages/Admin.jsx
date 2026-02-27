import { useEffect, useState } from 'react'
import client from '../api/client'
import Loader from '../components/Loader'
import Toast from '../components/Toast'

function fmt(n) {
  return new Intl.NumberFormat('ru-RU').format(n) + ' \u20bd'
}

function CreateIpModal({ onClose, onCreated }) {
  const [name, setName] = useState('')
  const [bank, setBank] = useState('')
  const [cash, setCash] = useState('')
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  const handleCreate = async () => {
    if (!name.trim()) return setToast('Введите название ИП')
    const bankVal = parseInt(bank, 10) || 0
    const cashVal = parseInt(cash, 10) || 0
    setLoading(true)
    try {
      const res = await client.post('/admin/ips', {
        name: name.trim(),
        bank_balance: bankVal,
        cash_balance: cashVal,
      })
      onCreated(res.data)
    } catch (e) {
      setToast('Ошибка: ' + (e.response?.data?.detail || 'неизвестная'))
      setLoading(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.5)', display: 'flex', alignItems: 'flex-end', zIndex: 200 }}>
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      <div style={{ background: 'var(--bg)', borderRadius: '20px 20px 0 0', padding: '24px 16px', width: '100%' }}>
        <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 16 }}>Создать ИП</div>
        <div className="input-group">
          <label className="input-label">Название ИП</label>
          <input className="input-field" placeholder="Анна, Василий..." value={name} onChange={e => setName(e.target.value)} />
        </div>
        <div className="input-group">
          <label className="input-label">Остаток на Р/С (руб)</label>
          <input className="input-field" type="number" inputMode="numeric" placeholder="0" value={bank} onChange={e => setBank(e.target.value)} />
        </div>
        <div className="input-group">
          <label className="input-label">Наличные ИП (руб)</label>
          <input className="input-field" type="number" inputMode="numeric" placeholder="0" value={cash} onChange={e => setCash(e.target.value)} />
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={onClose} style={{ flex: 1 }}>Отмена</button>
          <button className="btn btn-primary" onClick={handleCreate} disabled={loading} style={{ flex: 1 }}>
            {loading ? 'Создание...' : 'Создать'}
          </button>
        </div>
      </div>
    </div>
  )
}

function EditIpModal({ ip, onClose, onSaved }) {
  const [bank, setBank] = useState(String(ip.bank_balance))
  const [cash, setCash] = useState(String(ip.cash_balance))
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  const handleSave = async () => {
    const bankVal = parseInt(bank, 10)
    const cashVal = parseInt(cash, 10)
    if (isNaN(bankVal) || bankVal < 0) return setToast('Введите корректную сумму Р/С')
    if (isNaN(cashVal) || cashVal < 0) return setToast('Введите корректную сумму наличных')
    setLoading(true)
    try {
      const res = await client.patch('/admin/ips/' + ip.id + '/balances', {
        bank_balance: bankVal,
        cash_balance: cashVal,
      })
      onSaved(res.data)
    } catch (e) {
      setToast('Ошибка: ' + (e.response?.data?.detail || 'неизвестная'))
      setLoading(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.5)', display: 'flex', alignItems: 'flex-end', zIndex: 200 }}>
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      <div style={{ background: 'var(--bg)', borderRadius: '20px 20px 0 0', padding: '24px 16px', width: '100%' }}>
        <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 4 }}>{ip.name}</div>
        <div style={{ color: 'var(--hint)', fontSize: 13, marginBottom: 16 }}>Корректировка остатков</div>
        <div className="input-group">
          <label className="input-label">Остаток на Р/С (руб)</label>
          <input className="input-field" type="number" inputMode="numeric" value={bank} onChange={e => setBank(e.target.value)} />
        </div>
        <div className="input-group">
          <label className="input-label">Наличные ИП (руб)</label>
          <input className="input-field" type="number" inputMode="numeric" value={cash} onChange={e => setCash(e.target.value)} />
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={onClose} style={{ flex: 1 }}>Отмена</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={loading} style={{ flex: 1 }}>
            {loading ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Admin({ currentUser }) {
  const [tab, setTab] = useState('users')
  const [users, setUsers] = useState([])
  const [ips, setIps] = useState([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState(null)
  const [showCreateIp, setShowCreateIp] = useState(false)
  const [editingIp, setEditingIp] = useState(null)

  const loadData = () => {
    setLoading(true)
    Promise.all([
      client.get('/admin/users'),
      client.get('/admin/ips'),
    ]).then(([uRes, ipRes]) => {
      setUsers(uRes.data)
      setIps(ipRes.data)
    }).catch(() => setToast('Нет прав доступа'))
      .finally(() => setLoading(false))
  }

  useEffect(loadData, [])

  const toggleRole = async (user) => {
    const newRole = user.role === 'admin' ? 'user' : 'admin'
    try {
      await client.patch('/admin/users/' + user.id + '/role', { role: newRole })
      setUsers(prev => prev.map(u => u.id === user.id ? { ...u, role: newRole } : u))
      setToast('Роль ' + user.display_name + ' изменена')
    } catch (e) {
      setToast('Ошибка: ' + (e.response?.data?.detail || 'неизвестная'))
    }
  }

  if (loading) return <div className="page-content"><Loader /></div>

  return (
    <div className="page-content">
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      {showCreateIp && (
        <CreateIpModal
          onClose={() => setShowCreateIp(false)}
          onCreated={(ip) => {
            setIps(prev => [...prev, ip])
            setShowCreateIp(false)
            setToast('ИП создано: ' + ip.name)
          }}
        />
      )}
      {editingIp && (
        <EditIpModal
          ip={editingIp}
          onClose={() => setEditingIp(null)}
          onSaved={(updated) => {
            setIps(prev => prev.map(ip => ip.id === updated.id ? { ...ip, ...updated } : ip))
            setEditingIp(null)
            setToast('ИП обновлено: ' + updated.name)
          }}
        />
      )}

      <div className="page-header">Управление</div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <button className={'btn ' + (tab === 'users' ? 'btn-primary' : 'btn-secondary')} onClick={() => setTab('users')} style={{ flex: 1 }}>
          Пользователи
        </button>
        <button className={'btn ' + (tab === 'ips' ? 'btn-primary' : 'btn-secondary')} onClick={() => setTab('ips')} style={{ flex: 1 }}>
          ИП
        </button>
      </div>

      {tab === 'users' && (
        <div>
          <div className="hint" style={{ marginBottom: 12 }}>Всего: {users.length}</div>
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
                <span className={'user-role ' + u.role}>
                  {u.role === 'admin' ? 'Админ' : 'Юзер'}
                </span>
                {u.id !== currentUser?.id && (
                  <button className="btn btn-secondary btn-sm" style={{ width: 'auto', padding: '4px 10px' }} onClick={() => toggleRole(u)}>
                    Сменить
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'ips' && (
        <div>
          <button className="btn btn-primary" style={{ marginBottom: 16 }} onClick={() => setShowCreateIp(true)}>
            + Создать ИП
          </button>
          {ips.length === 0 && <div className="card"><div className="hint">ИП не созданы</div></div>}
          {ips.map(ip => (
            <div key={ip.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontWeight: 700, fontSize: 16 }}>{ip.name}</div>
                <button className="btn btn-secondary btn-sm" style={{ width: 'auto', padding: '4px 12px' }} onClick={() => setEditingIp(ip)}>
                  Изменить
                </button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 4, marginTop: 10 }}>
                <div><div className="card-title">Р/С</div><div style={{ fontWeight: 700 }}>{fmt(ip.bank_balance)}</div></div>
                <div><div className="card-title">Дебет</div><div style={{ fontWeight: 700 }}>{fmt(ip.debit_balance ?? 0)}</div></div>
                <div><div className="card-title">Наличные</div><div style={{ fontWeight: 700 }}>{fmt(ip.cash_balance)}</div></div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

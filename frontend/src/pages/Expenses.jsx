import { useEffect, useState } from 'react'
import client from '../api/client'
import Loader from '../components/Loader'
import Toast from '../components/Toast'

const SOURCE_LABELS = { cash: 'Нал', bank: 'Р/С', debit: 'Дебет' }

function fmt(n) {
  return new Intl.NumberFormat('ru-RU').format(n) + ' ₽'
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit' })
}

function AddExpenseModal({ onClose, onCreated }) {
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  const handleCreate = async () => {
    if (!description.trim()) return setToast('Введите описание')
    const amt = parseInt(amount, 10)
    if (!amt || amt <= 0) return setToast('Введите корректную сумму')
    setLoading(true)
    try {
      const res = await client.post('/expenses', { description: description.trim(), amount: amt })
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
        <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 16 }}>Добавить расход</div>
        <div className="input-group">
          <label className="input-label">Описание *</label>
          <input className="input-field" placeholder="Аренда, коммуналка..." value={description} onChange={e => setDescription(e.target.value)} />
        </div>
        <div className="input-group">
          <label className="input-label">Сумма (₽)</label>
          <input className="input-field" type="number" inputMode="numeric" placeholder="0" value={amount} onChange={e => setAmount(e.target.value)} />
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

function WriteOffModal({ expense, ips, onClose, onDone }) {
  const [ipId, setIpId] = useState('')
  const [amount, setAmount] = useState('')
  const [source, setSource] = useState('cash')
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  const handleWriteOff = async () => {
    if (!ipId) return setToast('Выберите ИП')
    const amt = parseInt(amount, 10)
    if (!amt || amt <= 0) return setToast('Введите корректную сумму')
    setLoading(true)
    try {
      await client.post('/expenses/' + expense.id + '/writeoffs', {
        ip_id: parseInt(ipId),
        amount: amt,
        source,
      })
      onDone()
    } catch (e) {
      setToast('Ошибка: ' + (e.response?.data?.detail || 'неизвестная'))
      setLoading(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.5)', display: 'flex', alignItems: 'flex-end', zIndex: 200 }}>
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      <div style={{ background: 'var(--bg)', borderRadius: '20px 20px 0 0', padding: '24px 16px', width: '100%' }}>
        <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 4 }}>Списать расход</div>
        <div style={{ color: 'var(--hint)', fontSize: 13, marginBottom: 16 }}>{expense.description}</div>
        <div className="input-group">
          <label className="input-label">ИП</label>
          <select className="input-field" value={ipId} onChange={e => setIpId(e.target.value)}>
            <option value="">— Выберите ИП —</option>
            {ips.map(ip => (
              <option key={ip.id} value={ip.id}>{ip.name}</option>
            ))}
          </select>
        </div>
        <div className="input-group">
          <label className="input-label">Сумма (₽)</label>
          <input className="input-field" type="number" inputMode="numeric" placeholder="0" value={amount} onChange={e => setAmount(e.target.value)} />
        </div>
        <div className="input-group">
          <label className="input-label">Источник</label>
          <div style={{ display: 'flex', gap: 8 }}>
            {['cash', 'bank', 'debit'].map(s => (
              <button
                key={s}
                className={'btn ' + (source === s ? 'btn-primary' : 'btn-secondary')}
                style={{ flex: 1 }}
                onClick={() => setSource(s)}
              >
                {SOURCE_LABELS[s]}
              </button>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={onClose} style={{ flex: 1 }}>Отмена</button>
          <button className="btn btn-primary" onClick={handleWriteOff} disabled={loading} style={{ flex: 1 }}>
            {loading ? 'Списание...' : 'Списать'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Expenses({ user }) {
  const [expenses, setExpenses] = useState([])
  const [ips, setIps] = useState([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState(null)
  const [showAdd, setShowAdd] = useState(false)
  const [writeOffTarget, setWriteOffTarget] = useState(null)

  const canCreate = user?.role === 'user' || user?.role === 'admin'

  const loadData = () => {
    setLoading(true)
    Promise.all([
      client.get('/expenses'),
      client.get('/balance'),
    ]).then(([expRes, balRes]) => {
      setExpenses(expRes.data)
      setIps(balRes.data.ips || [])
    }).catch(() => setToast('Ошибка загрузки'))
      .finally(() => setLoading(false))
  }

  useEffect(loadData, [])

  if (loading) return <div className="page-content"><Loader /></div>

  return (
    <div className="page-content">
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      {showAdd && (
        <AddExpenseModal
          onClose={() => setShowAdd(false)}
          onCreated={(exp) => {
            setExpenses(prev => [{ ...exp, created_at: new Date().toISOString(), writeoffs: [] }, ...prev])
            setShowAdd(false)
            setToast('✅ Расход добавлен')
          }}
        />
      )}
      {writeOffTarget && (
        <WriteOffModal
          expense={writeOffTarget}
          ips={ips}
          onClose={() => setWriteOffTarget(null)}
          onDone={() => {
            setWriteOffTarget(null)
            setToast('✅ Списано')
            loadData()
          }}
        />
      )}

      <div className="page-header">💰 Расходы</div>

      {canCreate && (
        <button className="btn btn-primary" style={{ marginBottom: 12 }} onClick={() => setShowAdd(true)}>
          + Добавить расход
        </button>
      )}

      {expenses.length === 0 ? (
        <div className="card text-center"><div className="hint">Расходов нет</div></div>
      ) : (
        expenses.map(exp => (
          <div key={exp.id} className="card" style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: 15 }}>{exp.description}</div>
                <div style={{ color: 'var(--hint)', fontSize: 12, marginTop: 2 }}>{formatDate(exp.created_at)}</div>
              </div>
              <div style={{ fontWeight: 700, fontSize: 16, color: 'var(--accent)' }}>{fmt(exp.amount)}</div>
            </div>
            {exp.writeoffs.length > 0 && (
              <div style={{ marginTop: 8, fontSize: 12, color: 'var(--hint)' }}>
                Списано: {exp.writeoffs.map(w => w.ip_name + ' ' + fmt(w.amount) + ' ' + SOURCE_LABELS[w.source]).join(' • ')}
              </div>
            )}
            {canCreate && (
              <button
                className="btn btn-secondary"
                style={{ marginTop: 10, padding: '6px 0' }}
                onClick={() => setWriteOffTarget(exp)}
              >
                Списать на ИП
              </button>
            )}
          </div>
        ))
      )}
    </div>
  )
}

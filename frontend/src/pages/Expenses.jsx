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

// Строка одного ИП в модалке списания
function IpRow({ ip, entry, onChange }) {
  return (
    <div style={{ borderTop: '1px solid var(--bg)', paddingTop: 10, marginTop: 6 }}>
      <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 6 }}>{ip.name}</div>
      <div style={{ display: 'flex', gap: 8 }}>
        <input
          className="input-field"
          type="number"
          inputMode="numeric"
          placeholder="Сумма"
          value={entry.amount}
          onChange={e => onChange({ ...entry, amount: e.target.value })}
          style={{ flex: 1, marginBottom: 0 }}
        />
        <div style={{ display: 'flex', gap: 4 }}>
          {['cash', 'bank', 'debit'].map(s => (
            <button
              key={s}
              className={'btn ' + (entry.source === s ? 'btn-primary' : 'btn-secondary')}
              style={{ padding: '0 10px', fontSize: 12 }}
              onClick={() => onChange({ ...entry, source: s })}
            >
              {SOURCE_LABELS[s]}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

function WriteOffModal({ expense, ips, alreadyWrittenOff, onClose, onDone }) {
  // entries: { [ip_id]: { amount: '', source: 'cash' } }
  const [entries, setEntries] = useState(
    Object.fromEntries(ips.map(ip => [ip.id, { amount: '', source: 'cash' }]))
  )
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  const remaining = expense.amount - alreadyWrittenOff

  const totalNew = ips.reduce((sum, ip) => {
    const amt = parseInt(entries[ip.id]?.amount, 10) || 0
    return sum + amt
  }, 0)

  const handleWriteOff = async () => {
    const toPost = ips
      .map(ip => ({ ip_id: ip.id, amount: parseInt(entries[ip.id]?.amount, 10) || 0, source: entries[ip.id]?.source || 'cash' }))
      .filter(e => e.amount > 0)

    if (toPost.length === 0) return setToast('Введите сумму хотя бы для одного ИП')

    if (totalNew > remaining && remaining > 0) {
      return setToast(`Сумма списания (${fmt(totalNew)}) превышает остаток расхода (${fmt(remaining)})`)
    }

    setLoading(true)
    try {
      await Promise.all(
        toPost.map(e =>
          client.post('/expenses/' + expense.id + '/writeoffs', {
            ip_id: e.ip_id,
            amount: e.amount,
            source: e.source,
          })
        )
      )
      onDone()
    } catch (e) {
      setToast('Ошибка: ' + (e.response?.data?.detail || 'неизвестная'))
      setLoading(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.5)', display: 'flex', alignItems: 'flex-end', zIndex: 200 }}>
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      <div style={{ background: 'var(--bg)', borderRadius: '20px 20px 0 0', padding: '24px 16px', width: '100%', maxHeight: '85vh', overflowY: 'auto' }}>
        <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 2 }}>Списать расход</div>
        <div style={{ color: 'var(--hint)', fontSize: 13, marginBottom: 4 }}>{expense.description}</div>

        {/* Остаток */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 12, fontSize: 13 }}>
          <span style={{ color: 'var(--hint)' }}>Заявлено: <b style={{ color: 'var(--text)' }}>{fmt(expense.amount)}</b></span>
          {alreadyWrittenOff > 0 && (
            <>
              <span style={{ color: 'var(--hint)' }}>Списано: <b style={{ color: '#ff3b30' }}>{fmt(alreadyWrittenOff)}</b></span>
              <span style={{ color: 'var(--hint)' }}>Остаток: <b style={{ color: remaining > 0 ? '#34c759' : '#ff3b30' }}>{fmt(remaining)}</b></span>
            </>
          )}
        </div>

        {/* Итого нового списания */}
        {totalNew > 0 && (
          <div style={{
            background: totalNew > remaining && remaining > 0 ? '#fff0f0' : 'var(--bg2)',
            borderRadius: 10,
            padding: '8px 12px',
            marginBottom: 10,
            fontSize: 13,
            fontWeight: 600,
            color: totalNew > remaining && remaining > 0 ? '#ff3b30' : 'var(--text)',
          }}>
            К списанию: {fmt(totalNew)}
            {totalNew > remaining && remaining > 0 && ' ⚠️ превышает остаток'}
          </div>
        )}

        {/* По каждому ИП */}
        {ips.map(ip => (
          <IpRow
            key={ip.id}
            ip={ip}
            entry={entries[ip.id]}
            onChange={val => setEntries(prev => ({ ...prev, [ip.id]: val }))}
          />
        ))}

        <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
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
          alreadyWrittenOff={writeOffTarget.writeoffs.reduce((s, w) => s + w.amount, 0)}
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
        expenses.map(exp => {
          const writtenOff = exp.writeoffs.reduce((s, w) => s + w.amount, 0)
          const remaining = exp.amount - writtenOff
          return (
            <div key={exp.id} className="card" style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>{exp.description}</div>
                  <div style={{ color: 'var(--hint)', fontSize: 12, marginTop: 2 }}>{formatDate(exp.created_at)}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontWeight: 700, fontSize: 16 }}>{fmt(exp.amount)}</div>
                  {writtenOff > 0 && (
                    <div style={{ fontSize: 12, marginTop: 2, color: remaining > 0 ? '#ff9500' : '#34c759' }}>
                      {remaining > 0 ? ('остаток ' + fmt(remaining)) : '✅ полностью списан'}
                    </div>
                  )}
                </div>
              </div>

              {exp.writeoffs.length > 0 && (
                <div style={{ marginTop: 8, padding: '8px 0 0', borderTop: '1px solid var(--bg)' }}>
                  {exp.writeoffs.map((w, i) => (
                    <div key={i} style={{ fontSize: 12, color: 'var(--hint)', display: 'flex', justifyContent: 'space-between' }}>
                      <span>{w.ip_name} · {SOURCE_LABELS[w.source]}</span>
                      <span style={{ fontWeight: 600, color: '#ff3b30' }}>-{fmt(w.amount)}</span>
                    </div>
                  ))}
                </div>
              )}

              {canCreate && remaining !== 0 && (
                <button
                  className="btn btn-secondary"
                  style={{ marginTop: 10, padding: '6px 0' }}
                  onClick={() => setWriteOffTarget(exp)}
                >
                  Списать на ИП
                </button>
              )}
            </div>
          )
        })
      )}
    </div>
  )
}

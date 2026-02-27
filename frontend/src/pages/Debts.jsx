import { useEffect, useState } from 'react'
import client from '../api/client'
import Loader from '../components/Loader'
import Toast from '../components/Toast'

function fmt(n) {
  return new Intl.NumberFormat('ru-RU').format(n) + ' ₽'
}

function RepayModal({ debt, onClose, onRepaid }) {
  const [amount, setAmount] = useState(String(debt.amount))
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  const handleRepay = async () => {
    const amt = parseInt(amount, 10)
    if (!amt || amt <= 0) return setToast('Введите сумму')
    if (amt > debt.amount) return setToast('Сумма превышает долг')
    setLoading(true)
    try {
      const res = await client.post(`/debts/${debt.id}/repay`, { amount: amt })
      onRepaid(res.data.new_balance)
    } catch (e) {
      setToast('❌ ' + (e.response?.data?.detail || 'Ошибка'))
      setLoading(false)
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,.5)',
      display: 'flex', alignItems: 'flex-end', zIndex: 200
    }}>
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      <div style={{
        background: 'var(--bg)', borderRadius: '20px 20px 0 0',
        padding: '24px 16px', width: '100%',
      }}>
        <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 8 }}>Погасить долг</div>
        <div style={{ color: 'var(--hint)', fontSize: 14, marginBottom: 16 }}>
          Кредитор: {debt.creditor_name} • Остаток: {fmt(debt.amount)}
        </div>
        <label className="input-label">Сумма погашения</label>
        <input
          className="input-field"
          type="number"
          inputMode="numeric"
          value={amount}
          onChange={e => setAmount(e.target.value)}
          style={{ marginBottom: 12 }}
        />
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={onClose} style={{ flex: 1 }}>Отмена</button>
          <button className="btn btn-primary" onClick={handleRepay} disabled={loading} style={{ flex: 1 }}>
            {loading ? '⏳' : '✅ Погасить'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Debts() {
  const [debts, setDebts] = useState(null)
  const [loading, setLoading] = useState(true)
  const [repaying, setRepaying] = useState(null)
  const [toast, setToast] = useState(null)

  const load = () => {
    setLoading(true)
    client.get('/debts')
      .then(r => setDebts(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  if (loading) return <div className="page-content"><Loader /></div>

  const handleRepaid = (newBalance) => {
    setRepaying(null)
    setToast(`✅ Погашено! Ваш баланс: ${fmt(newBalance)}`)
    load()
  }

  const hasDebts = (debts?.owed_to_me?.length > 0) || (debts?.i_owe?.length > 0)

  return (
    <div className="page-content">
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      {repaying && (
        <RepayModal
          debt={repaying}
          onClose={() => setRepaying(null)}
          onRepaid={handleRepaid}
        />
      )}

      <div className="page-header">🔴 Долги</div>

      {!hasDebts && (
        <div className="card text-center"><div className="hint">Долгов нет 🎉</div></div>
      )}

      {debts?.owed_to_me?.length > 0 && (
        <>
          <div className="section-title">Вам должны</div>
          {debts.owed_to_me.map(d => (
            <div key={d.id} className="debt-item">
              <div className="debt-info">
                <div className="debt-name">{d.debtor_name}</div>
                <div className="debt-amount">{fmt(d.amount)}</div>
              </div>
              <div style={{ fontSize: 22 }}>🟢</div>
            </div>
          ))}
        </>
      )}

      {debts?.i_owe?.length > 0 && (
        <>
          <div className="section-title mt-16">Вы должны</div>
          {debts.i_owe.map(d => (
            <div key={d.id} className="debt-item">
              <div className="debt-info">
                <div className="debt-name">{d.creditor_name}</div>
                <div className="debt-amount">{fmt(d.amount)}</div>
              </div>
              <button
                className="btn btn-primary btn-sm"
                style={{ width: 'auto', minWidth: 90 }}
                onClick={() => setRepaying(d)}
              >
                Погасить
              </button>
            </div>
          ))}
        </>
      )}
    </div>
  )
}

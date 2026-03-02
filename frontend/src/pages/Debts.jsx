import { useEffect, useState } from "react"
import client from "../api/client"
import Loader from "../components/Loader"
import Toast from "../components/Toast"

function fmt(n) {
  return new Intl.NumberFormat("ru-RU").format(n) + " ₽"
}

function RepayModal({ debt, onClose, onRepaid }) {
  const [amount, setAmount] = useState(String(debt.amount))
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  const handleRepay = async () => {
    const amt = parseInt(amount, 10)
    if (!amt || amt <= 0) return setToast("Введите сумму")
    if (amt > debt.amount) return setToast("Сумма превышает долг")
    setLoading(true)
    try {
      await client.post("/debts/" + debt.id + "/repay", { amount: amt })
      onRepaid()
    } catch (e) {
      setToast("❌ " + (e.response?.data?.detail || "Ошибка"))
      setLoading(false)
    }
  }

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.5)", display: "flex", alignItems: "flex-end", zIndex: 200 }}>
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      <div style={{ background: "var(--bg)", borderRadius: "20px 20px 0 0", padding: "24px 16px", width: "100%" }}>
        <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 4 }}>Погасить долг ИП</div>
        <div style={{ color: "var(--hint)", fontSize: 13, marginBottom: 16 }}>
          {debt.debtor_ip_name} → {debt.creditor_ip_name} • Остаток: {fmt(debt.amount)}
        </div>
        <div style={{ color: "var(--hint)", fontSize: 12, marginBottom: 12 }}>
          Деньги спишутся из наличных {debt.debtor_ip_name}
        </div>
        <label className="input-label">Сумма погашения</label>
        <input className="input-field" type="number" inputMode="numeric" value={amount} onChange={e => setAmount(e.target.value)} style={{ marginBottom: 12 }} />
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-secondary" onClick={onClose} style={{ flex: 1 }}>Отмена</button>
          <button className="btn btn-primary" onClick={handleRepay} disabled={loading} style={{ flex: 1 }}>{loading ? "⏳" : "✅ Погасить"}</button>
        </div>
      </div>
    </div>
  )
}

export default function Debts({ user }) {
  const [debts, setDebts] = useState([])
  const [loading, setLoading] = useState(true)
  const [repaying, setRepaying] = useState(null)
  const [toast, setToast] = useState(null)

  const load = () => {
    setLoading(true)
    client.get("/debts")
      .then(r => setDebts(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  if (loading) return <div className="page-content"><Loader /></div>

  return (
    <div className="page-content">
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      {repaying && (
        <RepayModal
          debt={repaying}
          onClose={() => setRepaying(null)}
          onRepaid={() => { setRepaying(null); setToast("✅ Погашено!"); load() }}
        />
      )}

      <div className="page-header">🔴 Долги между ИП</div>

      {debts.length === 0 && (
        <div className="card text-center"><div className="hint">Долгов нет 🎉</div></div>
      )}

      {debts.map(d => (
        <div key={d.id} className="debt-item">
          <div className="debt-info">
            <div className="debt-name">{d.debtor_ip_name} → {d.creditor_ip_name}</div>
            <div className="debt-amount">{fmt(d.amount)}</div>
          </div>
          {user?.role !== 'junior' && (
            <button className="btn btn-primary btn-sm" style={{ width: "auto", minWidth: 90 }} onClick={() => setRepaying(d)}>
              Погасить
            </button>
          )}
        </div>
      ))}
    </div>
  )
}

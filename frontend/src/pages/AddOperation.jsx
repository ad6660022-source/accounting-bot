import { useEffect, useState } from "react"
import client from "../api/client"
import Loader from "../components/Loader"
import Toast from "../components/Toast"

const tg = window.Telegram?.WebApp

const OPERATIONS = [
  { type: "zakup",       icon: "🛒", label: "Закуп",            needsIp: true,  needsTargetIp: false, needsComment: true,  needsDestination: false },
  { type: "storonnie",   icon: "💸", label: "Посторонние траты", needsIp: true,  needsTargetIp: false, needsComment: true,  needsDestination: false },
  { type: "prihod_mes",  icon: "📥", label: "Приход ежемес.",   needsIp: true,  needsTargetIp: false, needsComment: false, needsDestination: true  },
  { type: "prihod_fast", icon: "⚡", label: "Приход быстрый",   needsIp: true,  needsTargetIp: false, needsComment: false, needsDestination: true  },
  { type: "prihod_sto",  icon: "🏦", label: "Приход сторонний", needsIp: true,  needsTargetIp: false, needsComment: true,  needsDestination: true  },
  { type: "snyat_rs",    icon: "💴", label: "Снять с Р/С",      needsIp: true,  needsTargetIp: false, needsComment: false, needsDestination: false },
  { type: "snyat_debit", icon: "💵", label: "Снять с Дебета",   needsIp: true,  needsTargetIp: false, needsComment: false, needsDestination: false },
  { type: "vnesti_rs",   icon: "🏛",  label: "Внести на Р/С",    needsIp: true,  needsTargetIp: false, needsComment: false, needsDestination: false },
  { type: "odolzhit",    icon: "🤝", label: "Одолжить",         needsIp: true,  needsTargetIp: true,  needsComment: false, needsDestination: false },
]

const DESTINATIONS = [
  { value: "cash", label: "Наличные" },
  { value: "bank", label: "Р/С" },
  { value: "debit", label: "Дебет" },
]

function fmt(n) {
  return new Intl.NumberFormat("ru-RU").format(n) + " ₽"
}

export default function AddOperation({ user }) {
  const [ips, setIps] = useState([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [toast, setToast] = useState(null)

  const [selectedOp, setSelectedOp] = useState(null)
  const [selectedIp, setSelectedIp] = useState("")
  const [selectedTargetIp, setSelectedTargetIp] = useState("")
  const [amount, setAmount] = useState("")
  const [comment, setComment] = useState("")
  const [destination, setDestination] = useState("cash")

  useEffect(() => {
    client.get("/balance")
      .then(r => setIps(r.data.ips || []))
      .finally(() => setLoading(false))
  }, [])

  const op = OPERATIONS.find(o => o.type === selectedOp)

  const handleSubmit = async () => {
    if (!selectedOp) return setToast("Выберите тип операции")
    const amt = parseInt(amount, 10)
    if (!amt || amt <= 0) return setToast("Введите корректную сумму")
    if (op?.needsIp && !selectedIp) return setToast("Выберите ИП")
    if (op?.needsTargetIp && !selectedTargetIp) return setToast("Выберите ИП-заёмщика")
    if (op?.needsTargetIp && selectedIp === selectedTargetIp) return setToast("ИП-кредитор и ИП-заёмщик не могут совпадать")
    if (op?.needsComment && !comment.trim()) return setToast("Введите комментарий")

    setSubmitting(true)
    try {
      await client.post("/operations", {
        op_type: selectedOp,
        amount: amt,
        ip_id: selectedIp ? parseInt(selectedIp) : null,
        target_ip_id: selectedTargetIp ? parseInt(selectedTargetIp) : null,
        comment: comment.trim() || null,
        destination: op?.needsDestination ? destination : null,
      })
      tg?.HapticFeedback?.notificationOccurred("success")
      setToast("✅ Операция проведена!")
      setSelectedOp(null); setSelectedIp(""); setSelectedTargetIp(""); setAmount(""); setComment(""); setDestination("cash")
    } catch (e) {
      tg?.HapticFeedback?.notificationOccurred("error")
      setToast("❌ " + (e.response?.data?.detail || "Ошибка"))
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="page-content"><Loader /></div>

  if (user?.role === 'junior') {
    return (
      <div className="page-content">
        <div className="page-header">➕ Операция</div>
        <div className="card text-center">
          <div style={{ fontSize: 40, marginBottom: 12 }}>🔒</div>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Нет доступа</div>
          <div className="hint">Вы можете просматривать данные, но не можете проводить операции. Обратитесь к администратору для повышения прав.</div>
        </div>
      </div>
    )
  }

  return (
    <div className="page-content">
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      <div className="page-header">➕ Операция</div>
      <div className="section-title">Тип операции</div>
      <div className="op-grid">
        {OPERATIONS.map(o => (
          <button
            key={o.type}
            className={"op-btn " + (selectedOp === o.type ? "selected" : "")}
            onClick={() => { setSelectedOp(o.type); setSelectedIp(""); setSelectedTargetIp(""); setDestination("cash") }}
          >
            <span className="op-btn-icon">{o.icon}</span>
            <span className="op-btn-label">{o.label}</span>
          </button>
        ))}
      </div>

      {op?.needsIp && (
        <div className="input-group">
          <label className="input-label">{op.needsTargetIp ? "ИП (кто одалживает)" : "ИП"}</label>
          <select className="input-field" value={selectedIp} onChange={e => setSelectedIp(e.target.value)}>
            <option value="">— Выберите ИП —</option>
            {ips.map(ip => (
              <option key={ip.id} value={ip.id}>
                {ip.name} (Р/С: {fmt(ip.bank_balance)}, Деб: {fmt(ip.debit_balance)}, Нал: {fmt(ip.cash_balance)})
              </option>
            ))}
          </select>
        </div>
      )}

      {op?.needsTargetIp && (
        <div className="input-group">
          <label className="input-label">ИП (кому одалживают)</label>
          <select className="input-field" value={selectedTargetIp} onChange={e => setSelectedTargetIp(e.target.value)}>
            <option value="">— Выберите ИП —</option>
            {ips.filter(ip => String(ip.id) !== selectedIp).map(ip => (
              <option key={ip.id} value={ip.id}>{ip.name}</option>
            ))}
          </select>
        </div>
      )}

      {op?.needsDestination && (
        <div className="input-group">
          <label className="input-label">Куда зачислить</label>
          <div style={{ display: "flex", gap: 8 }}>
            {DESTINATIONS.map(d => (
              <button
                key={d.value}
                className={"btn " + (destination === d.value ? "btn-primary" : "btn-secondary")}
                style={{ flex: 1 }}
                onClick={() => setDestination(d.value)}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {selectedOp && (
        <div className="input-group">
          <label className="input-label">Сумма (₽)</label>
          <input className="input-field" type="number" inputMode="numeric" placeholder="Например: 5000" value={amount} onChange={e => setAmount(e.target.value)} />
        </div>
      )}

      {op?.needsComment && (
        <div className="input-group">
          <label className="input-label">Комментарий *</label>
          <input className="input-field" type="text" placeholder="Обязательное поле" value={comment} onChange={e => setComment(e.target.value)} />
        </div>
      )}

      {selectedOp && (
        <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting} style={{ marginTop: 8 }}>
          {submitting ? "⏳ Обработка..." : "✅ Провести операцию"}
        </button>
      )}
    </div>
  )
}

import { useEffect, useState } from 'react'
import client from '../api/client'
import Loader from '../components/Loader'
import Toast from '../components/Toast'

const tg = window.Telegram?.WebApp

const OPERATIONS = [
  { type: 'zakup',       icon: '🛒', label: 'Закуп',            needsIp: true,  needsUser: false, needsComment: false },
  { type: 'storonnie',   icon: '💸', label: 'Посторонние траты', needsIp: false, needsUser: false, needsComment: true  },
  { type: 'prihod_mes',  icon: '📥', label: 'Приход ежемес.',   needsIp: false, needsUser: false, needsComment: false },
  { type: 'prihod_fast', icon: '⚡', label: 'Приход быстрый',   needsIp: false, needsUser: false, needsComment: false },
  { type: 'prihod_sto',  icon: '🏦', label: 'Приход сторонний', needsIp: false, needsUser: false, needsComment: true  },
  { type: 'snyat_rs',    icon: '💴', label: 'Снять с Р/С',      needsIp: true,  needsUser: false, needsComment: false },
  { type: 'vnesti_rs',   icon: '🏛',  label: 'Внести на Р/С',    needsIp: true,  needsUser: false, needsComment: false },
  { type: 'odolzhit',    icon: '🤝', label: 'Одолжить',         needsIp: false, needsUser: true,  needsComment: false },
]

function fmt(n) {
  return new Intl.NumberFormat('ru-RU').format(n) + ' ₽'
}

export default function AddOperation({ setPage }) {
  const [ips, setIps] = useState([])
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [toast, setToast] = useState(null)

  const [selectedOp, setSelectedOp] = useState(null)
  const [selectedIp, setSelectedIp] = useState('')
  const [selectedUser, setSelectedUser] = useState('')
  const [amount, setAmount] = useState('')
  const [comment, setComment] = useState('')

  useEffect(() => {
    Promise.all([
      client.get('/balance'),
      client.get('/users').catch(() => ({ data: [] })),
    ]).then(([balRes, usersRes]) => {
      setIps(balRes.data.ips || [])
      setUsers(Array.isArray(usersRes.data) ? usersRes.data : [])
    }).finally(() => setLoading(false))
  }, [])

  const op = OPERATIONS.find(o => o.type === selectedOp)

  const handleSubmit = async () => {
    if (!selectedOp) return setToast('Выберите тип операции')
    const amt = parseInt(amount, 10)
    if (!amt || amt <= 0) return setToast('Введите корректную сумму')
    if (op?.needsIp && !selectedIp) return setToast('Выберите ИП')
    if (op?.needsUser && !selectedUser) return setToast('Выберите получателя')
    if (op?.needsComment && !comment.trim()) return setToast('Введите комментарий')

    setSubmitting(true)
    try {
      const res = await client.post('/operations', {
        op_type: selectedOp,
        amount: amt,
        ip_id: selectedIp ? parseInt(selectedIp) : null,
        target_user_id: selectedUser ? parseInt(selectedUser) : null,
        comment: comment.trim() || null,
      })
      tg?.HapticFeedback?.notificationOccurred('success')
      setToast(`✅ Готово! Баланс: ${fmt(res.data.new_balance)}`)
      // Сбрасываем форму
      setSelectedOp(null); setSelectedIp(''); setSelectedUser(''); setAmount(''); setComment('')
    } catch (e) {
      tg?.HapticFeedback?.notificationOccurred('error')
      setToast('❌ ' + (e.response?.data?.detail || 'Ошибка'))
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="page-content"><Loader /></div>

  return (
    <div className="page-content">
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}

      <div className="page-header">➕ Операция</div>

      {/* Выбор типа */}
      <div className="section-title">Тип операции</div>
      <div className="op-grid">
        {OPERATIONS.map(o => (
          <button
            key={o.type}
            className={`op-btn ${selectedOp === o.type ? 'selected' : ''}`}
            onClick={() => { setSelectedOp(o.type); setSelectedIp(''); setSelectedUser('') }}
          >
            <span className="op-btn-icon">{o.icon}</span>
            <span className="op-btn-label">{o.label}</span>
          </button>
        ))}
      </div>

      {/* Выбор ИП */}
      {op?.needsIp && (
        <div className="input-group">
          <label className="input-label">ИП</label>
          <select className="input-field" value={selectedIp} onChange={e => setSelectedIp(e.target.value)}>
            <option value="">— Выберите ИП —</option>
            {ips.map(ip => (
              <option key={ip.id} value={ip.id}>
                {ip.name} (Р/С: {fmt(ip.bank_balance)}, Нал: {fmt(ip.cash_balance)})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Выбор получателя займа */}
      {op?.needsUser && (
        <div className="input-group">
          <label className="input-label">Кому одолжить</label>
          <select className="input-field" value={selectedUser} onChange={e => setSelectedUser(e.target.value)}>
            <option value="">— Выберите пользователя —</option>
            {users.map(u => (
              <option key={u.id} value={u.id}>{u.display_name}</option>
            ))}
          </select>
        </div>
      )}

      {/* Сумма */}
      <div className="input-group">
        <label className="input-label">Сумма (₽)</label>
        <input
          className="input-field"
          type="number"
          inputMode="numeric"
          placeholder="Например: 5000"
          value={amount}
          onChange={e => setAmount(e.target.value)}
        />
      </div>

      {/* Комментарий */}
      {op?.needsComment && (
        <div className="input-group">
          <label className="input-label">Комментарий *</label>
          <input
            className="input-field"
            type="text"
            placeholder="Обязательное поле"
            value={comment}
            onChange={e => setComment(e.target.value)}
          />
        </div>
      )}

      {/* Кнопка */}
      <button
        className="btn btn-primary"
        onClick={handleSubmit}
        disabled={submitting}
        style={{ marginTop: 8 }}
      >
        {submitting ? '⏳ Обработка...' : '✅ Провести операцию'}
      </button>
    </div>
  )
}

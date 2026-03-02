import { useEffect, useState } from 'react'
import client from '../api/client'
import Loader from '../components/Loader'
import Toast from '../components/Toast'

const TX_ICONS = {
  zakup:           '🛒',
  storonnie:       '💸',
  prihod_mes:      '📥',
  prihod_fast:     '⚡',
  prihod_sto:      '🏦',
  snyat_rs:        '💴',
  snyat_debit:     '💵',
  vnesti_rs:       '🏛',
  odolzhit:        '🤝',
  pogasit:         '✅',
  expense_writeoff:'💰',
}

const PLUS_TYPES  = new Set(['prihod_mes', 'prihod_fast', 'prihod_sto', 'pogasit'])
const MINUS_TYPES = new Set(['zakup', 'storonnie', 'vnesti_rs', 'odolzhit', 'expense_writeoff'])

function fmt(n) {
  return new Intl.NumberFormat('ru-RU').format(n) + ' ₽'
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function EditModal({ tx, onClose, onSaved }) {
  const [amount, setAmount] = useState(String(tx.amount))
  const [comment, setComment] = useState(tx.comment || '')
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  const handleSave = async () => {
    const amt = parseInt(amount, 10)
    if (!amt || amt <= 0) return setToast('Введите корректную сумму')
    setLoading(true)
    try {
      const res = await client.patch('/operations/' + tx.id, { amount: amt, comment: comment.trim() || null })
      onSaved(res.data)
    } catch (e) {
      setToast('Ошибка: ' + (e.response?.data?.detail || 'неизвестная'))
      setLoading(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.6)', display: 'flex', alignItems: 'flex-end', zIndex: 200 }}>
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      <div style={{ background: 'var(--bg)', borderRadius: '20px 20px 0 0', padding: '24px 16px', width: '100%' }}>
        <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 4 }}>Редактировать операцию</div>
        <div style={{ color: 'var(--hint)', fontSize: 13, marginBottom: 16 }}>{tx.type_label}</div>
        <div className="input-group">
          <label className="input-label">Сумма (₽)</label>
          <input className="input-field" type="number" inputMode="numeric" value={amount} onChange={e => setAmount(e.target.value)} />
        </div>
        <div className="input-group">
          <label className="input-label">Комментарий</label>
          <input className="input-field" type="text" placeholder="Необязательно" value={comment} onChange={e => setComment(e.target.value)} />
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

function CancelModal({ tx, onClose, onCancelled }) {
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  const handleCancel = async () => {
    setLoading(true)
    try {
      await client.post('/operations/' + tx.id + '/cancel')
      onCancelled()
    } catch (e) {
      setToast('Ошибка: ' + (e.response?.data?.detail || 'неизвестная'))
      setLoading(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.6)', display: 'flex', alignItems: 'flex-end', zIndex: 200 }}>
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      <div style={{ background: 'var(--bg)', borderRadius: '20px 20px 0 0', padding: '24px 16px', width: '100%' }}>
        <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 8, color: '#ff4444' }}>Отменить операцию?</div>
        <div style={{ color: 'var(--hint)', fontSize: 14, marginBottom: 16 }}>
          {tx.type_label} — {fmt(tx.amount)}<br />
          Баланс ИП будет восстановлен. Это действие нельзя отменить.
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={onClose} style={{ flex: 1 }}>Не отменять</button>
          <button
            className="btn"
            onClick={handleCancel}
            disabled={loading}
            style={{ flex: 1, background: '#ff4444', color: '#fff' }}
          >
            {loading ? 'Отмена...' : 'Да, отменить'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function History({ user }) {
  const [txs, setTxs] = useState([])
  const [ips, setIps] = useState([])
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [toast, setToast] = useState(null)

  const [ipFilter, setIpFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [showCancelled, setShowCancelled] = useState(false)

  const [editingTx, setEditingTx] = useState(null)
  const [cancellingTx, setCancellingTx] = useState(null)

  const isAdmin = user?.role === 'admin'
  const canDownload = user?.role === 'user' || user?.role === 'admin'

  useEffect(() => {
    client.get('/balance')
      .then(r => setIps(r.data.ips || []))
      .catch(console.error)
  }, [])

  const loadTxs = () => {
    setLoading(true)
    const params = new URLSearchParams({ limit: 500 })
    if (ipFilter) params.append('ip_id', ipFilter)
    if (showCancelled) params.append('include_cancelled', 'true')
    client.get('/transactions?' + params.toString())
      .then(r => setTxs(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadTxs() }, [ipFilter, showCancelled])

  const handleDownload = async () => {
    if (!ipFilter) return setToast('Выберите ИП для выгрузки')
    setDownloading(true)
    try {
      const params = new URLSearchParams({ ip_id: ipFilter })
      if (dateFrom) params.append('date_from', dateFrom)
      if (dateTo) params.append('date_to', dateTo)
      const resp = await client.get('/export?' + params.toString(), { responseType: 'blob' })
      const url = URL.createObjectURL(resp.data)
      const a = document.createElement('a')
      a.href = url
      const ipName = ips.find(ip => String(ip.id) === ipFilter)?.name || ipFilter
      a.download = ipName + '_' + (dateFrom || 'all') + '.xlsx'
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setToast('Ошибка при выгрузке')
    } finally {
      setDownloading(false)
    }
  }

  // Клиентская фильтрация по датам
  const filteredTxs = txs.filter(tx => {
    const d = tx.created_at.slice(0, 10)
    if (dateFrom && d < dateFrom) return false
    if (dateTo && d > dateTo) return false
    return true
  })

  return (
    <div className="page-content">
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      {editingTx && (
        <EditModal
          tx={editingTx}
          onClose={() => setEditingTx(null)}
          onSaved={(updated) => {
            setTxs(prev => prev.map(t => t.id === editingTx.id ? { ...t, amount: updated.amount, comment: updated.comment } : t))
            setEditingTx(null)
            setToast('✅ Операция обновлена')
          }}
        />
      )}
      {cancellingTx && (
        <CancelModal
          tx={cancellingTx}
          onClose={() => setCancellingTx(null)}
          onCancelled={() => {
            setCancellingTx(null)
            setToast('✅ Операция отменена')
            loadTxs()
          }}
        />
      )}

      <div className="page-header">📋 История</div>

      {/* Фильтры */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 12 }}>
        <select
          className="input-field"
          value={ipFilter}
          onChange={e => setIpFilter(e.target.value)}
          style={{ marginBottom: 0 }}
        >
          <option value="">— Все ИП —</option>
          {ips.map(ip => (
            <option key={ip.id} value={ip.id}>{ip.name}</option>
          ))}
        </select>

        <div style={{ display: 'flex', gap: 8 }}>
          <div style={{ flex: 1 }}>
            <label className="input-label" style={{ fontSize: 11 }}>С даты</label>
            <input
              className="input-field"
              type="date"
              value={dateFrom}
              onChange={e => setDateFrom(e.target.value)}
              style={{ marginBottom: 0 }}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label className="input-label" style={{ fontSize: 11 }}>По дату</label>
            <input
              className="input-field"
              type="date"
              value={dateTo}
              onChange={e => setDateTo(e.target.value)}
              style={{ marginBottom: 0 }}
            />
          </div>
        </div>

        {isAdmin && (
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--hint)', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showCancelled}
              onChange={e => setShowCancelled(e.target.checked)}
            />
            Показать отменённые
          </label>
        )}

        {canDownload && (
          <button
            className="btn btn-primary"
            onClick={handleDownload}
            disabled={downloading || !ipFilter}
            style={{ opacity: !ipFilter ? 0.5 : 1 }}
          >
            {downloading ? '⏳ Формируем...' : '⬇ Скачать Excel'}
          </button>
        )}
      </div>

      {loading ? (
        <Loader />
      ) : filteredTxs.length === 0 ? (
        <div className="card text-center"><div className="hint">Нет операций</div></div>
      ) : (
        <div className="tx-list">
          {filteredTxs.map(tx => {
            const isPlus  = PLUS_TYPES.has(tx.type)
            const isMinus = MINUS_TYPES.has(tx.type)
            const cls = tx.is_cancelled ? 'cancelled' : isPlus ? 'plus' : isMinus ? 'minus' : 'neutral'
            const sign = isPlus ? '+' : isMinus ? '-' : ''
            const meta = [
              tx.ip_name,
              tx.user_name,
              tx.comment,
              formatDate(tx.created_at),
            ].filter(Boolean).join(' • ')
            return (
              <div key={tx.id} className={'tx-item' + (tx.is_cancelled ? ' cancelled' : '')}>
                <div className="tx-icon">{TX_ICONS[tx.type] || '💰'}</div>
                <div className="tx-info" style={{ flex: 1 }}>
                  <div className="tx-type">
                    {tx.type_label}
                    {tx.is_cancelled && <span style={{ marginLeft: 6, fontSize: 11, color: '#ff4444' }}>отменено</span>}
                  </div>
                  <div className="tx-meta">{meta}</div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
                  <div className={'tx-amount ' + cls}>{sign}{fmt(tx.amount)}</div>
                  {isAdmin && !tx.is_cancelled && (
                    <div style={{ display: 'flex', gap: 4 }}>
                      <button
                        style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 16, padding: '0 4px' }}
                        onClick={() => setEditingTx(tx)}
                        title="Редактировать"
                      >✏️</button>
                      <button
                        style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 16, padding: '0 4px' }}
                        onClick={() => setCancellingTx(tx)}
                        title="Отменить"
                      >🗑</button>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

import { useEffect, useState } from 'react'
import client from '../api/client'
import Loader from '../components/Loader'
import Toast from '../components/Toast'

const TX_ICONS = {
  zakup:       '🛒',
  storonnie:   '💸',
  prihod_mes:  '📥',
  prihod_fast: '⚡',
  prihod_sto:  '🏦',
  snyat_rs:    '💴',
  snyat_debit: '💵',
  vnesti_rs:   '🏛',
  odolzhit:    '🤝',
  pogasit:     '✅',
}

const PLUS_TYPES  = new Set(['prihod_mes', 'prihod_fast', 'prihod_sto', 'pogasit'])
const MINUS_TYPES = new Set(['zakup', 'storonnie', 'vnesti_rs', 'odolzhit'])

function fmt(n) {
  return new Intl.NumberFormat('ru-RU').format(n) + ' ₽'
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
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

  useEffect(() => {
    client.get('/balance')
      .then(r => setIps(r.data.ips || []))
      .catch(console.error)
  }, [])

  useEffect(() => {
    setLoading(true)
    const params = new URLSearchParams({ limit: 500 })
    if (ipFilter) params.append('ip_id', ipFilter)
    client.get('/transactions?' + params.toString())
      .then(r => setTxs(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [ipFilter])

  const canDownload = user?.role === 'user' || user?.role === 'admin'

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
            const cls = isPlus ? 'plus' : isMinus ? 'minus' : 'neutral'
            const sign = isPlus ? '+' : isMinus ? '-' : ''
            const meta = [
              tx.ip_name,
              tx.user_name,
              tx.comment,
              formatDate(tx.created_at),
            ].filter(Boolean).join(' • ')
            return (
              <div key={tx.id} className="tx-item">
                <div className="tx-icon">{TX_ICONS[tx.type] || '💰'}</div>
                <div className="tx-info">
                  <div className="tx-type">{tx.type_label}</div>
                  <div className="tx-meta">{meta}</div>
                </div>
                <div className={`tx-amount ${cls}`}>{sign}{fmt(tx.amount)}</div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

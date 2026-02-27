import { useEffect, useState } from 'react'
import client from '../api/client'
import Loader from '../components/Loader'

const TX_ICONS = {
  zakup:       '🛒',
  storonnie:   '💸',
  prihod_mes:  '📥',
  prihod_fast: '⚡',
  prihod_sto:  '🏦',
  snyat_rs:    '💴',
  vnesti_rs:   '🏛',
  odolzhit:    '🤝',
  pogasit:     '✅',
}

const PLUS_TYPES  = new Set(['prihod_mes', 'prihod_fast', 'prihod_sto', 'snyat_rs', 'pogasit'])
const MINUS_TYPES = new Set(['zakup', 'storonnie', 'vnesti_rs', 'odolzhit'])

function fmt(n) {
  return new Intl.NumberFormat('ru-RU').format(n) + ' ₽'
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

export default function History() {
  const [txs, setTxs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    client.get('/transactions?limit=100')
      .then(r => setTxs(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="page-content"><Loader /></div>

  return (
    <div className="page-content">
      <div className="page-header">📋 История</div>

      {txs.length === 0 ? (
        <div className="card text-center"><div className="hint">Нет операций</div></div>
      ) : (
        <div className="tx-list">
          {txs.map(tx => {
            const isPlus  = PLUS_TYPES.has(tx.type)
            const isMinus = MINUS_TYPES.has(tx.type)
            const cls = isPlus ? 'plus' : isMinus ? 'minus' : 'neutral'
            const sign = isPlus ? '+' : isMinus ? '-' : ''
            return (
              <div key={tx.id} className="tx-item">
                <div className="tx-icon">{TX_ICONS[tx.type] || '💰'}</div>
                <div className="tx-info">
                  <div className="tx-type">{tx.type_label}</div>
                  <div className="tx-meta">
                    {tx.ip_name ? `${tx.ip_name} • ` : ''}
                    {tx.comment ? `${tx.comment} • ` : ''}
                    {formatDate(tx.created_at)}
                  </div>
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

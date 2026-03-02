import { useEffect, useState } from 'react'
import client from '../api/client'
import Loader from '../components/Loader'

const PERIODS = [
  { key: 'today', label: 'Сегодня' },
  { key: 'week',  label: 'Неделя'  },
  { key: 'month', label: 'Месяц'   },
  { key: 'all',   label: 'Всё время' },
]

const INCOME_ROWS = [
  { type: 'prihod_fast', icon: '⚡', label: 'Приход быстрый' },
  { type: 'prihod_mes',  icon: '📥', label: 'Приход ежемесяч.' },
  { type: 'prihod_sto',  icon: '🏦', label: 'Приход сторонний' },
]

const EXPENSE_ROWS = [
  { type: 'zakup',            icon: '🛒', label: 'Закупы' },
  { type: 'storonnie',        icon: '💸', label: 'Посторонние траты' },
  { type: 'expense_writeoff', icon: '💰', label: 'Расходы (списания)' },
]

function fmt(n) {
  return new Intl.NumberFormat('ru-RU').format(n ?? 0) + ' ₽'
}

function AnalyticsSection({ title, rows, byType, total, colorClass }) {
  return (
    <div className="card" style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ fontWeight: 700, fontSize: 15 }}>{title}</div>
        <div style={{ fontWeight: 700, fontSize: 16 }} className={'report-value ' + colorClass}>{fmt(total)}</div>
      </div>
      {rows.map(row => {
        const val = byType[row.type] || 0
        if (val === 0) return null
        return (
          <div key={row.type} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0', borderTop: '1px solid var(--border)' }}>
            <div style={{ fontSize: 14, color: 'var(--hint)' }}>{row.icon} {row.label}</div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>{fmt(val)}</div>
          </div>
        )
      })}
      {rows.every(r => !(byType[r.type])) && (
        <div style={{ fontSize: 13, color: 'var(--hint)', textAlign: 'center' }}>Нет данных</div>
      )}
    </div>
  )
}

export default function Analytics() {
  const [period, setPeriod] = useState('month')
  const [ipId, setIpId] = useState('')
  const [ips, setIps] = useState([])
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    client.get('/balance').then(r => setIps(r.data.ips || [])).catch(console.error)
  }, [])

  useEffect(() => {
    setLoading(true)
    const params = new URLSearchParams({ period })
    if (ipId) params.append('ip_id', ipId)
    client.get('/analytics?' + params.toString())
      .then(r => setData(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [period, ipId])

  return (
    <div className="page-content">
      <div className="page-header">📈 Аналитика</div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <select
          className="input-field"
          value={ipId}
          onChange={e => setIpId(e.target.value)}
          style={{ marginBottom: 0, flex: 1 }}
        >
          <option value="">— Все ИП —</option>
          {ips.map(ip => (
            <option key={ip.id} value={ip.id}>{ip.name}</option>
          ))}
        </select>
      </div>

      <div className="period-tabs" style={{ marginBottom: 12 }}>
        {PERIODS.map(p => (
          <button
            key={p.key}
            className={'period-tab ' + (period === p.key ? 'active' : '')}
            onClick={() => setPeriod(p.key)}
          >
            {p.label}
          </button>
        ))}
      </div>

      {loading ? <Loader /> : data && (
        <>
          <AnalyticsSection
            title="📈 Поступления"
            rows={INCOME_ROWS}
            byType={data.by_type}
            total={data.total_income}
            colorClass="green"
          />
          <AnalyticsSection
            title="📉 Траты"
            rows={EXPENSE_ROWS}
            byType={data.by_type}
            total={data.total_expense}
            colorClass="red"
          />
        </>
      )}
    </div>
  )
}

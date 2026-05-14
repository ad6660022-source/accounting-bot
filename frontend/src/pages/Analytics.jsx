import { useEffect, useState } from 'react'
import client from '../api/client'
import Loader from '../components/Loader'

const tg = window.Telegram?.WebApp

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

function fmtShort(n) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'М'
  if (n >= 1_000) return (n / 1_000).toFixed(0) + 'К'
  return String(n)
}

// ── Summary bar chart: income vs expense ─────────────────────────────────────

function SummaryChart({ totalIncome, totalExpense }) {
  const max = Math.max(totalIncome, totalExpense, 1)
  const incPct = Math.round((totalIncome / max) * 100)
  const expPct = Math.round((totalExpense / max) * 100)
  const profit = totalIncome - totalExpense

  return (
    <div className="card" style={{ marginBottom: 12 }}>
      <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 12 }}>📊 Сводка</div>

      <div style={{ marginBottom: 8 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
          <span style={{ color: 'var(--hint)' }}>Поступления</span>
          <span style={{ fontWeight: 600, color: '#34c759' }}>{fmt(totalIncome)}</span>
        </div>
        <div style={{ background: 'var(--bg)', borderRadius: 4, height: 10, overflow: 'hidden' }}>
          <div style={{ width: incPct + '%', height: '100%', background: '#34c759', borderRadius: 4, transition: 'width .4s' }} />
        </div>
      </div>

      <div style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
          <span style={{ color: 'var(--hint)' }}>Расходы</span>
          <span style={{ fontWeight: 600, color: '#ff3b30' }}>{fmt(totalExpense)}</span>
        </div>
        <div style={{ background: 'var(--bg)', borderRadius: 4, height: 10, overflow: 'hidden' }}>
          <div style={{ width: expPct + '%', height: '100%', background: '#ff3b30', borderRadius: 4, transition: 'width .4s' }} />
        </div>
      </div>

      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        borderTop: '1px solid var(--border)', paddingTop: 10,
      }}>
        <span style={{ fontSize: 14, fontWeight: 600 }}>Прибыль</span>
        <span style={{ fontSize: 16, fontWeight: 700, color: profit >= 0 ? '#34c759' : '#ff3b30' }}>{fmt(profit)}</span>
      </div>
    </div>
  )
}

// ── Breakdown bar chart ───────────────────────────────────────────────────────

function BreakdownChart({ rows, byType, color }) {
  const values = rows.map(r => byType[r.type] || 0)
  const max = Math.max(...values, 1)
  const hasData = values.some(v => v > 0)
  if (!hasData) return null

  return (
    <div style={{ marginTop: 12 }}>
      {rows.map((row, i) => {
        const val = values[i]
        if (!val) return null
        const pct = Math.round((val / max) * 100)
        return (
          <div key={row.type} style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 3 }}>
              <span style={{ color: 'var(--hint)' }}>{row.icon} {row.label}</span>
              <span style={{ fontWeight: 600 }}>{fmtShort(val)}</span>
            </div>
            <div style={{ background: 'var(--bg)', borderRadius: 3, height: 6, overflow: 'hidden' }}>
              <div style={{ width: pct + '%', height: '100%', background: color, borderRadius: 3, transition: 'width .4s' }} />
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── Section with breakdown ────────────────────────────────────────────────────

function AnalyticsSection({ title, rows, byType, total, colorClass, barColor }) {
  return (
    <div className="card" style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
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
      <BreakdownChart rows={rows} byType={byType} color={barColor} />
    </div>
  )
}

export default function Analytics() {
  const [period, setPeriod] = useState('month')
  const [ipId, setIpId] = useState('')
  const [ips, setIps] = useState([])
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)

  const handleExport = async () => {
    setExporting(true)
    try {
      const initData = tg?.initData || ''
      const url = '/api/export/workspace'
      const resp = await fetch(url, { headers: { 'X-Init-Data': initData } })
      if (!resp.ok) throw new Error('Ошибка экспорта')
      const blob = await resp.blob()
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      const cd = resp.headers.get('Content-Disposition') || ''
      const match = cd.match(/filename\*=UTF-8''(.+)/)
      link.download = match ? decodeURIComponent(match[1]) : 'report.xlsx'
      link.click()
      URL.revokeObjectURL(link.href)
    } catch {
      // ignore
    } finally {
      setExporting(false)
    }
  }

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

      <button
        className="btn btn-secondary"
        onClick={handleExport}
        disabled={exporting}
        style={{ marginBottom: 16, fontSize: 14 }}
      >
        {exporting ? '⏳ Формируем...' : '📥 Экспорт в Excel'}
      </button>

      {loading ? <Loader /> : data && (
        <>
          <SummaryChart totalIncome={data.total_income} totalExpense={data.total_expense} />
          <AnalyticsSection
            title="📈 Поступления"
            rows={INCOME_ROWS}
            byType={data.by_type}
            total={data.total_income}
            colorClass="green"
            barColor="#34c759"
          />
          <AnalyticsSection
            title="📉 Траты"
            rows={EXPENSE_ROWS}
            byType={data.by_type}
            total={data.total_expense}
            colorClass="red"
            barColor="#ff3b30"
          />
        </>
      )}
    </div>
  )
}

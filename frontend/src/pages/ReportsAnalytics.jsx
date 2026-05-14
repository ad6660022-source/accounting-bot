import { useEffect, useState } from 'react'
import client from '../api/client'
import Loader from '../components/Loader'
import Toast from '../components/Toast'

// ── Общие ─────────────────────────────────────────────────────────────────────
const PERIODS = [
  { key: 'today', label: 'Сегодня' },
  { key: 'week',  label: 'Неделя'  },
  { key: 'month', label: 'Месяц'   },
  { key: 'all',   label: 'Всё время' },
]

function fmt(n) {
  return new Intl.NumberFormat('ru-RU').format(n ?? 0) + ' ₽'
}

function fmtShort(n) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'М'
  if (n >= 1_000) return (n / 1_000).toFixed(0) + 'К'
  return String(n)
}

function PeriodTabs({ period, setPeriod }) {
  return (
    <div className="period-tabs" style={{ marginBottom: 12 }}>
      {PERIODS.map(p => (
        <button key={p.key} className={'period-tab ' + (period === p.key ? 'active' : '')} onClick={() => setPeriod(p.key)}>
          {p.label}
        </button>
      ))}
    </div>
  )
}

// ── Вкладка: Сводка ───────────────────────────────────────────────────────────
function TabReport() {
  const [period, setPeriod] = useState('all')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    setLoading(true)
    client.get('/report/' + period).then(r => setData(r.data)).catch(console.error).finally(() => setLoading(false))
  }, [period])

  const handleSend = async () => {
    setSending(true)
    try {
      await client.post('/summary/send')
      setToast('✅ Сводка отправлена в Telegram!')
    } catch {
      setToast('❌ Ошибка отправки')
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      <PeriodTabs period={period} setPeriod={setPeriod} />

      <button className="btn btn-secondary" onClick={handleSend} disabled={sending} style={{ marginBottom: 12, fontSize: 14 }}>
        {sending ? '⏳ Отправка...' : '📤 Отправить в Telegram'}
      </button>

      {loading ? <Loader /> : data && (
        <>
          <div className="report-grid">
            <div className="report-card">
              <div className="report-label">📥 Приход</div>
              <div className="report-value green">+{fmt(data.income)}</div>
            </div>
            <div className="report-card">
              <div className="report-label">📤 Расход</div>
              <div className="report-value red">-{fmt(data.expense)}</div>
            </div>
          </div>

          {data.ips?.length > 0 && (
            <>
              <div className="section-title">🏦 Балансы ИП</div>
              <div className="ip-cards">
                {data.ips.map(ip => (
                  <div key={ip.id} className="ip-card">
                    <div className="ip-name">{ip.name}</div>
                    <div className="ip-row"><span className="ip-label">Р/С</span><span className="ip-val">{fmt(ip.bank_balance)}</span></div>
                    <div className="ip-row"><span className="ip-label">Дебет</span><span className="ip-val">{fmt(ip.debit_balance)}</span></div>
                    <div className="ip-row"><span className="ip-label">Нал</span><span className="ip-val">{fmt(ip.cash_balance)}</span></div>
                  </div>
                ))}
              </div>
            </>
          )}

          {data.ip_debts?.length > 0 && (
            <>
              <div className="section-title">🔴 Долги между ИП</div>
              {data.ip_debts.map((d, i) => (
                <div key={i} className="debt-item" style={{ pointerEvents: 'none' }}>
                  <div className="debt-info">
                    <div className="debt-name">{d.debtor_ip_name} → {d.creditor_ip_name}</div>
                    <div className="debt-amount">{fmt(d.amount)}</div>
                  </div>
                </div>
              ))}
            </>
          )}
        </>
      )}
    </>
  )
}

// ── Графики аналитики ─────────────────────────────────────────────────────────
const INCOME_ROWS  = [
  { type: 'prihod_fast', icon: '⚡', label: 'Приход быстрый' },
  { type: 'prihod_mes',  icon: '📥', label: 'Приход ежемесяч.' },
  { type: 'prihod_sto',  icon: '🏦', label: 'Приход сторонний' },
]
const EXPENSE_ROWS = [
  { type: 'zakup',            icon: '🛒', label: 'Закупы' },
  { type: 'storonnie',        icon: '💸', label: 'Посторонние траты' },
  { type: 'expense_writeoff', icon: '💰', label: 'Расходы (списания)' },
]

function BarRow({ label, icon, value, maxVal, color }) {
  const pct = maxVal > 0 ? Math.round((value / maxVal) * 100) : 0
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 3 }}>
        <span style={{ color: 'var(--hint)' }}>{icon} {label}</span>
        <span style={{ fontWeight: 600 }}>{fmtShort(value)}</span>
      </div>
      <div style={{ background: 'var(--bg)', borderRadius: 3, height: 6, overflow: 'hidden' }}>
        <div style={{ width: pct + '%', height: '100%', background: color, borderRadius: 3, transition: 'width .4s' }} />
      </div>
    </div>
  )
}

function SummaryChart({ totalIncome, totalExpense }) {
  const max = Math.max(totalIncome, totalExpense, 1)
  const profit = totalIncome - totalExpense
  return (
    <div className="card" style={{ marginBottom: 12 }}>
      <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 12 }}>📊 Итог</div>
      <div style={{ marginBottom: 8 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
          <span style={{ color: 'var(--hint)' }}>Поступления</span>
          <span style={{ fontWeight: 600, color: '#34c759' }}>{fmt(totalIncome)}</span>
        </div>
        <div style={{ background: 'var(--bg)', borderRadius: 4, height: 10, overflow: 'hidden' }}>
          <div style={{ width: Math.round(totalIncome / max * 100) + '%', height: '100%', background: '#34c759', borderRadius: 4, transition: 'width .4s' }} />
        </div>
      </div>
      <div style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
          <span style={{ color: 'var(--hint)' }}>Расходы</span>
          <span style={{ fontWeight: 600, color: '#ff3b30' }}>{fmt(totalExpense)}</span>
        </div>
        <div style={{ background: 'var(--bg)', borderRadius: 4, height: 10, overflow: 'hidden' }}>
          <div style={{ width: Math.round(totalExpense / max * 100) + '%', height: '100%', background: '#ff3b30', borderRadius: 4, transition: 'width .4s' }} />
        </div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--separator)', paddingTop: 10 }}>
        <span style={{ fontSize: 14, fontWeight: 600 }}>Прибыль</span>
        <span style={{ fontSize: 16, fontWeight: 700, color: profit >= 0 ? '#34c759' : '#ff3b30' }}>{fmt(profit)}</span>
      </div>
    </div>
  )
}

// ── Вкладка: Аналитика ────────────────────────────────────────────────────────
const tg = window.Telegram?.WebApp

function TabAnalytics() {
  const [period, setPeriod] = useState('month')
  const [ipId, setIpId]     = useState('')
  const [ips, setIps]       = useState([])
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    client.get('/balance').then(r => setIps(r.data.ips || [])).catch(console.error)
  }, [])

  useEffect(() => {
    setLoading(true)
    const p = new URLSearchParams({ period })
    if (ipId) p.append('ip_id', ipId)
    client.get('/analytics?' + p).then(r => setData(r.data)).catch(console.error).finally(() => setLoading(false))
  }, [period, ipId])

  const handleExport = async () => {
    setExporting(true)
    try {
      const resp = await fetch('/api/export/workspace', { headers: { 'X-Init-Data': tg?.initData || '' } })
      if (!resp.ok) throw new Error()
      const blob = await resp.blob()
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      const cd = resp.headers.get('Content-Disposition') || ''
      const m = cd.match(/filename\*=UTF-8''(.+)/)
      link.download = m ? decodeURIComponent(m[1]) : 'report.xlsx'
      link.click()
      URL.revokeObjectURL(link.href)
    } catch { /* ignore */ }
    finally { setExporting(false) }
  }

  return (
    <>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <select className="input-field" value={ipId} onChange={e => setIpId(e.target.value)} style={{ marginBottom: 0, flex: 1 }}>
          <option value="">— Все ИП —</option>
          {ips.map(ip => <option key={ip.id} value={ip.id}>{ip.name}</option>)}
        </select>
      </div>

      <PeriodTabs period={period} setPeriod={setPeriod} />

      <button className="btn btn-secondary" onClick={handleExport} disabled={exporting} style={{ marginBottom: 12, fontSize: 14 }}>
        {exporting ? '⏳ Формируем...' : '📥 Экспорт в Excel'}
      </button>

      {loading ? <Loader /> : data && (
        <>
          <SummaryChart totalIncome={data.total_income} totalExpense={data.total_expense} />

          <div className="card" style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <div style={{ fontWeight: 700, fontSize: 15 }}>📈 Поступления</div>
              <div style={{ fontWeight: 700, color: '#34c759' }}>{fmt(data.total_income)}</div>
            </div>
            {INCOME_ROWS.map(r => {
              const v = data.by_type[r.type] || 0
              if (!v) return null
              return <BarRow key={r.type} {...r} value={v} maxVal={data.total_income} color="#34c759" />
            })}
            {INCOME_ROWS.every(r => !data.by_type[r.type]) && <div style={{ fontSize: 13, color: 'var(--hint)', textAlign: 'center' }}>Нет данных</div>}
          </div>

          <div className="card" style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <div style={{ fontWeight: 700, fontSize: 15 }}>📉 Расходы</div>
              <div style={{ fontWeight: 700, color: '#ff3b30' }}>{fmt(data.total_expense)}</div>
            </div>
            {EXPENSE_ROWS.map(r => {
              const v = data.by_type[r.type] || 0
              if (!v) return null
              return <BarRow key={r.type} {...r} value={v} maxVal={data.total_expense} color="#ff3b30" />
            })}
            {EXPENSE_ROWS.every(r => !data.by_type[r.type]) && <div style={{ fontSize: 13, color: 'var(--hint)', textAlign: 'center' }}>Нет данных</div>}
          </div>
        </>
      )}
    </>
  )
}

// ── Главная страница ──────────────────────────────────────────────────────────
export default function ReportsAnalytics() {
  const [tab, setTab] = useState('report')

  return (
    <div className="page-content">
      <div className="page-header">📊 Отчёты</div>

      {/* Сегментированный контрол */}
      <div style={{
        display: 'flex', background: 'var(--bg3)', borderRadius: 10,
        padding: 3, marginBottom: 16, gap: 2,
      }}>
        {[['report', '📊 Сводка'], ['analytics', '📈 Аналитика']].map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            style={{
              flex: 1, border: 'none', borderRadius: 8, padding: '8px 0',
              fontSize: 13, fontWeight: 600, cursor: 'pointer',
              transition: 'all .15s',
              background: tab === key ? 'var(--bg2)' : 'transparent',
              color: tab === key ? 'var(--text)' : 'var(--hint)',
              boxShadow: tab === key ? 'var(--shadow-sm)' : 'none',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'report'    && <TabReport />}
      {tab === 'analytics' && <TabAnalytics />}
    </div>
  )
}

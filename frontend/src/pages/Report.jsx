import { useEffect, useState } from 'react'
import client from '../api/client'
import Loader from '../components/Loader'

const PERIODS = [
  { key: 'today', label: 'Сегодня' },
  { key: 'week',  label: 'Неделя'  },
  { key: 'month', label: 'Месяц'   },
  { key: 'all',   label: 'Всё время' },
]

function fmt(n) {
  return new Intl.NumberFormat('ru-RU').format(n ?? 0) + ' ₽'
}

export default function Report() {
  const [period, setPeriod] = useState('all')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    client.get(`/report/${period}`)
      .then(r => setData(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [period])

  return (
    <div className="page-content">
      <div className="page-header">📊 Сводка</div>

      <div className="period-tabs">
        {PERIODS.map(p => (
          <button
            key={p.key}
            className={`period-tab ${period === p.key ? 'active' : ''}`}
            onClick={() => setPeriod(p.key)}
          >
            {p.label}
          </button>
        ))}
      </div>

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
                    <div className="ip-row">
                      <span className="ip-label">Р/С</span>
                      <span className="ip-val">{fmt(ip.bank_balance)}</span>
                    </div>
                    <div className="ip-row">
                      <span className="ip-label">Дебет</span>
                      <span className="ip-val">{fmt(ip.debit_balance)}</span>
                    </div>
                    <div className="ip-row">
                      <span className="ip-label">Нал</span>
                      <span className="ip-val">{fmt(ip.cash_balance)}</span>
                    </div>
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
    </div>
  )
}

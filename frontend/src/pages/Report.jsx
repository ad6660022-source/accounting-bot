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
  return new Intl.NumberFormat('ru-RU').format(n) + ' ₽'
}

export default function Report() {
  const [period, setPeriod] = useState('month')
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

      {/* Выбор периода */}
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
          {/* Приход / Расход */}
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

          {/* Личный баланс */}
          <div className="card" style={{ background: 'var(--btn)', color: 'var(--btn-text)' }}>
            <div style={{ fontSize: 12, opacity: .8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: .5 }}>
              💳 Ваши наличные
            </div>
            <div style={{ fontSize: 28, fontWeight: 800, marginTop: 4 }}>
              {fmt(data.user_cash)}
            </div>
          </div>

          {/* Балансы ИП */}
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
                      <span className="ip-label">Нал</span>
                      <span className="ip-val">{fmt(ip.cash_balance)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Долги */}
          <div className="section-title">💰 Долги</div>
          <div className="report-grid">
            <div className="report-card">
              <div className="report-label">Вам должны</div>
              <div className="report-value green">{fmt(data.total_owed_to_me)}</div>
            </div>
            <div className="report-card">
              <div className="report-label">Вы должны</div>
              <div className="report-value red">{fmt(data.total_i_owe)}</div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

import { useEffect, useState } from "react"
import client from "../api/client"
import Loader from "../components/Loader"

function fmt(n) {
  return new Intl.NumberFormat("ru-RU").format(n) + " ₽"
}

export default function Dashboard({ user, setPage }) {
  const [balance, setBalance] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    client.get("/balance")
      .then(r => setBalance(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="page-content"><Loader /></div>

  return (
    <div className="page-content">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 13, color: "var(--hint)" }}>Привет,</div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{user?.display_name || "Гость"}</div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {user?.role === "admin" && (
            <div style={{ background: "#ffd60a22", color: "#b8920a", fontSize: 11, fontWeight: 700, padding: "4px 10px", borderRadius: 12 }}>
              👑 Админ
            </div>
          )}
          <button
            onClick={() => setPage("help")}
            style={{ background: "var(--bg3)", border: "none", borderRadius: "50%", width: 34, height: 34, fontSize: 17, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
            title="Помощь"
          >❓</button>
        </div>
      </div>

      <div className="card" style={{ background: "var(--btn)", color: "var(--btn-text)", borderRadius: "var(--radius)", marginBottom: 16 }}>
        <div style={{ fontSize: 12, opacity: .8, fontWeight: 600, textTransform: "uppercase", letterSpacing: .5, marginBottom: 10 }}>
          💰 Общий бюджет (все ИП)
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
          <div>
            <div style={{ fontSize: 11, opacity: .75, marginBottom: 2 }}>🏦 Р/С</div>
            <div style={{ fontSize: 18, fontWeight: 800, lineHeight: 1.1 }}>{fmt(balance?.total_bank ?? 0)}</div>
          </div>
          <div>
            <div style={{ fontSize: 11, opacity: .75, marginBottom: 2 }}>📋 Дебет</div>
            <div style={{ fontSize: 18, fontWeight: 800, lineHeight: 1.1 }}>{fmt(balance?.total_debit ?? 0)}</div>
          </div>
          <div>
            <div style={{ fontSize: 11, opacity: .75, marginBottom: 2 }}>💵 Наличные</div>
            <div style={{ fontSize: 18, fontWeight: 800, lineHeight: 1.1 }}>{fmt(balance?.total_cash ?? 0)}</div>
          </div>
        </div>
      </div>

      {balance?.ips?.length > 0 && (
        <>
          <div className="section-title">🏦 Балансы ИП</div>
          <div className="ip-cards">
            {balance.ips.map(ip => (
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

      {balance?.ips?.length === 0 && (
        <div className="card text-center">
          <div className="hint">ИП не созданы</div>
          {user?.role === "admin" && (
            <button className="btn btn-primary mt-8" onClick={() => setPage("admin")}>
              ➕ Создать ИП
            </button>
          )}
        </div>
      )}

      <div className="section-title mt-16">Быстрые действия</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        <button className="btn btn-primary" onClick={() => setPage("operation")}>➕ Операция</button>
        <button className="btn btn-secondary" onClick={() => setPage("expenses")}>💰 Расходы</button>
        <button className="btn btn-secondary" onClick={() => setPage("history")}>📋 История</button>
        <button className="btn btn-secondary" onClick={() => setPage("reports")}>📊 Отчёты</button>
      </div>
    </div>
  )
}

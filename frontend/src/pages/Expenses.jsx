import { useEffect, useState } from 'react'
import client from '../api/client'
import Loader from '../components/Loader'
import Toast from '../components/Toast'

const SOURCE_LABELS = { cash: 'Нал', bank: 'Р/С', debit: 'Дебет' }

function fmt(n) {
  return new Intl.NumberFormat('ru-RU').format(n) + ' ₽'
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit' })
}

// ── Модалка: создать расход ───────────────────────────────────────────────────

function AddExpenseModal({ onClose, onCreated }) {
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  const handleCreate = async () => {
    if (!description.trim()) return setToast('Введите описание')
    const amt = parseInt(amount, 10)
    if (!amt || amt <= 0) return setToast('Введите корректную сумму')
    setLoading(true)
    try {
      const res = await client.post('/expenses', { description: description.trim(), amount: amt })
      onCreated(res.data)
    } catch (e) {
      setToast('Ошибка: ' + (e.response?.data?.detail || 'неизвестная'))
      setLoading(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.5)', display: 'flex', alignItems: 'flex-end', zIndex: 200 }}>
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      <div style={{ background: 'var(--bg)', borderRadius: '20px 20px 0 0', padding: '24px 16px', width: '100%' }}>
        <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 16 }}>Добавить расход</div>
        <div className="input-group">
          <label className="input-label">Описание *</label>
          <input className="input-field" placeholder="Аренда, коммуналка..." value={description} onChange={e => setDescription(e.target.value)} />
        </div>
        <div className="input-group">
          <label className="input-label">Сумма (₽)</label>
          <input className="input-field" type="number" inputMode="numeric" placeholder="0" value={amount} onChange={e => setAmount(e.target.value)} />
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={onClose} style={{ flex: 1 }}>Отмена</button>
          <button className="btn btn-primary" onClick={handleCreate} disabled={loading} style={{ flex: 1 }}>
            {loading ? 'Создание...' : 'Создать'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Строка одного ИП в модалке списания ──────────────────────────────────────

function IpRow({ ip, entry, onChange }) {
  return (
    <div style={{ borderTop: '1px solid var(--bg)', paddingTop: 10, marginTop: 6 }}>
      <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 6 }}>{ip.name}</div>
      <div style={{ display: 'flex', gap: 8 }}>
        <input
          className="input-field"
          type="number"
          inputMode="numeric"
          placeholder="Сумма"
          value={entry.amount}
          onChange={e => onChange({ ...entry, amount: e.target.value })}
          style={{ flex: 1, marginBottom: 0 }}
        />
        <div style={{ display: 'flex', gap: 4 }}>
          {['cash', 'bank', 'debit'].map(s => (
            <button
              key={s}
              className={'btn ' + (entry.source === s ? 'btn-primary' : 'btn-secondary')}
              style={{ padding: '0 10px', fontSize: 12 }}
              onClick={() => onChange({ ...entry, source: s })}
            >
              {SOURCE_LABELS[s]}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── Модалка: списать расход ───────────────────────────────────────────────────

function WriteOffModal({ expense, ips, alreadyWrittenOff, onClose, onDone }) {
  const [entries, setEntries] = useState(
    Object.fromEntries(ips.map(ip => [ip.id, { amount: '', source: 'cash' }]))
  )
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  const remaining = expense.amount - alreadyWrittenOff
  const totalNew = ips.reduce((sum, ip) => sum + (parseInt(entries[ip.id]?.amount, 10) || 0), 0)

  const handleWriteOff = async () => {
    const toPost = ips
      .map(ip => ({ ip_id: ip.id, amount: parseInt(entries[ip.id]?.amount, 10) || 0, source: entries[ip.id]?.source || 'cash' }))
      .filter(e => e.amount > 0)

    if (toPost.length === 0) return setToast('Введите сумму хотя бы для одного ИП')
    if (totalNew > remaining && remaining > 0) {
      return setToast('Сумма списания (' + fmt(totalNew) + ') превышает остаток (' + fmt(remaining) + ')')
    }

    setLoading(true)
    try {
      await Promise.all(
        toPost.map(e => client.post('/expenses/' + expense.id + '/writeoffs', e))
      )
      onDone()
    } catch (e) {
      setToast('Ошибка: ' + (e.response?.data?.detail || 'неизвестная'))
      setLoading(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.5)', display: 'flex', alignItems: 'flex-end', zIndex: 200 }}>
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      <div style={{ background: 'var(--bg)', borderRadius: '20px 20px 0 0', padding: '24px 16px', width: '100%', maxHeight: '85vh', overflowY: 'auto' }}>
        <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 2 }}>Списать расход</div>
        <div style={{ color: 'var(--hint)', fontSize: 13, marginBottom: 4 }}>{expense.description}</div>
        <div style={{ display: 'flex', gap: 12, marginBottom: 12, fontSize: 13 }}>
          <span style={{ color: 'var(--hint)' }}>Заявлено: <b style={{ color: 'var(--text)' }}>{fmt(expense.amount)}</b></span>
          {alreadyWrittenOff > 0 && (
            <>
              <span style={{ color: 'var(--hint)' }}>Списано: <b style={{ color: '#ff3b30' }}>{fmt(alreadyWrittenOff)}</b></span>
              <span style={{ color: 'var(--hint)' }}>Остаток: <b style={{ color: remaining > 0 ? '#34c759' : '#ff3b30' }}>{fmt(remaining)}</b></span>
            </>
          )}
        </div>
        {totalNew > 0 && (
          <div style={{
            background: totalNew > remaining && remaining > 0 ? '#fff0f0' : 'var(--bg2)',
            borderRadius: 10, padding: '8px 12px', marginBottom: 10,
            fontSize: 13, fontWeight: 600,
            color: totalNew > remaining && remaining > 0 ? '#ff3b30' : 'var(--text)',
          }}>
            К списанию: {fmt(totalNew)}
            {totalNew > remaining && remaining > 0 && ' ⚠️ превышает остаток'}
          </div>
        )}
        {ips.map(ip => (
          <IpRow
            key={ip.id}
            ip={ip}
            entry={entries[ip.id]}
            onChange={val => setEntries(prev => ({ ...prev, [ip.id]: val }))}
          />
        ))}
        <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
          <button className="btn btn-secondary" onClick={onClose} style={{ flex: 1 }}>Отмена</button>
          <button className="btn btn-primary" onClick={handleWriteOff} disabled={loading} style={{ flex: 1 }}>
            {loading ? 'Списание...' : 'Списать'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Модалка: редактировать списание ───────────────────────────────────────────

function EditWriteOffModal({ writeoff, onClose, onSaved }) {
  const [amount, setAmount] = useState(String(writeoff.amount))
  const source = writeoff.source
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  const handleSave = async () => {
    const amt = parseInt(amount, 10)
    if (!amt || amt <= 0) return setToast('Введите корректную сумму')
    setLoading(true)
    try {
      // Меняем сумму через существующий PATCH /operations/{id}
      // source меняется через cancel + create нового — но для простоты разрешаем только сумму
      await client.patch('/operations/' + writeoff.tx_id, { amount: amt })
      onSaved(amt)
    } catch (e) {
      setToast('Ошибка: ' + (e.response?.data?.detail || 'неизвестная'))
      setLoading(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.6)', display: 'flex', alignItems: 'flex-end', zIndex: 300 }}>
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      <div style={{ background: 'var(--bg)', borderRadius: '20px 20px 0 0', padding: '24px 16px', width: '100%' }}>
        <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 4 }}>Изменить списание</div>
        <div style={{ color: 'var(--hint)', fontSize: 13, marginBottom: 16 }}>
          {writeoff.ip_name} · {SOURCE_LABELS[source]}
        </div>
        <div className="input-group">
          <label className="input-label">Сумма (₽)</label>
          <input
            className="input-field"
            type="number"
            inputMode="numeric"
            value={amount}
            onChange={e => setAmount(e.target.value)}
          />
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

// ── Модалка: подтвердить отмену/удаление ─────────────────────────────────────

function ConfirmModal({ title, text, danger, confirmLabel, onClose, onConfirm }) {
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  const handle = async () => {
    setLoading(true)
    try {
      await onConfirm()
    } catch (e) {
      setToast('Ошибка: ' + (e.response?.data?.detail || 'неизвестная'))
      setLoading(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.6)', display: 'flex', alignItems: 'flex-end', zIndex: 300 }}>
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
      <div style={{ background: 'var(--bg)', borderRadius: '20px 20px 0 0', padding: '24px 16px', width: '100%' }}>
        <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 8, color: danger ? '#ff4444' : 'var(--text)' }}>{title}</div>
        <div style={{ color: 'var(--hint)', fontSize: 14, marginBottom: 16 }}>{text}</div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={onClose} style={{ flex: 1 }}>Отмена</button>
          <button
            className="btn"
            onClick={handle}
            disabled={loading}
            style={{ flex: 1, background: '#ff4444', color: '#fff' }}
          >
            {loading ? 'Удаление...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Главная страница ──────────────────────────────────────────────────────────

export default function Expenses({ user }) {
  const [expenses, setExpenses] = useState([])
  const [ips, setIps] = useState([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState(null)

  // Модалки
  const [showAdd, setShowAdd] = useState(false)
  const [writeOffTarget, setWriteOffTarget] = useState(null)
  const [editingWriteOff, setEditingWriteOff] = useState(null)       // { tx_id, ip_name, amount, source, expense_id }
  const [cancellingWriteOff, setCancellingWriteOff] = useState(null) // { tx_id, ip_name, amount, expense_id }
  const [deletingExpense, setDeletingExpense] = useState(null)       // expense object

  const isAdmin = user?.role === 'admin'
  const canCreate = user?.role === 'user' || user?.role === 'admin'

  const handleCloseExpense = async (exp) => {
    try {
      await client.patch('/expenses/' + exp.id + '/close')
      setExpenses(prev => prev.map(e => e.id === exp.id ? { ...e, is_closed: true } : e))
      setToast('✅ Расход закрыт')
    } catch (e) {
      setToast('Ошибка: ' + (e.response?.data?.detail || 'неизвестная'))
    }
  }

  const loadData = () => {
    setLoading(true)
    Promise.all([
      client.get('/expenses'),
      client.get('/balance'),
    ]).then(([expRes, balRes]) => {
      setExpenses(expRes.data)
      setIps(balRes.data.ips || [])
    }).catch(() => setToast('Ошибка загрузки'))
      .finally(() => setLoading(false))
  }

  useEffect(loadData, [])

  if (loading) return <div className="page-content"><Loader /></div>

  return (
    <div className="page-content">
      {toast && <Toast message={toast} onDone={() => setToast(null)} />}

      {/* Создать расход */}
      {showAdd && (
        <AddExpenseModal
          onClose={() => setShowAdd(false)}
          onCreated={(exp) => {
            setExpenses(prev => [{ ...exp, created_at: new Date().toISOString(), writeoffs: [] }, ...prev])
            setShowAdd(false)
            setToast('✅ Расход добавлен')
          }}
        />
      )}

      {/* Новое списание */}
      {writeOffTarget && (
        <WriteOffModal
          expense={writeOffTarget}
          ips={ips}
          alreadyWrittenOff={writeOffTarget.writeoffs.reduce((s, w) => s + w.amount, 0)}
          onClose={() => setWriteOffTarget(null)}
          onDone={() => { setWriteOffTarget(null); setToast('✅ Списано'); loadData() }}
        />
      )}

      {/* Редактировать списание */}
      {editingWriteOff && (
        <EditWriteOffModal
          writeoff={editingWriteOff}
          onClose={() => setEditingWriteOff(null)}
          onSaved={() => { setEditingWriteOff(null); setToast('✅ Списание обновлено'); loadData() }}
        />
      )}

      {/* Отменить отдельное списание */}
      {cancellingWriteOff && (
        <ConfirmModal
          title="Отменить списание?"
          text={'С ' + cancellingWriteOff.ip_name + ' — ' + fmt(cancellingWriteOff.amount) + '. Баланс ИП будет восстановлен.'}
          danger
          confirmLabel="Да, отменить"
          onClose={() => setCancellingWriteOff(null)}
          onConfirm={async () => {
            await client.post('/operations/' + cancellingWriteOff.tx_id + '/cancel')
            setCancellingWriteOff(null)
            setToast('✅ Списание отменено')
            loadData()
          }}
        />
      )}

      {/* Удалить расход целиком */}
      {deletingExpense && (
        <ConfirmModal
          title="Удалить расход?"
          text={'«' + deletingExpense.description + '» — ' + fmt(deletingExpense.amount) + '. Все списания будут отменены, балансы ИП восстановлены.'}
          danger
          confirmLabel="Удалить"
          onClose={() => setDeletingExpense(null)}
          onConfirm={async () => {
            await client.delete('/expenses/' + deletingExpense.id)
            setDeletingExpense(null)
            setToast('✅ Расход удалён')
            loadData()
          }}
        />
      )}

      <div className="page-header">💰 Расходы</div>

      {expenses.length > 0 && (() => {
        const totalAmount    = expenses.reduce((s, e) => s + e.amount, 0)
        const totalWrittenOff = expenses.reduce((s, e) => s + e.writeoffs.reduce((ws, w) => ws + w.amount, 0), 0)
        const totalRemaining = totalAmount - totalWrittenOff
        return (
          <div className="card" style={{ marginBottom: 12, padding: '12px 16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', textAlign: 'center' }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 11, color: 'var(--hint)', textTransform: 'uppercase', letterSpacing: '.4px' }}>Всего</div>
                <div style={{ fontWeight: 700, fontSize: 15, marginTop: 2 }}>{fmt(totalAmount)}</div>
              </div>
              <div style={{ flex: 1, borderLeft: '1px solid var(--bg)', borderRight: '1px solid var(--bg)' }}>
                <div style={{ fontSize: 11, color: 'var(--hint)', textTransform: 'uppercase', letterSpacing: '.4px' }}>Списано</div>
                <div style={{ fontWeight: 700, fontSize: 15, marginTop: 2, color: '#ff3b30' }}>{fmt(totalWrittenOff)}</div>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 11, color: 'var(--hint)', textTransform: 'uppercase', letterSpacing: '.4px' }}>Остаток</div>
                <div style={{ fontWeight: 700, fontSize: 15, marginTop: 2, color: totalRemaining > 0 ? '#ff9500' : '#34c759' }}>{fmt(totalRemaining)}</div>
              </div>
            </div>
          </div>
        )
      })()}

      {canCreate && (
        <button className="btn btn-primary" style={{ marginBottom: 12 }} onClick={() => setShowAdd(true)}>
          + Добавить расход
        </button>
      )}

      {expenses.length === 0 ? (
        <div className="card text-center"><div className="hint">Расходов нет</div></div>
      ) : (
        expenses.map(exp => {
          const writtenOff = exp.writeoffs.reduce((s, w) => s + w.amount, 0)
          const remaining = exp.amount - writtenOff
          return (
            <div key={exp.id} className="card" style={{ marginBottom: 8 }}>
              {/* Заголовок карточки */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>{exp.description}</div>
                  <div style={{ color: 'var(--hint)', fontSize: 12, marginTop: 2 }}>{formatDate(exp.created_at)}</div>
                </div>
                <div style={{ textAlign: 'right', display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 16 }}>{fmt(exp.amount)}</div>
                    {writtenOff > 0 && (
                      <div style={{ fontSize: 12, marginTop: 2, color: remaining > 0 ? '#ff9500' : '#34c759' }}>
                        {remaining > 0 ? 'остаток ' + fmt(remaining) : '✅ закрыт'}
                      </div>
                    )}
                  </div>
                  {/* Удалить расход — только admin */}
                  {isAdmin && (
                    <button
                      onClick={() => setDeletingExpense(exp)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, padding: '0 2px', color: '#ff4444', lineHeight: 1 }}
                      title="Удалить расход"
                    >🗑</button>
                  )}
                </div>
              </div>

              {/* Список списаний */}
              {exp.writeoffs.length > 0 && (
                <div style={{ marginTop: 8, borderTop: '1px solid var(--bg)', paddingTop: 8 }}>
                  {exp.writeoffs.map((w, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                      <div style={{ flex: 1, fontSize: 12, color: 'var(--hint)' }}>
                        {w.ip_name} · {SOURCE_LABELS[w.source]}
                      </div>
                      <div style={{ fontSize: 12, fontWeight: 600, color: '#ff3b30' }}>
                        -{fmt(w.amount)}
                      </div>
                      {/* Edit / Cancel для admin */}
                      {isAdmin && (
                        <div style={{ display: 'flex', gap: 2 }}>
                          <button
                            onClick={() => setEditingWriteOff({ ...w, expense_id: exp.id })}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 14, padding: '0 3px' }}
                            title="Изменить"
                          >✏️</button>
                          <button
                            onClick={() => setCancellingWriteOff({ ...w, expense_id: exp.id })}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 14, padding: '0 3px' }}
                            title="Отменить списание"
                          >✖️</button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Кнопки действий */}
              {canCreate && !exp.is_closed && (
                <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                  {remaining !== 0 && (
                    <button
                      className="btn btn-secondary"
                      style={{ flex: 1, padding: '6px 0' }}
                      onClick={() => setWriteOffTarget(exp)}
                    >
                      Списать на ИП
                    </button>
                  )}
                  {remaining > 0 && (
                    <button
                      className="btn btn-secondary"
                      style={{ flex: 1, padding: '6px 0' }}
                      onClick={() => handleCloseExpense(exp)}
                    >
                      ✅ Закрыть
                    </button>
                  )}
                </div>
              )}
              {exp.is_closed && (
                <div style={{ marginTop: 8, fontSize: 12, color: '#34c759', fontWeight: 600 }}>✅ Закрыт</div>
              )}
            </div>
          )
        })
      )}
    </div>
  )
}

import { useEffect, useState } from 'react'
import client from './api/client'
import BottomNav from './components/BottomNav'
import Dashboard from './pages/Dashboard'
import AddOperation from './pages/AddOperation'
import History from './pages/History'
import Debts from './pages/Debts'
import Report from './pages/Report'
import Admin from './pages/Admin'
import Loader from './components/Loader'

export default function App() {
  const [page, setPage] = useState('dashboard')
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    client.get('/me')
      .then(r => setUser(r.data))
      .catch(err => {
        // В браузере без initData — покажем заглушку
        if (err.response?.status === 401) {
          setUser({ display_name: 'Гость', role: 'user', cash_balance: 0 })
        }
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <Loader />
      </div>
    )
  }

  const renderPage = () => {
    switch (page) {
      case 'dashboard': return <Dashboard user={user} setPage={setPage} />
      case 'operation': return <AddOperation setPage={setPage} />
      case 'history':   return <History />
      case 'debts':     return <Debts />
      case 'report':    return <Report />
      case 'admin':     return <Admin currentUser={user} />
      default:          return <Dashboard user={user} setPage={setPage} />
    }
  }

  return (
    <div className="page">
      {renderPage()}
      <BottomNav page={page} setPage={setPage} isAdmin={user?.role === 'admin'} />
    </div>
  )
}

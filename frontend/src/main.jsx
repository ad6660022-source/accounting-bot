import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './styles/global.css'

// Инициализируем Telegram Web App
const tg = window.Telegram?.WebApp
if (tg) {
  tg.ready()
  tg.expand()
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

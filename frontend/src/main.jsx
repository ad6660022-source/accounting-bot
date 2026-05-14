import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './styles/global.css'

// Инициализируем Telegram Web App
const tg = window.Telegram?.WebApp
if (tg) {
  tg.ready()
  tg.expand()
  // Применяем тему как data-атрибут для CSS
  const applyTheme = () => {
    document.documentElement.setAttribute('data-theme', tg.colorScheme || 'light')
  }
  applyTheme()
  tg.onEvent('themeChanged', applyTheme)
} else {
  // В браузере — используем системную тему
  const dark = window.matchMedia('(prefers-color-scheme: dark)').matches
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

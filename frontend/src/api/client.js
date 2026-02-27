import axios from 'axios'

// Telegram Web App SDK
const tg = window.Telegram?.WebApp

// Axios-клиент: initData передаётся в каждом запросе как заголовок
const client = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Добавляем initData перед каждым запросом (он может обновиться)
client.interceptors.request.use((config) => {
  config.headers['X-Init-Data'] = tg?.initData || ''
  return config
})

export default client

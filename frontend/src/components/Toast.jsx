import { useEffect, useState } from 'react'

export default function Toast({ message, onDone }) {
  useEffect(() => {
    const t = setTimeout(onDone, 2500)
    return () => clearTimeout(t)
  }, [onDone])

  return <div className="toast">{message}</div>
}

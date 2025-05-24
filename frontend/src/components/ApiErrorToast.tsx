'use client'

import { useEffect, useState } from 'react'
import { AlertCircle, X } from 'lucide-react'

interface ApiError {
  message: string
  status: number
  url: string
}

interface Toast {
  id: string
  error: ApiError
  timestamp: number
}

export default function ApiErrorToast() {
  const [toasts, setToasts] = useState<Toast[]>([])

  useEffect(() => {
    const handleApiError = (event: CustomEvent<ApiError>) => {
      const newToast: Toast = {
        id: Date.now().toString(),
        error: event.detail,
        timestamp: Date.now()
      }
      
      setToasts(prev => [...prev, newToast])
      
      // Auto-remove dopo 10 secondi
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== newToast.id))
      }, 10000)
    }

    window.addEventListener('api-error', handleApiError as EventListener)
    
    return () => {
      window.removeEventListener('api-error', handleApiError as EventListener)
    }
  }, [])

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-[9999] space-y-2 max-w-md">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className="bg-red-500 text-white p-4 rounded-lg shadow-lg flex items-start gap-3 animate-slide-in-right"
        >
          <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="font-medium">Errore API</div>
            <div className="text-sm opacity-90 mt-1">
              {toast.error.message}
            </div>
            <div className="text-xs opacity-75 mt-1">
              Status: {toast.error.status} • {new URL(toast.error.url).pathname}
            </div>
          </div>
          <button
            onClick={() => removeToast(toast.id)}
            className="p-1 hover:bg-red-600 rounded transition-colors flex-shrink-0"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  )
} 
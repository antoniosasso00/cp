'use client'

import { useState, useEffect } from 'react'
import { Badge } from '@/components/ui/badge'
import { Wifi, WifiOff, AlertTriangle } from 'lucide-react'

interface ConnectionHealthCheckerProps {
  className?: string
  showLabel?: boolean
  checkInterval?: number
}

type ConnectionStatus = 'online' | 'offline' | 'slow' | 'checking'

export function ConnectionHealthChecker({ 
  className = "", 
  showLabel = true, 
  checkInterval = 30000 
}: ConnectionHealthCheckerProps) {
  const [status, setStatus] = useState<ConnectionStatus>('checking')
  const [lastCheck, setLastCheck] = useState<Date | null>(null)
  const [responseTime, setResponseTime] = useState<number | null>(null)

  const checkConnection = async () => {
    setStatus('checking')
    const startTime = Date.now()
    
    try {
      // Test semplice di connettività verso il backend con timeout
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)
      
      const response = await fetch('/api/v1/docs', {
        method: 'HEAD',
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      const endTime = Date.now()
      const responseTime = endTime - startTime
      
      setResponseTime(responseTime)
      setLastCheck(new Date())
      
      if (response.ok) {
        setStatus(responseTime > 3000 ? 'slow' : 'online')
      } else {
        setStatus('offline')
      }
    } catch (error) {
      console.warn('Controllo connessione fallito:', error)
      setStatus('offline')
      setLastCheck(new Date())
      setResponseTime(null)
    }
  }

  useEffect(() => {
    // Controllo iniziale
    checkConnection()
    
    // Controllo periodico
    const interval = setInterval(checkConnection, checkInterval)
    
    return () => clearInterval(interval)
  }, [checkInterval])

  const getStatusConfig = () => {
    switch (status) {
      case 'online':
        return {
          icon: <Wifi className="h-3 w-3" />,
          label: 'Online',
          variant: 'success' as const,
          description: responseTime ? `${responseTime}ms` : ''
        }
      case 'slow':
        return {
          icon: <AlertTriangle className="h-3 w-3" />,
          label: 'Lento',
          variant: 'warning' as const,
          description: responseTime ? `${responseTime}ms` : ''
        }
      case 'offline':
        return {
          icon: <WifiOff className="h-3 w-3" />,
          label: 'Offline',
          variant: 'destructive' as const,
          description: 'Nessuna connessione'
        }
      case 'checking':
      default:
        return {
          icon: <Wifi className="h-3 w-3 animate-pulse" />,
          label: 'Controllo...',
          variant: 'secondary' as const,
          description: ''
        }
    }
  }

  const config = getStatusConfig()

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Badge 
        variant={config.variant}
        className="flex items-center gap-1 cursor-pointer hover:opacity-80"
        onClick={checkConnection}
        title={`Clicca per aggiornare. Ultimo controllo: ${lastCheck?.toLocaleTimeString() || 'Mai'}`}
      >
        {config.icon}
        {showLabel && <span className="text-xs">{config.label}</span>}
        {config.description && (
          <span className="text-xs opacity-75 ml-1">
            {config.description}
          </span>
        )}
      </Badge>
    </div>
  )
} 
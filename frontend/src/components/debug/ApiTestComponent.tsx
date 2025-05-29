'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'

interface ApiTestResult {
  endpoint: string
  status: 'success' | 'error' | 'loading'
  message: string
  responseTime?: number
}

export function ApiTestComponent() {
  const [testResults, setTestResults] = useState<ApiTestResult[]>([])
  const [isRunning, setIsRunning] = useState(false)

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

  const testEndpoints = [
    { name: 'Health Check', url: 'http://localhost:8000/health' },
    { name: 'ODL List', url: `${API_BASE_URL}/odl` },
    { name: 'Tools List', url: `${API_BASE_URL}/tools` },
    { name: 'Autoclavi List', url: `${API_BASE_URL}/autoclavi` },
  ]

  const testEndpoint = async (endpoint: { name: string; url: string }): Promise<ApiTestResult> => {
    const startTime = Date.now()
    
    try {
      const response = await fetch(endpoint.url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        cache: 'no-store',
      })

      const responseTime = Date.now() - startTime

      if (response.ok) {
        return {
          endpoint: endpoint.name,
          status: 'success',
          message: `✅ OK (${response.status})`,
          responseTime,
        }
      } else {
        return {
          endpoint: endpoint.name,
          status: 'error',
          message: `❌ Error ${response.status}: ${response.statusText}`,
          responseTime,
        }
      }
    } catch (error) {
      const responseTime = Date.now() - startTime
      return {
        endpoint: endpoint.name,
        status: 'error',
        message: `💥 Network Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        responseTime,
      }
    }
  }

  const runAllTests = async () => {
    setIsRunning(true)
    setTestResults([])

    for (const endpoint of testEndpoints) {
      // Aggiungi stato loading
      setTestResults(prev => [...prev, {
        endpoint: endpoint.name,
        status: 'loading',
        message: 'Testing...',
      }])

      const result = await testEndpoint(endpoint)
      
      // Aggiorna con il risultato
      setTestResults(prev => 
        prev.map(r => r.endpoint === endpoint.name ? result : r)
      )

      // Piccola pausa tra i test
      await new Promise(resolve => setTimeout(resolve, 500))
    }

    setIsRunning(false)
  }

  const getStatusIcon = (status: ApiTestResult['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'loading':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
    }
  }

  const getStatusBadge = (status: ApiTestResult['status']) => {
    switch (status) {
      case 'success':
        return <Badge variant="default" className="bg-green-500">Success</Badge>
      case 'error':
        return <Badge variant="destructive">Error</Badge>
      case 'loading':
        return <Badge variant="secondary">Testing...</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" />
          Test Connettività API
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert>
          <AlertDescription>
            <strong>API Base URL:</strong> {API_BASE_URL}
          </AlertDescription>
        </Alert>

        <Button 
          onClick={runAllTests} 
          disabled={isRunning}
          className="w-full"
        >
          {isRunning ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Testing in corso...
            </>
          ) : (
            'Avvia Test API'
          )}
        </Button>

        {testResults.length > 0 && (
          <div className="space-y-2">
            <h3 className="font-medium">Risultati Test:</h3>
            {testResults.map((result, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-2">
                  {getStatusIcon(result.status)}
                  <span className="font-medium">{result.endpoint}</span>
                </div>
                <div className="flex items-center gap-2">
                  {result.responseTime && (
                    <span className="text-sm text-muted-foreground">
                      {result.responseTime}ms
                    </span>
                  )}
                  {getStatusBadge(result.status)}
                </div>
              </div>
            ))}
          </div>
        )}

        {testResults.length > 0 && (
          <div className="space-y-2">
            <h3 className="font-medium">Dettagli:</h3>
            {testResults.map((result, index) => (
              <div key={index} className="text-sm">
                <strong>{result.endpoint}:</strong> {result.message}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
} 
'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react'

interface CompatibilityTestProps {
  batchData: any
}

export const CompatibilityTest: React.FC<CompatibilityTestProps> = ({ batchData }) => {
  // Test di compatibilità
  const runCompatibilityTests = () => {
    const tests = []
    
    // Test 1: Verifica presenza configurazione JSON
    tests.push({
      name: "Configurazione JSON",
      status: batchData?.configurazione_json ? "pass" : "fail",
      message: batchData?.configurazione_json 
        ? "Configurazione JSON presente" 
        : "Configurazione JSON mancante"
    })
    
    // Test 2: Verifica presenza tool
    const tools = batchData?.configurazione_json?.positioned_tools || 
                  batchData?.configurazione_json?.tool_positions || []
    tests.push({
      name: "Tool Posizionati",
      status: tools.length > 0 ? "pass" : "warn",
      message: `${tools.length} tool trovati`
    })
    
    // Test 3: Verifica formato 2L
    const hasCavalletti = batchData?.configurazione_json?.cavalletti?.length > 0
    const hasLevels = tools.some((t: any) => t.level !== undefined)
    const is2L = hasCavalletti || hasLevels
    tests.push({
      name: "Formato 2L",
      status: is2L ? "pass" : "info",
      message: is2L 
        ? `Batch 2L rilevato (cavalletti: ${batchData?.configurazione_json?.cavalletti?.length || 0}, tool con livelli: ${tools.filter((t: any) => t.level !== undefined).length})`
        : "Batch 1L standard"
    })
    
    // Test 4: Verifica dati autoclave
    tests.push({
      name: "Dati Autoclave",
      status: batchData?.autoclave ? "pass" : "warn",
      message: batchData?.autoclave 
        ? `${batchData.autoclave.nome} (${batchData.autoclave.lunghezza}x${batchData.autoclave.larghezza_piano}mm)`
        : "Dati autoclave mancanti o incompleti"
    })
    
    // Test 5: Verifica struttura campi tool
    const sampleTool = tools[0]
    if (sampleTool) {
      const requiredFields = ['x', 'y', 'width', 'height']
      const missingFields = requiredFields.filter(field => sampleTool[field] === undefined)
      tests.push({
        name: "Campi Tool Richiesti",
        status: missingFields.length === 0 ? "pass" : "fail",
        message: missingFields.length === 0 
          ? "Tutti i campi richiesti presenti"
          : `Campi mancanti: ${missingFields.join(', ')}`
      })
    }
    
    // Test 6: Verifica metriche
    tests.push({
      name: "Metriche Batch",
      status: batchData?.metrics ? "pass" : "info",
      message: batchData?.metrics 
        ? `Efficienza: ${batchData.metrics.efficiency_percentage?.toFixed(1)}%`
        : "Metriche non disponibili"
    })
    
    return tests
  }
  
  const tests = runCompatibilityTests()
  const passCount = tests.filter(t => t.status === "pass").length
  const failCount = tests.filter(t => t.status === "fail").length
  const warnCount = tests.filter(t => t.status === "warn").length
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pass": return <CheckCircle className="h-4 w-4 text-green-500" />
      case "fail": return <XCircle className="h-4 w-4 text-red-500" />
      case "warn": return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      default: return <Info className="h-4 w-4 text-blue-500" />
    }
  }
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case "pass": return "text-green-700 bg-green-50 border-green-200"
      case "fail": return "text-red-700 bg-red-50 border-red-200"
      case "warn": return "text-yellow-700 bg-yellow-50 border-yellow-200"
      default: return "text-blue-700 bg-blue-50 border-blue-200"
    }
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          🧪 Test di Compatibilità Nesting
          <div className="ml-auto flex gap-2">
            <Badge variant="default" className="bg-green-500">
              {passCount} ✓
            </Badge>
            {warnCount > 0 && (
              <Badge variant="secondary" className="bg-yellow-500">
                {warnCount} ⚠
              </Badge>
            )}
            {failCount > 0 && (
              <Badge variant="destructive">
                {failCount} ✗
              </Badge>
            )}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {tests.map((test, index) => (
          <Alert key={index} className={getStatusColor(test.status)}>
            <div className="flex items-center gap-2">
              {getStatusIcon(test.status)}
              <span className="font-medium">{test.name}:</span>
            </div>
            <AlertDescription className="mt-1">
              {test.message}
            </AlertDescription>
          </Alert>
        ))}
        
        {/* Summary */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Riepilogo Batch:</h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-gray-600">ID:</span> {batchData?.id || 'N/A'}
            </div>
            <div>
              <span className="text-gray-600">Stato:</span> {batchData?.stato || 'N/A'}
            </div>
            <div>
              <span className="text-gray-600">Tipo:</span> {
                tests.find(t => t.name === "Formato 2L")?.status === "pass" ? "2L Multi-Livello" : "1L Standard"
              }
            </div>
            <div>
              <span className="text-gray-600">Canvas:</span> {
                tests.find(t => t.name === "Formato 2L")?.status === "pass" ? "NestingCanvas2L" : "NestingCanvas"
              }
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 
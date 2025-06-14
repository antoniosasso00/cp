'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card'
import { Button } from '@/shared/components/ui/button'
import { Badge } from '@/shared/components/ui/badge'
import NestingCanvas from './components/NestingCanvas'
import mockData from './test-mock-data.json'

// 🧪 COMPONENTE TEST: Verifica compatibilità NestingCanvas con formato 2L

export default function TestCompatibilityPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [testResult, setTestResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const runCompatibilityTest = () => {
    setIsLoading(true)
    setError(null)
    
    try {
      // 🔍 STEP 1: Verifica struttura JSON
      console.log('🧪 TEST 1: Struttura JSON Mock Data')
      console.log('Mock Data:', mockData)
      
      // 🔍 STEP 2: Verifica campi positioned_tools
      const tools = mockData.configurazione_json.positioned_tools
      console.log('🧪 TEST 2: Tool con livelli')
      console.log('Total tools:', tools.length)
      
      tools.forEach((tool, index) => {
        console.log(`Tool ${index + 1}:`, {
          odl_id: tool.odl_id,
          part_number: tool.part_number,
          level: tool.level,
          has_level: tool.level !== undefined,
          position: { x: tool.x, y: tool.y },
          dimensions: { width: tool.width, height: tool.height }
        })
      })
      
      // 🔍 STEP 3: Verifica cavalletti
      const cavalletti = mockData.configurazione_json.cavalletti
      console.log('🧪 TEST 3: Cavalletti')
      console.log('Total cavalletti:', cavalletti.length)
      
      cavalletti.forEach((cavalletto, index) => {
        console.log(`Cavalletto ${index + 1}:`, {
          tool_odl_id: cavalletto.tool_odl_id,
          position: { x: cavalletto.x, y: cavalletto.y },
          sequence: cavalletto.sequence_number,
          capacity: cavalletto.load_capacity_kg
        })
      })
      
      // 🔍 STEP 4: Conteggi per livello
      const level0Tools = tools.filter(t => t.level === 0)
      const level1Tools = tools.filter(t => t.level === 1)
      
      setTestResult({
        success: true,
        totalTools: tools.length,
        level0Count: level0Tools.length,
        level1Count: level1Tools.length,
        cavallettiCount: cavalletti.length,
        level0Tools: level0Tools.map(t => t.part_number),
        level1Tools: level1Tools.map(t => t.part_number),
        hasLevelField: tools.every(t => t.level !== undefined),
        hasCavalletti: cavalletti.length > 0
      })
      
      console.log('🧪 TEST RESULT:', {
        level0Count: level0Tools.length,
        level1Count: level1Tools.length,
        cavallettiCount: cavalletti.length
      })
      
    } catch (err: any) {
      console.error('❌ TEST FAILED:', err)
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    // Auto-run test on mount
    runCompatibilityTest()
  }, [])

  return (
    <div className="space-y-6 p-6">
      <Card>
        <CardHeader>
          <CardTitle>🧪 Test Compatibilità NestingCanvas - Formato 2L</CardTitle>
          <p className="text-sm text-gray-600">
            Verifica che il componente NestingCanvas riesca a parsare correttamente il nuovo formato JSON 
            con livelli (0/1) e cavalletti senza errori.
          </p>
        </CardHeader>
        
        <CardContent className="space-y-4">
          <div className="flex gap-3">
            <Button 
              onClick={runCompatibilityTest} 
              disabled={isLoading}
              variant="outline"
            >
              {isLoading ? '🔄 Testing...' : '▶️ Run Test'}
            </Button>
          </div>

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600 font-medium">❌ Test Failed</p>
              <p className="text-red-500 text-sm mt-1">{error}</p>
            </div>
          )}

          {testResult && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-600 font-medium">✅ Test Passed</p>
              <div className="grid grid-cols-2 gap-4 mt-3 text-sm">
                <div>
                  <p><strong>Total Tools:</strong> {testResult.totalTools}</p>
                  <p><strong>Level 0 Tools:</strong> {testResult.level0Count}</p>
                  <p><strong>Level 1 Tools:</strong> {testResult.level1Count}</p>
                  <p><strong>Cavalletti:</strong> {testResult.cavallettiCount}</p>
                </div>
                <div>
                  <p><strong>Has Level Field:</strong> {testResult.hasLevelField ? '✅' : '❌'}</p>
                  <p><strong>Has Cavalletti:</strong> {testResult.hasCavalletti ? '✅' : '❌'}</p>
                </div>
              </div>
              
              <div className="mt-4">
                <p className="font-medium">Level 0 Parts:</p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {testResult.level0Tools.map((part: string, i: number) => (
                    <Badge key={i} variant="outline" className="text-xs">
                      {part}
                    </Badge>
                  ))}
                </div>
                
                <p className="font-medium mt-2">Level 1 Parts:</p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {testResult.level1Tools.map((part: string, i: number) => (
                    <Badge key={i} variant="secondary" className="text-xs">
                      {part}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 🎯 CANVAS TEST: Carica il mock data nel componente reale */}
      <Card>
        <CardHeader>
          <CardTitle>🎯 NestingCanvas Rendering Test</CardTitle>
          <p className="text-sm text-gray-600">
            Il componente sotto dovrebbe renderizzare correttamente i tool e mostrare i log di parsing nella console.
          </p>
        </CardHeader>
        
        <CardContent>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600 mb-4">
              📋 Apri la console del browser (F12) per vedere i log dettagliati di parsing del NestingCanvas.
            </p>
            
            {/* Rendering del canvas con mock data */}
            <NestingCanvas batchData={mockData as any} />
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 
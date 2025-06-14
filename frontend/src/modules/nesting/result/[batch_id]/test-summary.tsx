'use client'

import React from 'react'
import { Badge } from '@/shared/components/ui/badge'
import mockData from './test-mock-data.json'

// 🔍 QUICK TEST: Verifica che i dati siano parsabili

const TestSummary = () => {
  const tools = mockData.configurazione_json.positioned_tools
  const cavalletti = mockData.configurazione_json.cavalletti
  
  const level0Tools = tools.filter(t => t.level === 0)
  const level1Tools = tools.filter(t => t.level === 1)
  
  console.log('🔍 QUICK TEST - Mock Data Parsing:', {
    totalTools: tools.length,
    level0: level0Tools.length,
    level1: level1Tools.length,
    cavalletti: cavalletti.length,
    hasLevelField: tools.every(t => t.level !== undefined),
    allToolsHavePosition: tools.every(t => t.x !== undefined && t.y !== undefined)
  })

  return (
    <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
      <h3 className="font-bold text-lg mb-3">🔍 Test Summary - Mock Data Parsing</h3>
      
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <p><strong>Total Tools:</strong> {tools.length}</p>
          <p><strong>Level 0 (Piano):</strong> {level0Tools.length}</p>
          <p><strong>Level 1 (Cavalletti):</strong> {level1Tools.length}</p>
          <p><strong>Cavalletti:</strong> {cavalletti.length}</p>
        </div>
        
        <div>
          <p><strong>Has Level Field:</strong> {tools.every(t => t.level !== undefined) ? '✅' : '❌'}</p>
          <p><strong>Has Positions:</strong> {tools.every(t => t.x !== undefined && t.y !== undefined) ? '✅' : '❌'}</p>
          <p><strong>Has Part Numbers:</strong> {tools.every(t => t.part_number) ? '✅' : '❌'}</p>
          <p><strong>Is 2L Compatible:</strong> {(tools.some(t => t.level !== undefined) || cavalletti.length > 0) ? '✅' : '❌'}</p>
        </div>
      </div>
      
      <div className="mt-4">
        <p className="font-medium mb-2">Level 0 Tools:</p>
        <div className="flex flex-wrap gap-1">
          {level0Tools.map((tool, i) => (
            <Badge key={i} variant="outline" className="text-xs">
              {tool.part_number} (ODL {tool.odl_id})
            </Badge>
          ))}
        </div>
        
        <p className="font-medium mb-2 mt-3">Level 1 Tools:</p>
        <div className="flex flex-wrap gap-1">
          {level1Tools.map((tool, i) => (
            <Badge key={i} variant="secondary" className="text-xs">
              {tool.part_number} (ODL {tool.odl_id})
            </Badge>
          ))}
        </div>
      </div>
    </div>
  )
}

export default TestSummary 
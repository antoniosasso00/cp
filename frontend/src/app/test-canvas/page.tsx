'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function TestCanvasPage() {
  const [canvasData, setCanvasData] = useState<any>(null)
  
  useEffect(() => {
    // Simula dati semplici per test
    const testData = {
      configurazione_json: {
        canvas_width: 1200.0,
        canvas_height: 2000.0,
        tool_positions: [
          {
            odl_id: 1,
            x: 100,
            y: 100,
            width: 200,
            height: 150,
            peso: 25.0,
            rotated: false,
            part_number: "TEST-001",
            tool_nome: "Test Tool 1"
          },
          {
            odl_id: 2,
            x: 350,
            y: 100,
            width: 150,
            height: 300,
            peso: 30.0,
            rotated: true,
            part_number: "TEST-002", 
            tool_nome: "Test Tool 2"
          },
          {
            odl_id: 3,
            x: 100,
            y: 300,
            width: 400,
            height: 100,
            peso: 15.0,
            rotated: false,
            part_number: "TEST-003",
            tool_nome: "Test Tool 3"
          }
        ]
      },
      autoclave: {
        id: 1,
        nome: "Test Autoclave",
        lunghezza: 2000.0,
        larghezza_piano: 1200.0,
        codice: "TEST-AUTO-001",
        produttore: "TestCorp"
      },
      metrics: {
        efficiency_percentage: 45.2
      },
      id: "test-batch-123"
    }
    
    setCanvasData(testData)
  }, [])

  if (!canvasData) {
    return <div>Caricamento test...</div>
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <Card>
        <CardHeader>
          <CardTitle>🧪 Test Canvas Semplice</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="text-sm text-gray-600">
              <p><strong>Canvas:</strong> {canvasData.configurazione_json.canvas_width} x {canvasData.configurazione_json.canvas_height} mm</p>
              <p><strong>Tools:</strong> {canvasData.configurazione_json.tool_positions.length}</p>
              <p><strong>Autoclave:</strong> {canvasData.autoclave.nome}</p>
            </div>
            
            <div className="border border-gray-300 p-4 bg-gray-50 rounded">
              <h3 className="font-medium mb-2">Tool Positions:</h3>
              {canvasData.configurazione_json.tool_positions.map((tool: any) => (
                <div key={tool.odl_id} className="text-xs mb-1">
                  ODL {tool.odl_id}: ({tool.x}, {tool.y}) - {tool.width}×{tool.height}mm - {tool.peso}kg
                  {tool.rotated && " [RUOTATO]"}
                </div>
              ))}
            </div>

            {/* Import dinamico del canvas */}
            <div className="h-96 border-2 border-blue-300 rounded-lg p-4">
              <p className="text-center text-gray-500 mt-32">
                Canvas verrà mostrato qui dopo il fix
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 
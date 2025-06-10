'use client'

import React, { useState } from 'react'
import dynamic from 'next/dynamic'
import { Card } from '@/shared/components/ui/card'
import { Button } from '@/shared/components/ui/button'
import { Badge } from '@/shared/components/ui/badge'
import { Loader2 } from 'lucide-react'

// Dynamic import del canvas per SSR
const NestingCanvasV2 = dynamic(
  () => import('@/modules/nesting/result/[batch_id]/components/NestingCanvasV2'),
  {
    loading: () => (
      <div className="flex items-center justify-center h-96 bg-white border rounded-lg">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    ),
    ssr: false
  }
)

// Dati di test per il canvas
const generateTestData = (count: number) => {
  const tools = []
  const canvasWidth = 2000
  const canvasHeight = 1500
  
  for (let i = 1; i <= count; i++) {
    const width = 80 + Math.random() * 200
    const height = 60 + Math.random() * 150
    const x = Math.random() * (canvasWidth - width)
    const y = Math.random() * (canvasHeight - height)
    
    tools.push({
      odl_id: i,
      x,
      y,
      width,
      height,
      peso: 1 + Math.random() * 10,
      rotated: Math.random() > 0.7,
      part_number: `PART-${String(i).padStart(3, '0')}`,
      tool_nome: `Tool ${i} - ${Math.random() > 0.5 ? 'Rettangolare' : 'Quadrato'}`
    })
  }
  
  return tools
}

export default function TestCanvasPage() {
  const [toolCount, setToolCount] = useState(25)
  const [selectedTool, setSelectedTool] = useState<number | null>(null)
  const [canvasSize, setCanvasSize] = useState({ width: 2000, height: 1500 })
  const [isFullscreen, setIsFullscreen] = useState(false)

  const toolPositions = generateTestData(toolCount)

  const handleToolSelect = (odlId: number | null) => {
    setSelectedTool(odlId)
    console.log('🎯 Tool selezionato:', odlId)
  }

  const handleRegenerateData = () => {
    // Force re-render con nuovi dati casuali
    setToolCount(prev => prev)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto space-y-4">
        {/* Header */}
        <Card className="p-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold">🧪 Test Canvas Nesting v2.0</h1>
              <p className="text-gray-600">Test delle funzionalità upgrade: grid 10mm, righello, pan/zoom, virtualizzazione</p>
            </div>
            <Badge variant="outline" className="text-lg px-3 py-1">
              {toolPositions.length > 100 ? '⚡ VIRTUALIZED' : '📊 STANDARD'} Mode
            </Badge>
          </div>

          {/* Controls */}
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Tool Count:</label>
              <select 
                value={toolCount} 
                onChange={(e) => setToolCount(Number(e.target.value))}
                className="px-3 py-1 border rounded"
              >
                <option value={10}>10 tools</option>
                <option value={25}>25 tools</option>
                <option value={50}>50 tools</option>
                <option value={75}>75 tools</option>
                <option value={100}>100 tools</option>
                <option value={150}>150 tools (virtualized)</option>
                <option value={200}>200 tools (virtualized)</option>
                <option value={500}>500 tools (virtualized)</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Canvas Size:</label>
              <select
                value={`${canvasSize.width}x${canvasSize.height}`}
                onChange={(e) => {
                  const [w, h] = e.target.value.split('x').map(Number)
                  setCanvasSize({ width: w, height: h })
                }}
                className="px-3 py-1 border rounded"
              >
                <option value="1500x1000">1500×1000 mm</option>
                <option value="2000x1500">2000×1500 mm</option>
                <option value="3000x2000">3000×2000 mm</option>
                <option value="4000x3000">4000×3000 mm</option>
              </select>
            </div>

            <Button onClick={handleRegenerateData} size="sm">
              🎲 Rigenera Dati
            </Button>

            <Button 
              onClick={() => setIsFullscreen(!isFullscreen)} 
              variant="outline" 
              size="sm"
            >
              {isFullscreen ? '🗗 Normale' : '🗖 Fullscreen'}
            </Button>
          </div>
        </Card>

        {/* Performance Info */}
        <Card className="p-3 bg-blue-50 border-blue-200">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="font-medium text-blue-800">Tools Rendering</div>
              <div className="text-blue-600">{toolPositions.length} elementi</div>
            </div>
            <div>
              <div className="font-medium text-blue-800">Canvas Size</div>
              <div className="text-blue-600">{canvasSize.width} × {canvasSize.height} mm</div>
            </div>
            <div>
              <div className="font-medium text-blue-800">Virtualization</div>
              <div className="text-blue-600">
                {toolPositions.length > 100 ? '✅ Attiva (&gt;100)' : '❌ Disattiva (≤100)'}
              </div>
            </div>
            <div>
              <div className="font-medium text-blue-800">Target FPS</div>
              <div className="text-blue-600">60+ FPS</div>
            </div>
          </div>
        </Card>

        {/* Canvas Container */}
        <div className="flex gap-4">
          {/* Canvas */}
          <div className="flex-1">
            <NestingCanvasV2
              canvasWidth={canvasSize.width}
              canvasHeight={canvasSize.height}
              toolPositions={toolPositions}
              planeAssignments={{}}
              isFullscreen={isFullscreen}
              onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
              onToolSelect={handleToolSelect}
              className={isFullscreen ? 'fixed inset-0 z-50 bg-white' : ''}
            />
          </div>

          {/* Sidebar Info */}
          {!isFullscreen && (
            <div className="w-80 space-y-4">
              {/* Features Test */}
              <Card className="p-4">
                <h3 className="font-semibold mb-3">✨ Features Test</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Grid Toggle (10mm)</span>
                    <span className="text-green-600">✅</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Ruler (mm units)</span>
                    <span className="text-green-600">✅</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Pan (mouse drag)</span>
                    <span className="text-green-600">✅</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Zoom (Ctrl + wheel)</span>
                    <span className="text-green-600">✅</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Debounce (16ms)</span>
                    <span className="text-green-600">✅</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tool Selection</span>
                    <span className="text-green-600">✅</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Virtualization</span>
                    <span className={toolPositions.length > 100 ? "text-green-600" : "text-gray-400"}>
                      {toolPositions.length > 100 ? "✅" : "⏸️"}
                    </span>
                  </div>
                </div>
              </Card>

              {/* Tool Selected */}
              {selectedTool && (
                <Card className="p-4 bg-blue-50 border-blue-200">
                  <h3 className="font-semibold text-blue-800 mb-2">🎯 Tool Selezionato</h3>
                  {(() => {
                    const tool = toolPositions.find(t => t.odl_id === selectedTool)
                    if (!tool) return null
                    
                    return (
                      <div className="space-y-2 text-sm">
                        <div><strong>ODL:</strong> {tool.odl_id}</div>
                        <div><strong>Parte:</strong> {tool.part_number}</div>
                        <div><strong>Tool:</strong> {tool.tool_nome}</div>
                        <div><strong>Pos:</strong> ({tool.x.toFixed(0)}, {tool.y.toFixed(0)}) mm</div>
                        <div><strong>Size:</strong> {tool.width.toFixed(0)} × {tool.height.toFixed(0)} mm</div>
                        <div><strong>Weight:</strong> {tool.peso.toFixed(1)} kg</div>
                        <div><strong>Rotated:</strong> {tool.rotated ? 'Yes' : 'No'}</div>
                      </div>
                    )
                  })()}
                </Card>
              )}

              {/* Performance Tips */}
              <Card className="p-4 bg-green-50 border-green-200">
                <h3 className="font-semibold text-green-800 mb-2">🚀 Performance Tips</h3>
                <div className="space-y-1 text-xs text-green-700">
                  <div>• Use Ctrl+Wheel for smooth zoom</div>
                  <div>• Virtualization auto-activates &gt;100 tools</div>
                  <div>• Grid optimized for viewport rendering</div>
                  <div>• 16ms debounce maintains 60+ FPS</div>
                  <div>• Tool labels hide on low zoom levels</div>
                </div>
              </Card>

              {/* Test Instructions */}
              <Card className="p-4 bg-yellow-50 border-yellow-200">
                <h3 className="font-semibold text-yellow-800 mb-2">🧪 Test Instructions</h3>
                <div className="space-y-1 text-xs text-yellow-700">
                  <div>1. Try different tool counts (10-500)</div>
                  <div>2. Test zoom with Ctrl+Wheel</div>
                  <div>3. Pan by dragging background</div>
                  <div>4. Click tools to select them</div>
                  <div>5. Toggle grid/ruler/dimensions</div>
                  <div>6. Test fullscreen mode</div>
                  <div>7. Check performance with 500 tools</div>
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 
'use client'

import React, { useState } from 'react'
import { ToolRect, SimpleToolRect, testSmallAreaRendering, mapODLIdToNumber } from './tool-rect'
import type { ToolPosition } from './types'

/**
 * Demo component per mostrare il comportamento del ToolRect
 * con diverse dimensioni e contenuti
 */
export const ToolRectDemo: React.FC = () => {
  const [selectedTool, setSelectedTool] = useState<number | null>(null)
  const [showTooltips, setShowTooltips] = useState(true)
  
  // Esempi di tool con diverse dimensioni per test
  const demoTools: ToolPosition[] = [
    {
      odl_id: 1,
      x: 50,
      y: 50,
      width: 120,
      height: 80,
      peso: 25.5,
      rotated: false,
      part_number: 'P123456',
      numero_odl: '2024001',
      descrizione_breve: 'Componente Principale',
      excluded: false
    },
    {
      odl_id: 2,
      x: 200,
      y: 50,
      width: 80,
      height: 60,
      peso: 15.2,
      rotated: true,
      rotation_angle: 90,
      part_number: 'P789012',
      numero_odl: '2024002',
      descrizione_breve: 'Parte Ruotata',
      excluded: false
    },
    {
      odl_id: 3,
      x: 320,
      y: 50,
      width: 40,
      height: 30,
      peso: 5.1,
      rotated: false,
      part_number: 'P345678',
      numero_odl: '2024003',
      descrizione_breve: 'Componente Piccolo',
      excluded: false
    },
    {
      odl_id: 4,
      x: 400,
      y: 50,
      width: 25,
      height: 20,
      peso: 2.3,
      rotated: false,
      part_number: 'P901234',
      numero_odl: '2024004',
      descrizione_breve: 'Molto Piccolo',
      excluded: false
    },
    {
      odl_id: 5,
      x: 50,
      y: 160,
      width: 100,
      height: 50,
      peso: 18.7,
      rotated: false,
      part_number: 'P567890',
      numero_odl: '2024005',
      descrizione_breve: 'Componente Escluso',
      excluded: true
    },
    {
      odl_id: 6,
      x: 450,
      y: 50,
      width: 60,
      height: 40,
      peso: 12.1,
      rotated: false,
      part_number: 'P111222',
      numero_odl: '',  // Test senza numero ODL
      descrizione_breve: 'Senza Numero ODL',
      excluded: false
    }
  ]

  const autoclaveWidth = 500
  const autoclaveHeight = 300

  const handleToolClick = (toolId: number) => {
    setSelectedTool(selectedTool === toolId ? null : toolId)
  }

  // Esegui test di rendering su piccole aree
  const smallAreaTests = testSmallAreaRendering()

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">ToolRect Component Demo</h1>
        
        {/* Controlli */}
        <div className="mb-6 flex gap-4 items-center">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={showTooltips}
              onChange={(e) => setShowTooltips(e.target.checked)}
              className="rounded"
            />
            <span>Mostra Tooltip</span>
          </label>
          
          <button
            onClick={() => setSelectedTool(null)}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Deseleziona Tutto
          </button>
        </div>

        {/* Canvas principale */}
        <div className="bg-white border-2 border-gray-300 mb-8" style={{ width: autoclaveWidth + 100, height: autoclaveHeight + 100 }}>
          <div className="p-12">
            <h2 className="text-xl font-semibold mb-4">Canvas Principale - Test Dimensioni Diverse</h2>
            
            {/* Area autoclave */}
            <div className="relative border-2 border-blue-500 bg-blue-50" style={{ width: autoclaveWidth, height: autoclaveHeight }}>
              <div className="absolute top-2 left-2 text-xs text-blue-600 font-mono">
                Autoclave {autoclaveWidth} × {autoclaveHeight} mm
              </div>
              
              {/* Rendering dei tool */}
              <svg width={autoclaveWidth} height={autoclaveHeight} className="absolute inset-0">
                {demoTools.map((tool) => (
                  <ToolRect
                    key={tool.odl_id}
                    tool={tool}
                    onClick={() => handleToolClick(tool.odl_id)}
                    isSelected={selectedTool === tool.odl_id}
                    autoclaveWidth={autoclaveWidth}
                    autoclaveHeight={autoclaveHeight}
                    showTooltips={showTooltips}
                  />
                ))}
              </svg>
            </div>
          </div>
        </div>

        {/* Informazioni tool selezionato */}
        {selectedTool && (
          <div className="bg-white p-6 rounded-lg shadow-md mb-8">
            <h3 className="text-lg font-semibold mb-4">Tool Selezionato: ODL {selectedTool}</h3>
            {(() => {
              const tool = demoTools.find(t => t.odl_id === selectedTool)
              if (!tool) return null
              
              return (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <strong>Numero ODL:</strong><br />
                    {mapODLIdToNumber(tool)}
                  </div>
                  <div>
                    <strong>Part Number:</strong><br />
                    {tool.part_number}
                  </div>
                  <div>
                    <strong>Dimensioni:</strong><br />
                    {tool.width} × {tool.height} mm
                  </div>
                  <div>
                    <strong>Area:</strong><br />
                    {(tool.width * tool.height / 1000).toFixed(1)} cm²
                  </div>
                  <div>
                    <strong>Peso:</strong><br />
                    {tool.peso} kg
                  </div>
                  <div>
                    <strong>Rotazione:</strong><br />
                    {tool.rotated ? `Sì (${tool.rotation_angle || 90}°)` : 'No'}
                  </div>
                  <div>
                    <strong>Stato:</strong><br />
                    {tool.excluded ? 'Escluso' : 'Valido'}
                  </div>
                  <div>
                    <strong>Posizione:</strong><br />
                    ({tool.x}, {tool.y})
                  </div>
                </div>
              )
            })()}
          </div>
        )}

        {/* Test risultati piccole aree */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h3 className="text-lg font-semibold mb-4">Test Rendering Piccole Aree (&lt; 50px)</h3>
          
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Dimensioni</th>
                  <th className="text-left p-2">Area</th>
                  <th className="text-left p-2">Font Size</th>
                  <th className="text-left p-2">Visibilità Testo</th>
                  <th className="text-left p-2">Risultato Atteso</th>
                  <th className="text-left p-2">Risultato Effettivo</th>
                </tr>
              </thead>
              <tbody>
                {smallAreaTests.map((test, index) => (
                  <tr key={index} className="border-b">
                    <td className="p-2 font-mono">{test.width} × {test.height}</td>
                    <td className="p-2">{(test.width * test.height).toLocaleString()} px²</td>
                    <td className="p-2">{test.fontSize}px</td>
                    <td className="p-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        test.textVisible ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {test.result}
                      </span>
                    </td>
                    <td className="p-2 text-gray-600">{test.expected}</td>
                    <td className="p-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        test.result === (test.expected.includes('No') ? 'Hidden' : 'Visible') 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {test.result === (test.expected.includes('No') ? 'Hidden' : 'Visible') ? '✓ Pass' : '⚠ Check'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Confronto versioni Simple vs Complete */}
        <div className="grid md:grid-cols-2 gap-8">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">ToolRect Completo</h3>
            <div className="border border-gray-300" style={{ width: 200, height: 120 }}>
              <svg width={200} height={120}>
                <ToolRect
                  tool={demoTools[0]}
                  autoclaveWidth={200}
                  autoclaveHeight={120}
                  showTooltips={showTooltips}
                />
              </svg>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Include: ODL, Part#, Descrizione, Tooltip, Indicatori
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">SimpleToolRect</h3>
            <div className="border border-gray-300" style={{ width: 200, height: 120 }}>
              <svg width={200} height={120}>
                <SimpleToolRect
                  tool={demoTools[0]}
                  autoclaveWidth={200}
                  autoclaveHeight={120}
                />
              </svg>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Include: Solo ODL, rendering ottimizzato
            </p>
          </div>
        </div>

        {/* Legenda */}
        <div className="bg-white p-6 rounded-lg shadow-md mt-8">
          <h3 className="text-lg font-semibold mb-4">Legenda</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500 border border-green-600"></div>
              <span>Tool Valido</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-yellow-500 border border-yellow-600"></div>
              <span>Tool Ruotato</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-500 border border-red-600"></div>
              <span>Tool Escluso</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-orange-500 border border-orange-600"></div>
              <span>Fuori Limiti</span>
            </div>
          </div>
          <div className="mt-4 text-xs text-gray-600">
            <p><strong>R</strong> = Indicatore rotazione | <strong>!</strong> = Fuori dai limiti autoclave</p>
            <p>Il font-size si adatta automaticamente all'area del rettangolo con scala logaritmica</p>
            <p>Hover sui tool per vedere tooltip dettagliati (se abilitati)</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ToolRectDemo 
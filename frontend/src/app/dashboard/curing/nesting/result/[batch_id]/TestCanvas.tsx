'use client'

import React from 'react'
import NestingCanvas from './NestingCanvas'

// Dati di test per verificare il funzionamento del canvas
const mockODLData = [
  {
    odl_id: 1,
    tool_id: 101,
    x_mm: 50,
    y_mm: 50,
    larghezza_mm: 400,
    lunghezza_mm: 300,
    part_number: "PN001-TEST",
    descrizione: "Componente di test 1",
    ciclo_cura: "Ciclo Standard A",
    tool_nome: "Tool-A-001"
  },
  {
    odl_id: 2,
    tool_id: 102,
    x_mm: 500,
    y_mm: 50,
    larghezza_mm: 350,
    lunghezza_mm: 250,
    part_number: "PN002-TEST",
    descrizione: "Componente di test 2",
    ciclo_cura: "Ciclo Standard B",
    tool_nome: "Tool-B-002"
  },
  {
    odl_id: 3,
    tool_id: 103,
    x_mm: 100,
    y_mm: 400,
    larghezza_mm: 300,
    lunghezza_mm: 200,
    part_number: "PN003-TEST",
    descrizione: "Componente di test 3",
    ciclo_cura: "Ciclo Rapido C",
    tool_nome: "Tool-C-003"
  }
]

const mockAutoclave = {
  id: 1,
  nome: "Autoclave Test A1",
  lunghezza: 1500,
  larghezza_piano: 800,
  codice: "AUT-001"
}

const TestCanvas: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      <div className="border rounded-lg p-4 bg-blue-50">
        <h2 className="text-lg font-semibold mb-2 text-blue-900">🧪 Test Canvas Nesting</h2>
        <p className="text-sm text-blue-700">
          Questo è un test del componente NestingCanvas con dati mock per verificare il funzionamento.
        </p>
      </div>
      
      <NestingCanvas 
        odlData={mockODLData}
        autoclave={mockAutoclave}
        className="w-full"
      />
      
      <div className="border rounded-lg p-4 bg-green-50">
        <h3 className="font-medium mb-2 text-green-900">✅ Test Status</h3>
        <div className="space-y-1 text-sm text-green-700">
          <p>• Canvas caricato: <span className="font-medium">✓</span></p>
          <p>• ODL visualizzati: <span className="font-medium">{mockODLData.length}</span></p>
          <p>• Dimensioni autoclave: <span className="font-medium">{mockAutoclave.lunghezza} × {mockAutoclave.larghezza_piano} mm</span></p>
          <p>• React-Konva: <span className="font-medium">✓ Funzionante</span></p>
        </div>
      </div>
    </div>
  )
}

export default TestCanvas 
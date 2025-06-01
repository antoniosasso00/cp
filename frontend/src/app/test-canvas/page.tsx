import NestingCanvas from '../dashboard/curing/nesting/result/[batch_id]/NestingCanvas'

export default function TestCanvasPage() {
  // Dati di test per il NestingCanvas
  const testBatchData = {
    configurazione_json: {
      canvas_width: 800,
      canvas_height: 600,
      tool_positions: [
        {
          odl_id: 1,
          x: 100,
          y: 100,
          width: 200,
          height: 150,
          peso: 5.5,
          rotated: false,
          part_number: "TEST001",
          tool_nome: "Tool Test 1"
        },
        {
          odl_id: 2,
          x: 350,
          y: 100,
          width: 180,
          height: 120,
          peso: 3.2,
          rotated: true,
          part_number: "TEST002",
          tool_nome: "Tool Test 2"
        }
      ]
    },
    autoclave: {
      id: 1,
      nome: "Autoclave Test",
      lunghezza: 2000,
      larghezza_piano: 1200,
      codice: "AC001"
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Test Canvas React-Konva</h1>
          <p className="text-gray-600">Verifica del funzionamento del componente NestingCanvas</p>
        </div>
        
        <NestingCanvas batchData={testBatchData} className="max-w-4xl mx-auto" />
      </div>
    </div>
  )
} 
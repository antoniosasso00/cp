import TestCanvas from '../dashboard/curing/nesting/result/[batch_id]/TestCanvas'

export default function TestCanvasPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Test Canvas React-Konva</h1>
          <p className="text-gray-600">Verifica del funzionamento del componente NestingCanvas</p>
        </div>
        
        <TestCanvas />
      </div>
    </div>
  )
} 
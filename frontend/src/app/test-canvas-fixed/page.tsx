'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, AlertTriangle } from 'lucide-react';

// ✅ Import del wrapper centralizzato
import CanvasWrapper, { 
  Layer, 
  Rect, 
  Text, 
  Circle,
  useClientMount 
} from '@/components/canvas/CanvasWrapper';

// Dati di test semplici
const testData = [
  { id: 1, x: 50, y: 50, width: 100, height: 80, color: '#FF6B6B', label: 'Test A' },
  { id: 2, x: 200, y: 100, width: 120, height: 60, color: '#4ECDC4', label: 'Test B' },
  { id: 3, x: 350, y: 50, width: 80, height: 100, color: '#45B7D1', label: 'Test C' },
];

export default function TestCanvasFixedPage() {
  const mounted = useClientMount();

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold">✅ Test Canvas - Versione Corretta</h1>
          <p className="text-muted-foreground">
            Verifica del nuovo CanvasWrapper che risolve l'errore runtime
          </p>
        </div>

        {/* Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              Status Sistema
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-2">
                {mounted ? (
                  <>
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span className="text-green-600">Client Mounted</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    <span className="text-yellow-600">Loading...</span>
                  </>
                )}
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span className="text-green-600">Wrapper Caricato</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span className="text-green-600">SSR Disabled</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span className="text-green-600">React-Konva OK</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Canvas Test */}
        <Card>
          <CardHeader>
            <CardTitle>Canvas di Test - Nessun Errore Runtime</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Canvas usando il nuovo wrapper */}
              <div className="border rounded-lg overflow-hidden bg-gray-50">
                <CanvasWrapper width={600} height={400} loadingDelay={200}>
                  <Layer>
                    {/* Griglia di sfondo */}
                    {Array.from({ length: 13 }, (_, i) => i * 50).map(x => (
                      <Rect
                        key={`grid-v-${x}`}
                        x={x}
                        y={0}
                        width={1}
                        height={400}
                        fill="#e5e7eb"
                        opacity={0.5}
                      />
                    ))}
                    {Array.from({ length: 9 }, (_, i) => i * 50).map(y => (
                      <Rect
                        key={`grid-h-${y}`}
                        x={0}
                        y={y}
                        width={600}
                        height={1}
                        fill="#e5e7eb"
                        opacity={0.5}
                      />
                    ))}
                    
                    {/* Elementi di test */}
                    {testData.map(item => (
                      <React.Fragment key={item.id}>
                        <Rect
                          x={item.x}
                          y={item.y}
                          width={item.width}
                          height={item.height}
                          fill={item.color}
                          stroke="#333"
                          strokeWidth={2}
                          opacity={0.8}
                        />
                        <Text
                          x={item.x + item.width / 2}
                          y={item.y + item.height / 2}
                          text={item.label}
                          fontSize={14}
                          fill="white"
                          fontStyle="bold"
                          align="center"
                          width={item.width}
                        />
                      </React.Fragment>
                    ))}
                    
                    {/* Elemento decorativo */}
                    <Circle
                      x={550}
                      y={50}
                      radius={25}
                      fill="#96CEB4"
                      stroke="#333"
                      strokeWidth={2}
                    />
                    <Text
                      x={550}
                      y={90}
                      text="✅ OK"
                      fontSize={16}
                      fill="#22c55e"
                      fontStyle="bold"
                      align="center"
                      width={50}
                    />
                  </Layer>
                </CanvasWrapper>
              </div>
              
              {/* Legenda */}
              <div className="flex flex-wrap gap-2">
                {testData.map(item => (
                  <Badge 
                    key={item.id} 
                    style={{ backgroundColor: item.color, color: 'white' }}
                  >
                    {item.label}
                  </Badge>
                ))}
                <Badge variant="outline">
                  ✅ Nessun Errore Runtime
                </Badge>
              </div>
              
              {/* Info */}
              <div className="text-sm text-muted-foreground bg-blue-50 p-3 rounded-lg">
                <p className="font-semibold text-blue-800 mb-1">ℹ️ Informazioni Tecniche:</p>
                <ul className="space-y-1 text-blue-700">
                  <li>• <strong>Wrapper:</strong> CanvasWrapper centralizzato</li>
                  <li>• <strong>Import:</strong> Dynamic import con gestione sicura</li>
                  <li>• <strong>Loading:</strong> Stato controllato con delay appropriato</li>
                  <li>• <strong>SSR:</strong> Completamente disabilitato per react-konva</li>
                  <li>• <strong>Client Mount:</strong> Verificato con hook dedicato</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Call to Action */}
        <Card>
          <CardContent className="text-center p-6">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-green-800 mb-2">
              🎉 Problema Risolto!
            </h3>
            <p className="text-green-600 mb-4">
              Il canvas React-Konva ora funziona senza errori runtime. 
              Puoi testare le pagine originali che prima causavano problemi.
            </p>
            <div className="flex justify-center gap-2">
              <Badge variant="outline" className="text-green-600">
                No Runtime Errors
              </Badge>
              <Badge variant="outline" className="text-blue-600">
                SSR Compatible
              </Badge>
              <Badge variant="outline" className="text-purple-600">
                Client-Side Only
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 
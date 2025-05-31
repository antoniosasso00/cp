'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Stage, Layer, Rect, Text, Group } from 'react-konva';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CheckCircle, X, RotateCw } from 'lucide-react';
import axios from 'axios';

// Interfacce TypeScript per i dati
interface ToolPosition {
  odl_id: number;
  x: number;
  y: number;
  width: number;
  height: number;
  peso: number;
  rotated?: boolean;
  part_number?: string;
  descrizione?: string;
  ciclo_cura?: string;
  tool_nome?: string;
}

interface ConfigurazioneLayout {
  canvas_width: number;
  canvas_height: number;
  scale_factor: number;
  tool_positions: ToolPosition[];
  plane_assignments: Record<string, number>;
}

interface BatchNestingData {
  id: string;
  nome: string;
  stato: string;
  autoclave_id: number;
  configurazione_json: ConfigurazioneLayout;
  peso_totale_kg: number;
  area_totale_utilizzata: number;
  numero_nesting: number;
  note: string;
  created_at: string;
  updated_at: string;
  // Informazioni dell'autoclave (saranno aggiunte dal backend)
  autoclave?: {
    nome: string;
    larghezza_piano: number;
    lunghezza: number;
    produttore: string;
  };
}

interface ODLEscluso {
  odl_id: number;
  part_number: string;
  descrizione: string;
  motivo: string;
  dettagli: string;
}

// Generatore di colori casuali per i tool
const generateToolColor = (index: number): string => {
  const colors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
    '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
  ];
  return colors[index % colors.length];
};

export default function NestingResultPage() {
  const params = useParams();
  const router = useRouter();
  const batch_id = params.batch_id as string;

  // States
  const [batchData, setBatchData] = useState<BatchNestingData | null>(null);
  const [odlEsclusi, setOdlEsclusi] = useState<ODLEscluso[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [canvasScale, setCanvasScale] = useState(1);
  const [canvasWidth, setCanvasWidth] = useState(800);
  const [canvasHeight, setCanvasHeight] = useState(600);
  const [selectedTool, setSelectedTool] = useState<ToolPosition | null>(null);
  const [isConfirming, setIsConfirming] = useState(false);

  // Recupera i dati del batch dal backend
  useEffect(() => {
    const fetchBatchData = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`/api/v1/batch_nesting/${batch_id}/full`);
        const data = response.data;
        
        console.log('📊 Dati batch ricevuti:', data);
        setBatchData(data);
        
        // Imposta gli ODL esclusi se presenti
        if (data.odl_esclusi && Array.isArray(data.odl_esclusi)) {
          setOdlEsclusi(data.odl_esclusi);
        }
        
        // Calcola la scala dinamica basata sulle dimensioni dell'autoclave
        if (data.configurazione_json) {
          const maxCanvasWidth = 800;
          const maxCanvasHeight = 600;
          const autoclaveWidth = data.configurazione_json.canvas_width || 2000;
          const autoclaveHeight = data.configurazione_json.canvas_height || 3000;
          
          const scaleX = maxCanvasWidth / autoclaveWidth;
          const scaleY = maxCanvasHeight / autoclaveHeight;
          const scale = Math.min(scaleX, scaleY, 1); // Non ingrandire mai oltre le dimensioni reali
          
          setCanvasScale(scale);
          setCanvasWidth(autoclaveWidth * scale);
          setCanvasHeight(autoclaveHeight * scale);
          
          console.log(`🔍 Scala calcolata: ${scale.toFixed(3)} (${autoclaveWidth}x${autoclaveHeight}mm → ${canvasWidth.toFixed(0)}x${canvasHeight.toFixed(0)}px)`);
        }
        
      } catch (err: any) {
        console.error('❌ Errore nel caricamento dati batch:', err);
        setError(err.response?.data?.detail || 'Errore nel caricamento dei dati');
      } finally {
        setLoading(false);
      }
    };

    if (batch_id) {
      fetchBatchData();
    }
  }, [batch_id]);

  // Funzione per rimuovere un ODL dalla configurazione
  const removeODL = (odlId: number) => {
    if (!batchData?.configurazione_json) return;

    const updatedPositions = batchData.configurazione_json.tool_positions.filter(
      tool => tool.odl_id !== odlId
    );

    setBatchData({
      ...batchData,
      configurazione_json: {
        ...batchData.configurazione_json,
        tool_positions: updatedPositions
      }
    });
  };

  // Funzione per confermare la configurazione
  const confirmConfiguration = async () => {
    try {
      setIsConfirming(true);
      
      await axios.put(`/api/v1/batch_nesting/${batch_id}`, {
        stato: 'confermato',
        confermato_da_utente: 'utente_frontend',
        confermato_da_ruolo: 'Curing'
      });
      
      setBatchData(prev => prev ? { ...prev, stato: 'confermato' } : null);
      alert('✅ Configurazione confermata con successo!');
      
    } catch (err: any) {
      console.error('❌ Errore nella conferma:', err);
      alert('❌ Errore nella conferma della configurazione');
    } finally {
      setIsConfirming(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-lg">Caricamento risultati nesting...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  // No data state
  if (!batchData) {
    return (
      <div className="container mx-auto p-6">
        <Alert>
          <AlertDescription>Nessun dato disponibile per questo batch.</AlertDescription>
        </Alert>
      </div>
    );
  }

  const toolPositions = batchData.configurazione_json?.tool_positions || [];
  const autoclaveWidth = batchData.configurazione_json?.canvas_width || 0;
  const autoclaveHeight = batchData.configurazione_json?.canvas_height || 0;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Risultato Nesting</h1>
          <p className="text-muted-foreground">
            Batch: {batchData.nome || batchData.id}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={batchData.stato === 'confermato' ? 'default' : 'secondary'}>
            {batchData.stato === 'confermato' ? <CheckCircle className="h-4 w-4 mr-1" /> : null}
            {batchData.stato.toUpperCase()}
          </Badge>
        </div>
      </div>

      {/* Layout principale */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Canvas principale */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Visualizzazione Nesting 2D</span>
                <div className="text-sm text-muted-foreground">
                  Autoclave: {autoclaveWidth}x{autoclaveHeight}mm • Scala: {(canvasScale * 100).toFixed(1)}%
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="border rounded-lg p-4 bg-gray-50">
                <Stage width={canvasWidth} height={canvasHeight}>
                  <Layer>
                    {/* Bordo dell'autoclave */}
                    <Rect
                      x={0}
                      y={0}
                      width={canvasWidth}
                      height={canvasHeight}
                      stroke="#333"
                      strokeWidth={2}
                      fill="rgba(240, 240, 240, 0.5)"
                    />
                    
                    {/* Griglia opzionale */}
                    {Array.from({ length: Math.floor(autoclaveWidth / 100) + 1 }, (_, i) => (
                      <Rect
                        key={`grid-v-${i}`}
                        x={i * 100 * canvasScale}
                        y={0}
                        width={1}
                        height={canvasHeight}
                        fill="rgba(200, 200, 200, 0.3)"
                      />
                    ))}
                    {Array.from({ length: Math.floor(autoclaveHeight / 100) + 1 }, (_, i) => (
                      <Rect
                        key={`grid-h-${i}`}
                        x={0}
                        y={i * 100 * canvasScale}
                        width={canvasWidth}
                        height={1}
                        fill="rgba(200, 200, 200, 0.3)"
                      />
                    ))}
                    
                    {/* Tool posizionati */}
                    {toolPositions.map((tool, index) => (
                      <Group
                        key={`tool-${tool.odl_id}`}
                        x={tool.x * canvasScale}
                        y={tool.y * canvasScale}
                        onMouseEnter={() => setSelectedTool(tool)}
                        onMouseLeave={() => setSelectedTool(null)}
                        onClick={() => {
                          if (window.confirm(`Rimuovere ODL ${tool.odl_id} dalla configurazione?`)) {
                            removeODL(tool.odl_id);
                          }
                        }}
                      >
                        {/* Rettangolo del tool */}
                        <Rect
                          width={tool.width * canvasScale}
                          height={tool.height * canvasScale}
                          fill={generateToolColor(index)}
                          stroke="#000"
                          strokeWidth={1}
                          opacity={selectedTool?.odl_id === tool.odl_id ? 0.8 : 0.7}
                        />
                        
                        {/* Testo del tool */}
                        <Text
                          x={(tool.width * canvasScale) / 2}
                          y={(tool.height * canvasScale) / 2 - 20}
                          text={`ODL ${tool.odl_id}`}
                          fontSize={12}
                          fontStyle="bold"
                          fill="#000"
                          align="center"
                          width={tool.width * canvasScale}
                        />
                        
                        <Text
                          x={(tool.width * canvasScale) / 2}
                          y={(tool.height * canvasScale) / 2}
                          text={tool.part_number || `Tool ${tool.odl_id}`}
                          fontSize={10}
                          fill="#000"
                          align="center"
                          width={tool.width * canvasScale}
                        />
                        
                        <Text
                          x={(tool.width * canvasScale) / 2}
                          y={(tool.height * canvasScale) / 2 + 15}
                          text={`${tool.width.toFixed(0)}x${tool.height.toFixed(0)}mm`}
                          fontSize={9}
                          fill="#666"
                          align="center"
                          width={tool.width * canvasScale}
                        />
                        
                        {/* Indicatore rotazione */}
                        {tool.rotated && (
                          <Group x={tool.width * canvasScale - 15} y={5}>
                            <Rect
                              width={12}
                              height={12}
                              fill="rgba(0, 0, 0, 0.7)"
                              cornerRadius={2}
                            />
                            <Text
                              x={6}
                              y={6}
                              text="↻"
                              fontSize={8}
                              fill="white"
                              align="center"
                              width={12}
                            />
                          </Group>
                        )}
                      </Group>
                    ))}
                  </Layer>
                </Stage>
              </div>
              
              {/* Tooltip per tool selezionato */}
              {selectedTool && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="text-sm">
                    <strong>ODL {selectedTool.odl_id}</strong>
                    <span className="ml-2">
                      {selectedTool.rotated && <RotateCw className="inline h-4 w-4 mr-1" />}
                    </span>
                  </div>
                  <div className="text-xs text-gray-600">
                    Posizione: ({selectedTool.x.toFixed(0)}, {selectedTool.y.toFixed(0)})mm
                    <br />
                    Dimensioni: {selectedTool.width.toFixed(0)}x{selectedTool.height.toFixed(0)}mm
                    <br />
                    Peso: {selectedTool.peso.toFixed(1)}kg
                    {selectedTool.rotated && <span className="text-orange-600"> • Ruotato 90°</span>}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Pannello informazioni */}
        <div className="space-y-4">
          
          {/* Statistiche */}
          <Card>
            <CardHeader>
              <CardTitle>Statistiche Nesting</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span>Tool posizionati:</span>
                <span className="font-semibold">{toolPositions.length}</span>
              </div>
              <div className="flex justify-between">
                <span>Peso totale:</span>
                <span className="font-semibold">{batchData.peso_totale_kg.toFixed(1)} kg</span>
              </div>
              <div className="flex justify-between">
                <span>Area utilizzata:</span>
                <span className="font-semibold">{(batchData.area_totale_utilizzata / 10000).toFixed(2)} m²</span>
              </div>
              <div className="flex justify-between">
                <span>Efficienza:</span>
                <span className="font-semibold">
                  {((batchData.area_totale_utilizzata / (autoclaveWidth * autoclaveHeight)) * 100).toFixed(1)}%
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Azioni */}
          <Card>
            <CardHeader>
              <CardTitle>Azioni</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {batchData.stato === 'sospeso' && (
                <Button 
                  onClick={confirmConfiguration}
                  disabled={isConfirming}
                  className="w-full"
                >
                  {isConfirming ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <CheckCircle className="h-4 w-4 mr-2" />
                  )}
                  Accetta Configurazione
                </Button>
              )}
              
              <Button 
                variant="outline" 
                onClick={() => router.back()}
                className="w-full"
              >
                Torna Indietro
              </Button>
            </CardContent>
          </Card>

          {/* Informazioni batch */}
          <Card>
            <CardHeader>
              <CardTitle>Dettagli Batch</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div>
                <strong>ID:</strong> {batchData.id}
              </div>
              <div>
                <strong>Creato:</strong> {new Date(batchData.created_at).toLocaleString('it-IT')}
              </div>
              <div>
                <strong>Aggiornato:</strong> {new Date(batchData.updated_at).toLocaleString('it-IT')}
              </div>
              {batchData.autoclave && (
                <>
                  <Separator className="my-2" />
                  <div>
                    <strong>Autoclave:</strong> {batchData.autoclave.nome}
                  </div>
                  <div>
                    <strong>Produttore:</strong> {batchData.autoclave.produttore}
                  </div>
                  <div>
                    <strong>Dimensioni piano:</strong> {batchData.autoclave.larghezza_piano}x{batchData.autoclave.lunghezza}mm
                  </div>
                </>
              )}
              {batchData.note && (
                <>
                  <Separator className="my-2" />
                  <div>
                    <strong>Note:</strong> 
                    <p className="text-gray-600 mt-1">{batchData.note}</p>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* ODL Esclusi */}
      {odlEsclusi.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <X className="h-5 w-5 mr-2 text-red-500" />
              ODL Esclusi ({odlEsclusi.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">ODL ID</th>
                    <th className="text-left py-2">Part Number</th>
                    <th className="text-left py-2">Descrizione</th>
                    <th className="text-left py-2">Motivo Esclusione</th>
                  </tr>
                </thead>
                <tbody>
                  {odlEsclusi.map((odl) => (
                    <tr key={odl.odl_id} className="border-b">
                      <td className="py-2">{odl.odl_id}</td>
                      <td className="py-2">{odl.part_number}</td>
                      <td className="py-2">{odl.descrizione}</td>
                      <td className="py-2 text-red-600">{odl.motivo}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 
import { NestingResponse } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { formatDateIT } from '@/lib/utils'
import { X, Download, Info, ZoomIn, ZoomOut, Search, AlertTriangle } from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { useRef, useState } from 'react'

interface NestingDetailsProps {
  nesting: NestingResponse
  isOpen: boolean
  onClose: () => void
}

// Interfaccia per rappresentare un ODL posizionato nel layout
interface PositionedODL {
  odl: NestingResponse['odl_list'][0]
  x: number
  y: number
  width: number
  height: number
}

export function NestingDetails({ nesting, isOpen, onClose }: NestingDetailsProps) {
  if (!nesting) return null

  // Ref per l'elemento dell'anteprima da esportare
  const previewRef = useRef<HTMLDivElement>(null)
  
  // Stato per il controllo dello zoom
  const [zoomLevel, setZoomLevel] = useState(1)

  // Stato per gestire l'ODL in hover
  const [hoveredODL, setHoveredODL] = useState<NestingResponse['odl_list'][0] | null>(null)

  // Stato per la ricerca ODL
  const [searchTerm, setSearchTerm] = useState('')

  // Calcola le percentuali di utilizzo
  const areaPercentage = nesting.area_totale ? Math.round((nesting.area_utilizzata / nesting.area_totale) * 100) : 0
  const valvolePercentage = nesting.valvole_totali ? Math.round((nesting.valvole_utilizzate / nesting.valvole_totali) * 100) : 0

  // Dimensioni del canvas per l'anteprima
  const canvasWidth = 800; // Aumentata per migliore visualizzazione
  const canvasHeight = 500;
  
  // Converti dimensioni da millimetri a unità canvas con fattore di scala appropriato
  // Assumendo che le dimensioni dell'autoclave siano in millimetri
  const MM_TO_PIXEL_SCALE = 0.3; // 1mm = 0.3 pixel (aumentato per migliore visibilità)
  
  const autoclaveWidthMM = nesting.autoclave.lunghezza;
  const autoclaveHeightMM = nesting.autoclave.larghezza_piano;
  
  // Calcola il fattore di scala per adattare l'autoclave al canvas
  const scaleX = (canvasWidth * 0.85) / (autoclaveWidthMM * MM_TO_PIXEL_SCALE);
  const scaleY = (canvasHeight * 0.85) / (autoclaveHeightMM * MM_TO_PIXEL_SCALE);
  const scale = Math.min(scaleX, scaleY);

  // Dimensioni dell'autoclave nel canvas
  const autoclaveWidth = autoclaveWidthMM * MM_TO_PIXEL_SCALE * scale;
  const autoclaveHeight = autoclaveHeightMM * MM_TO_PIXEL_SCALE * scale;
  
  // Debug: log delle dimensioni dell'autoclave
  console.log('🏭 Autoclave Debug:', {
    originalMM: `${autoclaveWidthMM}x${autoclaveHeightMM}`,
    canvasSize: `${canvasWidth}x${canvasHeight}`,
    mmToPixelScale: MM_TO_PIXEL_SCALE,
    scaleFactors: { scaleX: scaleX.toFixed(3), scaleY: scaleY.toFixed(3), finalScale: scale.toFixed(3) },
    finalAutoclaveSize: `${autoclaveWidth.toFixed(1)}x${autoclaveHeight.toFixed(1)}`
  });
  
  // Margini per centrare l'autoclave
  const marginLeft = (canvasWidth - autoclaveWidth) / 2;
  const marginTop = (canvasHeight - autoclaveHeight) / 2;

  // 🔧 ALGORITMO SEMPLIFICATO E ROBUSTO PER IL POSIZIONAMENTO DEGLI ODL
  const calculateODLPositions = (): PositionedODL[] => {
    const positioned: PositionedODL[] = [];
    
    const padding = 5; // Spaziatura minima tra gli ODL
    const contentPadding = 8; // Padding dal bordo dell'autoclave
    const availableWidth = Math.max(autoclaveWidth - (contentPadding * 2), 100);
    const availableHeight = Math.max(autoclaveHeight - (contentPadding * 2), 100);
    
    // Debug: log delle dimensioni
    console.log('🔍 Debug Layout:', {
      autoclaveWidth: autoclaveWidth.toFixed(1),
      autoclaveHeight: autoclaveHeight.toFixed(1),
      availableWidth: availableWidth.toFixed(1),
      availableHeight: availableHeight.toFixed(1),
      scale: scale.toFixed(3),
      odlCount: nesting.odl_list.length
    });
    
    // Se l'autoclave è troppo piccola, usa un layout a griglia semplice
    if (availableWidth < 50 || availableHeight < 50) {
      console.log('⚠️ Autoclave troppo piccola, uso layout a griglia forzato');
      
      // Layout a griglia forzato per autoclavi molto piccole
      const cols = Math.max(2, Math.floor(Math.sqrt(nesting.odl_list.length)));
      const rows = Math.ceil(nesting.odl_list.length / cols);
      const cellWidth = Math.max(30, availableWidth / cols - padding);
      const cellHeight = Math.max(20, availableHeight / rows - padding);
      
      nesting.odl_list.forEach((odl, index) => {
        const col = index % cols;
        const row = Math.floor(index / cols);
        
        positioned.push({
          odl,
          x: contentPadding + col * (cellWidth + padding),
          y: contentPadding + row * (cellHeight + padding),
          width: cellWidth,
          height: cellHeight
        });
      });
      
      console.log(`✅ Layout griglia: ${positioned.length}/${nesting.odl_list.length} ODL posizionati`);
      return positioned;
    }
    
    // Layout normale per autoclavi di dimensioni adeguate
    let currentX = contentPadding;
    let currentY = contentPadding;
    let rowHeight = 0;
    
    for (const odl of nesting.odl_list) {
      // Calcola dimensioni del tool nel canvas
      const toolWidthMM = odl.tool.lunghezza_piano || 100; // Default se mancante
      const toolHeightMM = odl.tool.larghezza_piano || 50; // Default se mancante
      
      // Calcola dimensioni scalate con minimi ragionevoli
      let toolWidth = Math.max(toolWidthMM * MM_TO_PIXEL_SCALE * scale, 25);
      let toolHeight = Math.max(toolHeightMM * MM_TO_PIXEL_SCALE * scale, 15);
      
      // Limita le dimensioni massime per evitare ODL troppo grandi
      const maxWidth = availableWidth * 0.4; // Max 40% della larghezza
      const maxHeight = availableHeight * 0.3; // Max 30% dell'altezza
      
      toolWidth = Math.min(toolWidth, maxWidth);
      toolHeight = Math.min(toolHeight, maxHeight);
      
      // Debug: log delle dimensioni dell'ODL
      console.log(`📦 ODL #${odl.id}:`, {
        originalMM: `${toolWidthMM}x${toolHeightMM}`,
        scaledPx: `${toolWidth.toFixed(1)}x${toolHeight.toFixed(1)}`,
        position: `${currentX.toFixed(1)},${currentY.toFixed(1)}`
      });
      
      // Controlla se l'ODL entra nella riga corrente
      if (currentX + toolWidth > contentPadding + availableWidth && positioned.length > 0) {
        // Va a capo
        currentX = contentPadding;
        currentY += rowHeight + padding;
        rowHeight = 0;
      }
      
      // Controlla se c'è spazio verticale
      if (currentY + toolHeight <= contentPadding + availableHeight) {
        positioned.push({
          odl,
          x: currentX,
          y: currentY,
          width: toolWidth,
          height: toolHeight
        });
        
        currentX += toolWidth + padding;
        rowHeight = Math.max(rowHeight, toolHeight);
      } else {
        console.log(`❌ ODL #${odl.id} non posizionato - spazio verticale insufficiente`);
        break; // Ferma il posizionamento se non c'è più spazio verticale
      }
    }
    
    console.log(`✅ Posizionati ${positioned.length}/${nesting.odl_list.length} ODL`);
    return positioned;
  };

  // Calcola le posizioni degli ODL
  const positionedODLs = calculateODLPositions();

  // Funzione per ottenere il colore dell'ODL basato sulla priorità
  const getODLColor = (odl: NestingResponse['odl_list'][0]) => {
    const priorita = odl.priorita || 5;
    if (priorita <= 2) {
      return 'bg-red-100 border-red-400 text-red-800 hover:bg-red-200'; // Priorità alta
    } else if (priorita <= 4) {
      return 'bg-yellow-100 border-yellow-400 text-yellow-800 hover:bg-yellow-200'; // Priorità media
    } else {
      return 'bg-blue-100 border-blue-400 text-blue-800 hover:bg-blue-200'; // Priorità bassa
    }
  };

  // Funzione per scaricare l'anteprima come immagine PNG
  const downloadPreview = async () => {
    if (!previewRef.current) return
    
    try {
      // Importa html2canvas dinamicamente per evitare errori SSR
      const html2canvas = (await import('html2canvas')).default
      
      const canvas = await html2canvas(previewRef.current)
      
      // Crea il link per il download
      const link = document.createElement('a')
      link.download = `nesting-${nesting.id}-preview.png`
      link.href = canvas.toDataURL('image/png')
      
      // Trigger del download
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
    } catch (error) {
      console.error('Errore durante l\'export dell\'anteprima:', error)
      // Qui potresti aggiungere un toast di errore se disponibile
    }
  }

  // Funzioni per il controllo dello zoom
  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 0.2, 3))
  }
  
  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 0.2, 0.5))
  }

  // Funzione per verificare se un ODL corrisponde alla ricerca
  const matchesSearch = (odl: NestingResponse['odl_list'][0]) => {
    if (!searchTerm) return false
    const term = searchTerm.toLowerCase()
    return (
      odl.id.toString().includes(term) ||
      odl.parte.part_number.toLowerCase().includes(term) ||
      odl.parte.descrizione_breve.toLowerCase().includes(term) ||
      odl.tool.part_number_tool.toLowerCase().includes(term)
    )
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[900px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="flex items-center gap-2">
                <Info className="h-5 w-5" />
                Dettagli Nesting #{nesting.id}
              </DialogTitle>
              <DialogDescription>
                Creato il {formatDateIT(new Date(nesting.created_at))}
              </DialogDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={downloadPreview}>
                <Download className="h-4 w-4 mr-1" />
                Esporta PNG
              </Button>
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Informazioni Autoclave */}
          <div className="bg-slate-50 p-4 rounded-lg">
            <h3 className="text-lg font-medium mb-2">Informazioni Autoclave</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="font-medium">{nesting.autoclave.nome}</p>
                <p className="text-muted-foreground">Codice: {nesting.autoclave.codice}</p>
                <p className="text-muted-foreground">ID: {nesting.autoclave.id}</p>
              </div>
              <div>
                <p className="text-muted-foreground">
                  Dimensioni: {nesting.autoclave.lunghezza} × {nesting.autoclave.larghezza_piano} mm
                </p>
                <p className="text-muted-foreground">
                  Linee vuoto: {nesting.autoclave.num_linee_vuoto}
                </p>
              </div>
            </div>
          </div>

          {/* Statistiche Utilizzo */}
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium">Utilizzo Area</h4>
                <Badge variant={areaPercentage > 80 ? "default" : areaPercentage > 60 ? "secondary" : "outline"}>
                  {areaPercentage}%
                </Badge>
              </div>
              <Progress value={areaPercentage} className="h-3" />
              <p className="text-xs text-muted-foreground">
                {nesting.area_utilizzata.toFixed(2)} m² / {nesting.area_totale.toFixed(2)} m²
              </p>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium">Utilizzo Valvole</h4>
                <Badge variant={valvolePercentage > 80 ? "default" : valvolePercentage > 60 ? "secondary" : "outline"}>
                  {valvolePercentage}%
                </Badge>
              </div>
              <Progress value={valvolePercentage} className="h-3" />
              <p className="text-xs text-muted-foreground">
                {nesting.valvole_utilizzate} / {nesting.valvole_totali}
              </p>
            </div>
          </div>

          {/* Tabella ODL */}
          <div>
            <h3 className="text-lg font-medium mb-3">ODL Inclusi ({nesting.odl_list.length})</h3>
            <div className="border rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID ODL</TableHead>
                    <TableHead>Part Number</TableHead>
                    <TableHead>Descrizione</TableHead>
                    <TableHead>Tool</TableHead>
                    <TableHead>Dimensioni (mm)</TableHead>
                    <TableHead>Valvole</TableHead>
                    <TableHead>Priorità</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {nesting.odl_list.map((odl, index) => (
                    <TableRow key={odl.id}>
                      <TableCell className="font-medium">#{odl.id}</TableCell>
                      <TableCell>{odl.parte.part_number}</TableCell>
                      <TableCell className="max-w-[200px] truncate" title={odl.parte.descrizione_breve}>
                        {odl.parte.descrizione_breve}
                      </TableCell>
                      <TableCell>{odl.tool.part_number_tool}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {odl.tool.lunghezza_piano} × {odl.tool.larghezza_piano}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{odl.parte.num_valvole_richieste}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={odl.priorita <= 2 ? "destructive" : odl.priorita <= 4 ? "default" : "secondary"}>
                          {odl.priorita}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
          
          {/* Anteprima Layout Migliorata */}
          {nesting.odl_list.length > 0 && (
            <div>
              <div className="space-y-3 mb-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium">Anteprima Layout</h3>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1">
                      <Button variant="outline" size="sm" onClick={handleZoomOut}>
                        <ZoomOut className="h-4 w-4" />
                      </Button>
                      <span className="text-sm text-muted-foreground min-w-[60px] text-center">
                        {Math.round(zoomLevel * 100)}%
                      </span>
                      <Button variant="outline" size="sm" onClick={handleZoomIn}>
                        <ZoomIn className="h-4 w-4" />
                      </Button>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {positionedODLs.length} / {nesting.odl_list.length} ODL posizionati
                    </p>
                  </div>
                </div>
                
                {/* Campo di ricerca ODL */}
                <div className="relative max-w-sm">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Cerca ODL per ID, Part Number o Tool..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              
              <div 
                ref={previewRef}
                className="border-2 border-slate-300 rounded-lg p-4 bg-slate-100 dark:bg-slate-800 dark:border-slate-600 relative overflow-auto shadow-inner" 
                style={{ 
                  width: canvasWidth, 
                  height: canvasHeight,
                }}
              >
                {/* Contenitore dell'autoclave */}
                <div 
                  className="absolute bg-white dark:bg-slate-700 border-4 border-slate-700 dark:border-slate-400 shadow-xl rounded-lg transition-transform" 
                  style={{ 
                    width: autoclaveWidth * zoomLevel, 
                    height: autoclaveHeight * zoomLevel,
                    left: marginLeft,
                    top: marginTop,
                    transform: `scale(${zoomLevel})`,
                    transformOrigin: 'top left'
                  }}
                >
                  {/* Griglia di sfondo migliorata per migliore visibilità */}
                  <div 
                    className="absolute inset-0 opacity-20 dark:opacity-30"
                    style={{
                      backgroundImage: `
                        linear-gradient(to right, #64748b 1px, transparent 1px),
                        linear-gradient(to bottom, #64748b 1px, transparent 1px)
                      `,
                      backgroundSize: '25px 25px'
                    }}
                  />
                  
                  {/* Griglia secondaria più fine */}
                  <div 
                    className="absolute inset-0 opacity-10 dark:opacity-15"
                    style={{
                      backgroundImage: `
                        linear-gradient(to right, #94a3b8 1px, transparent 1px),
                        linear-gradient(to bottom, #94a3b8 1px, transparent 1px)
                      `,
                      backgroundSize: '5px 5px'
                    }}
                  />
                  
                  {/* ODL posizionati con l'algoritmo migliorato */}
                  {positionedODLs.map((positioned, index) => {
                    const isSearchMatch = matchesSearch(positioned.odl)
                    const isHighlighted = hoveredODL?.id === positioned.odl.id
                    const shouldDim = searchTerm && !isSearchMatch
                    
                    return (
                      <div
                        key={positioned.odl.id}
                        className={`absolute border-2 flex flex-col justify-center items-center text-xs font-medium transition-all hover:z-20 hover:shadow-xl hover:scale-110 cursor-pointer rounded-md ${getODLColor(positioned.odl)} ${isHighlighted ? 'ring-4 ring-blue-500 shadow-xl z-10 scale-105' : ''} ${isSearchMatch ? 'ring-3 ring-yellow-400 shadow-lg' : ''} ${shouldDim ? 'opacity-30' : ''}`}
                        style={{
                          width: positioned.width,
                          height: positioned.height,
                          left: positioned.x,
                          top: positioned.y,
                          minWidth: '80px',
                          minHeight: '50px'
                        }}
                        onMouseEnter={() => setHoveredODL(positioned.odl)}
                        onMouseLeave={() => setHoveredODL(null)}
                        title={`ODL #${positioned.odl.id} - ${positioned.odl.parte.part_number}\nTool: ${positioned.odl.tool.part_number_tool}\nDimensioni: ${positioned.odl.tool.lunghezza_piano}×${positioned.odl.tool.larghezza_piano}mm\nValvole: ${positioned.odl.parte.num_valvole_richieste}\nPriorità: ${positioned.odl.priorita}`}
                      >
                        <span className="truncate px-1 font-bold text-sm" style={{ maxWidth: positioned.width - 8 }}>
                          #{positioned.odl.id}
                        </span>
                        <span className="truncate px-1 text-xs font-medium" style={{ maxWidth: positioned.width - 8 }}>
                          {positioned.odl.parte.part_number}
                        </span>
                        <div className="flex items-center gap-1 text-[10px] opacity-90">
                          <span>V:{positioned.odl.parte.num_valvole_richieste}</span>
                          <span>•</span>
                          <span>P:{positioned.odl.priorita}</span>
                        </div>
                      </div>
                    )
                  })}
                  
                  {/* Indicatore per ODL non posizionati - migliorato */}
                  {positionedODLs.length < nesting.odl_list.length && (
                    <div className="absolute bottom-3 right-3 bg-red-100 dark:bg-red-900 border-2 border-red-400 dark:border-red-600 text-red-800 dark:text-red-200 px-3 py-2 rounded-lg text-sm font-medium shadow-lg">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4" />
                        <span>{nesting.odl_list.length - positionedODLs.length} ODL non visualizzati</span>
                      </div>
                      <div className="text-xs opacity-75 mt-1">
                        Spazio insufficiente nell'autoclave
                      </div>
                    </div>
                  )}
                  
                  {/* Messaggio se nessun ODL è posizionato */}
                  {positionedODLs.length === 0 && nesting.odl_list.length > 0 && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="bg-yellow-100 dark:bg-yellow-900 border-2 border-yellow-400 dark:border-yellow-600 text-yellow-800 dark:text-yellow-200 px-6 py-4 rounded-lg text-center shadow-lg max-w-md">
                        <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
                        <div className="font-medium">Nessun ODL visualizzabile</div>
                        <div className="text-sm opacity-75 mt-1">
                          Gli ODL potrebbero essere troppo grandi per questa visualizzazione o l'autoclave potrebbe essere troppo piccola.
                        </div>
                        <div className="text-xs opacity-60 mt-2">
                          Controlla la console del browser per dettagli di debug.
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Visualizzazione semplificata se il posizionamento fallisce */}
                  {positionedODLs.length === 0 && nesting.odl_list.length > 0 && (
                    <div className="absolute bottom-16 left-3 right-3">
                      <div className="bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
                        <div className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
                          Lista ODL (visualizzazione semplificata):
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {nesting.odl_list.slice(0, 8).map((odl, index) => (
                            <div
                              key={odl.id}
                              className={`px-2 py-1 rounded text-xs font-medium ${getODLColor(odl)}`}
                              title={`ODL #${odl.id} - ${odl.parte.part_number}`}
                            >
                              #{odl.id}
                            </div>
                          ))}
                          {nesting.odl_list.length > 8 && (
                            <div className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-600">
                              +{nesting.odl_list.length - 8}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Etichetta con informazioni migliorata */}
                <div className="absolute bottom-3 left-3 bg-white/95 dark:bg-slate-800/95 border-2 border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-700 dark:text-slate-300 shadow-lg">
                  <div className="font-medium">Autoclave: {nesting.autoclave.nome}</div>
                  <div className="text-xs opacity-75">
                    Dimensioni: {nesting.autoclave.lunghezza} × {nesting.autoclave.larghezza_piano} mm
                  </div>
                  <div className="text-xs opacity-75">
                    Scala: 1:{Math.round(1/scale)}x • Zoom: {Math.round(zoomLevel * 100)}%
                  </div>
                </div>
                
                {/* Legenda colori migliorata */}
                <div className="absolute top-3 right-3 bg-white/95 dark:bg-slate-800/95 border-2 border-slate-300 dark:border-slate-600 rounded-lg p-3 text-xs shadow-lg">
                  <div className="font-medium mb-2 text-slate-700 dark:text-slate-300">Legenda Priorità:</div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 bg-red-100 border-2 border-red-400 rounded"></div>
                      <span className="text-slate-600 dark:text-slate-400">Alta (1-2)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 bg-yellow-100 border-2 border-yellow-400 rounded"></div>
                      <span className="text-slate-600 dark:text-slate-400">Media (3-4)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 bg-blue-100 border-2 border-blue-400 rounded"></div>
                      <span className="text-slate-600 dark:text-slate-400">Bassa (5+)</span>
                    </div>
                  </div>
                </div>
                
                {/* Indicatore di stato del nesting */}
                <div className="absolute top-3 left-3 bg-white/95 dark:bg-slate-800/95 border-2 border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-xs shadow-lg">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${
                      nesting.stato === 'Schedulato' ? 'bg-green-500' :
                      nesting.stato === 'In corso' ? 'bg-blue-500' :
                      nesting.stato === 'Completato' ? 'bg-gray-500' :
                      'bg-yellow-500'
                    }`}></div>
                    <span className="font-medium text-slate-700 dark:text-slate-300">{nesting.stato}</span>
                  </div>
                  <div className="text-[10px] opacity-75 text-slate-600 dark:text-slate-400 mt-1">
                    ODL: {positionedODLs.length}/{nesting.odl_list.length}
                  </div>
                </div>
              </div>
              
              {/* Pannello informativo per ODL in hover */}
              {hoveredODL && (
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-semibold text-blue-900 mb-2">Dettagli ODL #{hoveredODL.id}</h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p><strong>Part Number:</strong> {hoveredODL.parte.part_number}</p>
                      <p><strong>Descrizione:</strong> {hoveredODL.parte.descrizione_breve}</p>
                      <p><strong>Tool:</strong> {hoveredODL.tool.part_number_tool}</p>
                    </div>
                    <div>
                      <p><strong>Dimensioni:</strong> {hoveredODL.tool.lunghezza_piano} × {hoveredODL.tool.larghezza_piano} mm</p>
                      <p><strong>Valvole:</strong> {hoveredODL.parte.num_valvole_richieste}</p>
                      <p><strong>Priorità:</strong> 
                        <Badge variant={hoveredODL.priorita <= 2 ? "destructive" : hoveredODL.priorita <= 4 ? "default" : "secondary"} className="ml-1">
                          {hoveredODL.priorita}
                        </Badge>
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
} 
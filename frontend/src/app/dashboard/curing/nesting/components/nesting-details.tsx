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
  piano?: 1 | 2  // ✅ Campo opzionale per indicare il piano
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
  const canvasWidth = 800
  const canvasHeight = 500
  
  // Converti dimensioni da millimetri a unità canvas con fattore di scala appropriato
  const MM_TO_PIXEL_SCALE = 0.3 // 1mm = 0.3 pixel
  
  const autoclaveWidthMM = nesting.autoclave.lunghezza
  const autoclaveHeightMM = nesting.autoclave.larghezza_piano
  
  // Calcola il fattore di scala per adattare l'autoclave al canvas
  const scaleX = (canvasWidth * 0.85) / (autoclaveWidthMM * MM_TO_PIXEL_SCALE)
  const scaleY = (canvasHeight * 0.85) / (autoclaveHeightMM * MM_TO_PIXEL_SCALE)
  const scale = Math.min(scaleX, scaleY)

  // Dimensioni dell'autoclave nel canvas
  const autoclaveWidth = autoclaveWidthMM * MM_TO_PIXEL_SCALE * scale
  const autoclaveHeight = autoclaveHeightMM * MM_TO_PIXEL_SCALE * scale
  
  // Margini per centrare l'autoclave
  const marginLeft = (canvasWidth - autoclaveWidth) / 2
  const marginTop = (canvasHeight - autoclaveHeight) / 2

  // ✅ Utilizza le posizioni reali calcolate dal backend
  const calculateODLPositions = (): PositionedODL[] => {
    const positioned: PositionedODL[] = []
    
    // Se abbiamo posizioni reali dal backend, usale
    if (nesting.posizioni_tool && nesting.posizioni_tool.length > 0) {
      console.log('✅ Utilizzo posizioni reali dal backend')
      
      for (const posizione of nesting.posizioni_tool) {
        // Trova l'ODL corrispondente
        const odl = nesting.odl_list.find(o => o.id === posizione.odl_id)
        if (!odl) {
          console.warn(`⚠️ ODL ${posizione.odl_id} non trovato nella lista`)
          continue
        }
        
        // Converti le coordinate da mm a pixel
        const x = (posizione.x * MM_TO_PIXEL_SCALE * scale)
        const y = (posizione.y * MM_TO_PIXEL_SCALE * scale)
        const width = (posizione.width * MM_TO_PIXEL_SCALE * scale)
        const height = (posizione.height * MM_TO_PIXEL_SCALE * scale)
        
        positioned.push({
          odl,
          x: Math.max(0, x),
          y: Math.max(0, y),
          width: Math.max(20, width),
          height: Math.max(15, height),
          piano: posizione.piano || 1  // Default piano 1 se non specificato
        })
      }
      
      console.log(`✅ Posizionati ${positioned.length} ODL con coordinate reali`)
      return positioned
    }
    
    // ⚠️ FALLBACK: Se non abbiamo posizioni dal backend, usa layout a griglia
    console.log('⚠️ Nessuna posizione dal backend, uso layout a griglia di fallback')
    
    const padding = 8
    const contentPadding = 10
    const availableWidth = Math.max(autoclaveWidth - (contentPadding * 2), 100)
    const availableHeight = Math.max(autoclaveHeight - (contentPadding * 2), 100)
    
    const cols = Math.max(2, Math.floor(Math.sqrt(nesting.odl_list.length)))
    const rows = Math.ceil(nesting.odl_list.length / cols)
    const cellWidth = Math.max(40, (availableWidth - (cols - 1) * padding) / cols)
    const cellHeight = Math.max(30, (availableHeight - (rows - 1) * padding) / rows)
    
    nesting.odl_list.forEach((odl, index) => {
      const col = index % cols
      const row = Math.floor(index / cols)
      
      positioned.push({
        odl,
        x: contentPadding + col * (cellWidth + padding),
        y: contentPadding + row * (cellHeight + padding),
        width: cellWidth,
        height: cellHeight,
        piano: 1 // Default piano 1
      })
    })
    
    console.log(`✅ Layout griglia fallback: ${positioned.length}/${nesting.odl_list.length} ODL posizionati`)
    return positioned
  }

  // Calcola le posizioni degli ODL
  const positionedODLs = calculateODLPositions()

  // Funzione per ottenere il colore dell'ODL basato sulla priorità
  const getODLColor = (odl: NestingResponse['odl_list'][0]) => {
    const priorita = odl.priorita || 5
    if (priorita <= 2) {
      return 'bg-red-100 border-red-400 text-red-800 hover:bg-red-200' // Priorità alta
    } else if (priorita <= 4) {
      return 'bg-yellow-100 border-yellow-400 text-yellow-800 hover:bg-yellow-200' // Priorità media
    } else {
      return 'bg-blue-100 border-blue-400 text-blue-800 hover:bg-blue-200' // Priorità bassa
    }
  }

  // Funzione per scaricare l'anteprima come immagine PNG
  const downloadPreview = async () => {
    if (!previewRef.current) return

    try {
      const html2canvas = (await import('html2canvas')).default
      const canvas = await html2canvas(previewRef.current)

      const link = document.createElement('a')
      link.download = `nesting-${nesting.id}-preview.png`
      link.href = canvas.toDataURL()
      link.click()
    } catch (error) {
      console.error('Errore durante l\'esportazione:', error)
    }
  }

  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 0.2, 3))
  }

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 0.2, 0.5))
  }

  const matchesSearch = (odl: NestingResponse['odl_list'][0]) => {
    if (!searchTerm) return true
    const searchLower = searchTerm.toLowerCase()
    return (
      odl.id.toString().includes(searchLower) ||
      odl.parte.part_number.toLowerCase().includes(searchLower) ||
      odl.tool.part_number_tool.toLowerCase().includes(searchLower) ||
      odl.parte.descrizione_breve.toLowerCase().includes(searchLower)
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
                {/* ✅ Visualizzazione ciclo di cura */}
                {nesting.ciclo_cura_nome && (
                  <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded">
                    <p className="text-blue-800 font-medium text-xs">Ciclo di Cura</p>
                    <p className="text-blue-700 font-semibold">{nesting.ciclo_cura_nome}</p>
                    {nesting.ciclo_cura_id && (
                      <p className="text-blue-600 text-xs">ID: {nesting.ciclo_cura_id}</p>
                    )}
                  </div>
                )}
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
                    <TableHead>Piano</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {nesting.odl_list.map((odl) => {
                    const posizione = nesting.posizioni_tool?.find(p => p.odl_id === odl.id)
                    return (
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
                        <TableCell>
                          <Badge variant="outline">
                            Piano {posizione?.piano || 1}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          </div>
          
          {/* Anteprima Layout */}
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
                  {/* Griglia di sfondo */}
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
                  
                  {/* ✅ Etichetta ciclo di cura nell'anteprima */}
                  {nesting.ciclo_cura_nome && (
                    <div className="absolute top-2 left-2 bg-blue-100 dark:bg-blue-900 border border-blue-300 dark:border-blue-700 text-blue-800 dark:text-blue-200 px-2 py-1 rounded text-xs font-medium shadow-sm">
                      🔄 {nesting.ciclo_cura_nome}
                    </div>
                  )}
                  
                  {/* ODL posizionati */}
                  {positionedODLs.map((positioned) => {
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
                        title={`ODL #${positioned.odl.id} - ${positioned.odl.parte.part_number}\nTool: ${positioned.odl.tool.part_number_tool}\nDimensioni: ${positioned.odl.tool.lunghezza_piano}×${positioned.odl.tool.larghezza_piano}mm\nValvole: ${positioned.odl.parte.num_valvole_richieste}\nPriorità: ${positioned.odl.priorita}\nPiano: ${positioned.piano || 1}`}
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
                          <span>•</span>
                          <span>Piano {positioned.piano || 1}</span>
                        </div>
                      </div>
                    )
                  })}
                  
                  {/* Indicatore per ODL non posizionati */}
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
                </div>
                
                {/* Etichetta con informazioni */}
                <div className="absolute bottom-3 left-3 bg-white/95 dark:bg-slate-800/95 border-2 border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-700 dark:text-slate-300 shadow-lg">
                  <div className="font-medium">Autoclave: {nesting.autoclave.nome}</div>
                  <div className="text-xs opacity-75">
                    Dimensioni: {nesting.autoclave.lunghezza} × {nesting.autoclave.larghezza_piano} mm
                  </div>
                  <div className="text-xs opacity-75">
                    Scala: 1:{Math.round(1/scale)}x • Zoom: {Math.round(zoomLevel * 100)}%
                  </div>
                </div>
                
                {/* Legenda colori */}
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
import { NestingResponse } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { formatDateIT } from '@/lib/utils'
import { X, Download, Info } from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'

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

  // Calcola le percentuali di utilizzo
  const areaPercentage = nesting.area_totale ? Math.round((nesting.area_utilizzata / nesting.area_totale) * 100) : 0
  const valvolePercentage = nesting.valvole_totali ? Math.round((nesting.valvole_utilizzate / nesting.valvole_totali) * 100) : 0

  // Dimensioni del canvas per l'anteprima
  const canvasWidth = 800; // Aumentata per migliore visualizzazione
  const canvasHeight = 500;
  
  // Converti dimensioni da millimetri a unità canvas con fattore di scala appropriato
  // Assumendo che le dimensioni dell'autoclave siano in millimetri
  const MM_TO_PIXEL_SCALE = 0.1; // 1mm = 0.1 pixel (regolabile)
  
  const autoclaveWidthMM = nesting.autoclave.lunghezza;
  const autoclaveHeightMM = nesting.autoclave.larghezza_piano;
  
  // Calcola il fattore di scala per adattare l'autoclave al canvas
  const scaleX = (canvasWidth * 0.85) / (autoclaveWidthMM * MM_TO_PIXEL_SCALE);
  const scaleY = (canvasHeight * 0.85) / (autoclaveHeightMM * MM_TO_PIXEL_SCALE);
  const scale = Math.min(scaleX, scaleY);

  // Dimensioni dell'autoclave nel canvas
  const autoclaveWidth = autoclaveWidthMM * MM_TO_PIXEL_SCALE * scale;
  const autoclaveHeight = autoclaveHeightMM * MM_TO_PIXEL_SCALE * scale;
  
  // Margini per centrare l'autoclave
  const marginLeft = (canvasWidth - autoclaveWidth) / 2;
  const marginTop = (canvasHeight - autoclaveHeight) / 2;

  // 🔧 ALGORITMO MIGLIORATO PER IL POSIZIONAMENTO DEGLI ODL
  const calculateODLPositions = (): PositionedODL[] => {
    const positioned: PositionedODL[] = [];
    const rows: { height: number; width: number; items: PositionedODL[] }[] = [];
    
    const padding = 8; // Spaziatura tra i tool
    const contentPadding = 10; // Padding dal bordo dell'autoclave
    const availableWidth = autoclaveWidth - (contentPadding * 2);
    
    for (const odl of nesting.odl_list) {
      // Calcola dimensioni del tool nel canvas
      const toolWidthMM = odl.tool.lunghezza_piano;
      const toolHeightMM = odl.tool.larghezza_piano;
      const toolWidth = Math.max(toolWidthMM * MM_TO_PIXEL_SCALE * scale, 60); // Minimo 60px per leggibilità
      const toolHeight = Math.max(toolHeightMM * MM_TO_PIXEL_SCALE * scale, 40); // Minimo 40px per leggibilità
      
      let placed = false;
      
      // Prova a posizionare in una riga esistente
      for (const row of rows) {
        if (row.width + toolWidth + padding <= availableWidth) {
          const item: PositionedODL = {
            odl,
            x: contentPadding + row.width + (row.items.length > 0 ? padding : 0),
            y: contentPadding + rows.slice(0, rows.indexOf(row)).reduce((sum, r) => sum + r.height + padding, 0),
            width: toolWidth,
            height: toolHeight
          };
          
          positioned.push(item);
          row.items.push(item);
          row.width += toolWidth + (row.items.length > 1 ? padding : 0);
          row.height = Math.max(row.height, toolHeight);
          placed = true;
          break;
        }
      }
      
      // Se non si adatta in nessuna riga esistente, crea una nuova riga
      if (!placed) {
        const totalRowsHeight = rows.reduce((sum, r) => sum + r.height + padding, 0);
        
        // Controlla se la nuova riga entra nell'autoclave
        if (totalRowsHeight + toolHeight + contentPadding <= autoclaveHeight - contentPadding) {
          const item: PositionedODL = {
            odl,
            x: contentPadding,
            y: contentPadding + totalRowsHeight,
            width: toolWidth,
            height: toolHeight
          };
          
          positioned.push(item);
          rows.push({
            height: toolHeight,
            width: toolWidth,
            items: [item]
          });
        }
        // Se non entra, il tool viene saltato (overflow)
      }
    }
    
    return positioned;
  };

  const positionedODLs = calculateODLPositions();

  // Funzione per generare colori distintivi per ogni ODL
  const getODLColor = (index: number) => {
    const colors = [
      'bg-blue-100 border-blue-400',
      'bg-green-100 border-green-400', 
      'bg-yellow-100 border-yellow-400',
      'bg-purple-100 border-purple-400',
      'bg-pink-100 border-pink-400',
      'bg-indigo-100 border-indigo-400',
      'bg-red-100 border-red-400',
      'bg-orange-100 border-orange-400'
    ];
    return colors[index % colors.length];
  };

  // Funzione per scaricare l'anteprima come immagine (da implementare)
  const downloadPreview = () => {
    console.log('Download anteprima nesting - da implementare');
    // TODO: Implementare export come PNG/PDF
  };

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
                Esporta
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
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-medium">Anteprima Layout</h3>
                <p className="text-sm text-muted-foreground">
                  {positionedODLs.length} / {nesting.odl_list.length} ODL posizionati
                </p>
              </div>
              
              <div 
                className="border-2 border-dashed border-gray-300 rounded-lg p-4 bg-gray-50 relative overflow-hidden" 
                style={{ 
                  width: canvasWidth, 
                  height: canvasHeight,
                }}
              >
                {/* Contenitore dell'autoclave */}
                <div 
                  className="absolute bg-white border-2 border-slate-600 shadow-lg rounded-sm" 
                  style={{ 
                    width: autoclaveWidth, 
                    height: autoclaveHeight,
                    left: marginLeft,
                    top: marginTop
                  }}
                >
                  {/* Griglia di sfondo per aiutare la visualizzazione */}
                  <div 
                    className="absolute inset-0 opacity-10"
                    style={{
                      backgroundImage: `
                        linear-gradient(to right, #000 1px, transparent 1px),
                        linear-gradient(to bottom, #000 1px, transparent 1px)
                      `,
                      backgroundSize: '20px 20px'
                    }}
                  />
                  
                  {/* ODL posizionati con l'algoritmo migliorato */}
                  {positionedODLs.map((positioned, index) => (
                    <div
                      key={positioned.odl.id}
                      className={`absolute border-2 flex flex-col justify-center items-center text-xs font-medium transition-all hover:z-10 hover:shadow-lg ${getODLColor(index)}`}
                      style={{
                        width: positioned.width,
                        height: positioned.height,
                        left: positioned.x,
                        top: positioned.y,
                        borderRadius: '4px'
                      }}
                      title={`ODL #${positioned.odl.id} - ${positioned.odl.parte.part_number}`}
                    >
                      <span className="truncate px-1 font-semibold" style={{ maxWidth: positioned.width - 8 }}>
                        #{positioned.odl.id}
                      </span>
                      <span className="truncate px-1 text-[10px]" style={{ maxWidth: positioned.width - 8 }}>
                        {positioned.odl.parte.part_number}
                      </span>
                      <span className="text-[10px] opacity-75">
                        V: {positioned.odl.parte.num_valvole_richieste}
                      </span>
                    </div>
                  ))}
                  
                  {/* Indicatore per ODL non posizionati */}
                  {positionedODLs.length < nesting.odl_list.length && (
                    <div className="absolute bottom-2 right-2 bg-red-100 border border-red-300 text-red-700 px-2 py-1 rounded text-xs">
                      {nesting.odl_list.length - positionedODLs.length} ODL non visualizzati
                    </div>
                  )}
                </div>
                
                {/* Etichetta con informazioni */}
                <div className="absolute bottom-2 left-2 bg-white/90 border rounded px-2 py-1 text-xs text-slate-600">
                  <div>Autoclave: {nesting.autoclave.lunghezza} × {nesting.autoclave.larghezza_piano} mm</div>
                  <div>Scala: 1:{Math.round(1/scale)}x</div>
                </div>
                
                {/* Legenda colori */}
                <div className="absolute top-2 right-2 bg-white/95 border rounded p-2 text-xs">
                  <div className="font-medium mb-1">Legenda:</div>
                  <div className="flex items-center gap-1 mb-1">
                    <div className="w-3 h-3 bg-blue-100 border border-blue-400 rounded"></div>
                    <span>ODL standard</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-3 bg-red-100 border border-red-400 rounded"></div>
                    <span>Priorità alta</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
} 
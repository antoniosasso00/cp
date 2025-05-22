import { NestingResponse } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { formatDateIT } from '@/lib/utils'
import { X } from 'lucide-react'
import { Progress } from '@/components/ui/progress'

interface NestingDetailsProps {
  nesting: NestingResponse
  isOpen: boolean
  onClose: () => void
}

export function NestingDetails({ nesting, isOpen, onClose }: NestingDetailsProps) {
  if (!nesting) return null

  // Calcola le percentuali di utilizzo
  const areaPercentage = nesting.area_totale ? Math.round((nesting.area_utilizzata / nesting.area_totale) * 100) : 0
  const valvolePercentage = nesting.valvole_totali ? Math.round((nesting.valvole_utilizzate / nesting.valvole_totali) * 100) : 0

  // Calcola le dimensioni del canvas e il fattore di scala
  const canvasWidth = 700; // Larghezza fissa del canvas in pixel
  const canvasHeight = 400; // Altezza fissa del canvas in pixel
  
  // Calcola il fattore di scala per mantenere le proporzioni dell'autoclave
  const scaleX = canvasWidth / nesting.autoclave.lunghezza;
  const scaleY = canvasHeight / nesting.autoclave.larghezza_piano;
  const scale = Math.min(scaleX, scaleY) * 0.9; // Utilizziamo il 90% dello spazio disponibile

  // Dimensioni dell'autoclave nel canvas
  const autoclaveWidth = nesting.autoclave.lunghezza * scale;
  const autoclaveHeight = nesting.autoclave.larghezza_piano * scale;
  
  // Calcola il margine per centrare l'autoclave nel canvas
  const marginLeft = (canvasWidth - autoclaveWidth) / 2;
  const marginTop = (canvasHeight - autoclaveHeight) / 2;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[800px]">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle>Dettagli Nesting #{nesting.id}</DialogTitle>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
          <DialogDescription>
            Creato il {formatDateIT(new Date(nesting.created_at))}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div>
            <h3 className="text-lg font-medium">Informazioni Autoclave</h3>
            <p className="text-sm text-muted-foreground mt-1">
              {nesting.autoclave.nome} ({nesting.autoclave.codice}) - ID: {nesting.autoclave.id}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Utilizzo Area</h4>
              <Progress value={areaPercentage} className="h-2" />
              <p className="text-xs text-muted-foreground">
                {nesting.area_utilizzata.toFixed(2)} m² / {nesting.area_totale.toFixed(2)} m² ({areaPercentage}%)
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Utilizzo Valvole</h4>
              <Progress value={valvolePercentage} className="h-2" />
              <p className="text-xs text-muted-foreground">
                {nesting.valvole_utilizzate} / {nesting.valvole_totali} ({valvolePercentage}%)
              </p>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-medium">ODL Inclusi</h3>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID ODL</TableHead>
                  <TableHead>Part Number</TableHead>
                  <TableHead>Descrizione</TableHead>
                  <TableHead>Valvole</TableHead>
                  <TableHead>Priorità</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {nesting.odl_list.map((odl) => (
                  <TableRow key={odl.id}>
                    <TableCell>{odl.id}</TableCell>
                    <TableCell>{odl.parte.part_number}</TableCell>
                    <TableCell>{odl.parte.descrizione_breve}</TableCell>
                    <TableCell>{odl.parte.num_valvole_richieste}</TableCell>
                    <TableCell>{odl.priorita}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          
          {nesting.odl_list.length > 0 && (
            <div>
              <h3 className="text-lg font-medium mb-3">Anteprima Layout</h3>
              <div 
                className="border rounded-md p-4 bg-gray-50 relative" 
                style={{ 
                  width: canvasWidth, 
                  height: canvasHeight,
                }}
              >
                {/* Contenitore dell'autoclave */}
                <div 
                  className="absolute bg-white border-2 border-slate-400" 
                  style={{ 
                    width: autoclaveWidth, 
                    height: autoclaveHeight,
                    left: marginLeft,
                    top: marginTop
                  }}
                >
                  {/* Posiziona gli ODL in orizzontale */}
                  {nesting.odl_list.map((odl, index) => {
                    // Assumiamo che odl.tool abbia lunghezza_piano e larghezza_piano
                    // Per semplicità, posizionali in linea orizzontale
                    const toolWidth = odl.tool.lunghezza_piano * scale;
                    const toolHeight = odl.tool.larghezza_piano * scale;
                    
                    // Calcola la posizione x in base all'indice (layout orizzontale semplificato)
                    // Spazio tra gli ODL: 10px
                    let xOffset = 10;
                    let yOffset = 10;
                    
                    // Se ci sono ODL precedenti, somma le loro larghezze + 10px di gap
                    for (let i = 0; i < index; i++) {
                      xOffset += (nesting.odl_list[i].tool.lunghezza_piano * scale) + 10;
                    }
                    
                    // Se l'ODL esce dall'autoclave, vai alla riga successiva
                    if (xOffset + toolWidth > autoclaveWidth - 10) {
                      xOffset = 10;
                      yOffset += toolHeight + 10;
                    }
                    
                    return (
                      <div
                        key={odl.id}
                        className="absolute border border-slate-500 bg-blue-100 flex flex-col justify-center items-center text-xs p-1 overflow-hidden"
                        style={{
                          width: toolWidth,
                          height: toolHeight,
                          left: xOffset,
                          top: yOffset,
                        }}
                      >
                        <span className="font-medium truncate" style={{ maxWidth: toolWidth - 10 }}>
                          {odl.parte.part_number}
                        </span>
                        <span>Valvole: {odl.parte.num_valvole_richieste}</span>
                      </div>
                    );
                  })}
                </div>
                
                {/* Etichetta dimensioni autoclave */}
                <div className="absolute bottom-0 right-0 text-xs text-slate-500 p-1">
                  Autoclave: {nesting.autoclave.lunghezza}x{nesting.autoclave.larghezza_piano} mm
                </div>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
} 
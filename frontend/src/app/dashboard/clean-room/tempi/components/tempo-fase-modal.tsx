import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/components/ui/use-toast";
import { phaseTimesApi, TempoFaseResponse, ODLResponse } from "@/lib/api";

interface TempoFaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  item: TempoFaseResponse | null;
  odlList: ODLResponse[];
  onSuccess: () => void;
}

export default function TempoFaseModal({
  isOpen,
  onClose,
  item,
  odlList,
  onSuccess,
}: TempoFaseModalProps) {
  const { toast } = useToast();
  const isEditing = !!item;

  // Form state
  const [odlId, setOdlId] = useState<number | string>("");
  const [fase, setFase] = useState<"laminazione" | "attesa_cura" | "cura">("laminazione");
  const [inizioFase, setInizioFase] = useState<string>("");
  const [fineFase, setFineFase] = useState<string>("");
  const [note, setNote] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      if (item) {
        // Editing mode
        setOdlId(item.odl_id);
        setFase(item.fase);
        
        // Format date strings for input fields
        if (item.inizio_fase) {
          const date = new Date(item.inizio_fase);
          setInizioFase(formatDateTimeForInput(date));
        }
        
        if (item.fine_fase) {
          const date = new Date(item.fine_fase);
          setFineFase(formatDateTimeForInput(date));
        } else {
          setFineFase("");
        }
        
        setNote(item.note || "");
      } else {
        // Creation mode - set defaults
        setOdlId("");
        setFase("laminazione");
        setInizioFase(formatDateTimeForInput(new Date()));
        setFineFase("");
        setNote("");
      }
    }
  }, [isOpen, item]);

  // Format date for datetime-local input
  function formatDateTimeForInput(date: Date): string {
    return date.toISOString().slice(0, 16);
  }

  const handleSubmit = async () => {
    if (!odlId) {
      toast({
        variant: "destructive",
        title: "Errore",
        description: "Seleziona un ODL",
      });
      return;
    }

    try {
      setIsLoading(true);
      
      if (isEditing && item) {
        // Per gli aggiornamenti, invio solo i campi modificati senza il tipo fase
        const updateData = {
          inizio_fase: inizioFase ? new Date(inizioFase).toISOString() : undefined,
          fine_fase: fineFase ? new Date(fineFase).toISOString() : null,
          note: note || null,
        };
        
        await phaseTimesApi.updatePhaseTime(item.id, updateData);
        toast({
          title: "Modificato",
          description: "Tempo fase aggiornato con successo",
        });
      } else {
        // Per le creazioni, includo il tipo di fase
        const createData = {
          odl_id: Number(odlId),
          fase,
          inizio_fase: inizioFase ? new Date(inizioFase).toISOString() : new Date().toISOString(),
          fine_fase: fineFase ? new Date(fineFase).toISOString() : null,
          note: note || null,
        };
        
        await phaseTimesApi.createPhaseTime(createData);
        toast({
          title: "Creato",
          description: "Nuovo tempo fase registrato con successo",
        });
      }

      onSuccess();
    } catch (error: any) {
      console.error("Errore durante il salvataggio:", error);
      toast({
        variant: "destructive",
        title: "Errore",
        description: error.message || "Si è verificato un errore durante il salvataggio",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Helper per recuperare informazioni aggiuntive sull'ODL
  const getOdlInfo = (id: number) => {
    const odl = odlList.find(o => o.id === id);
    if (!odl) return null;
    
    return {
      part_number: odl.parte.part_number,
      descrizione: odl.parte.descrizione_breve,
      status: odl.status
    };
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{isEditing ? "Modifica Tempo Fase" : "Registra Nuovo Tempo Fase"}</DialogTitle>
          <DialogDescription>
            {isEditing
              ? "Modifica i dettagli del monitoraggio tempo"
              : "Inserisci i dettagli per registrare un nuovo monitoraggio tempo"}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="odl">ODL</Label>
            <Select
              value={odlId ? odlId.toString() : ""}
              onValueChange={(value) => {
                if (!value || value.trim() === "") {
                  setOdlId("");
                  return;
                }
                const numValue = Number(value);
                if (!isNaN(numValue)) {
                  setOdlId(numValue);
                }
              }}
              disabled={isEditing}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleziona un ODL" />
              </SelectTrigger>
              <SelectContent>
                {odlList.length === 0 ? (
                  <div className="p-2 text-sm text-muted-foreground">
                    Nessun ODL disponibile
                  </div>
                ) : (
                  odlList
                    .filter((odl) => odl?.id && odl?.parte?.part_number)
                    .map((odl) => {
                      const info = `${odl.id} - ${odl.parte.part_number} (${odl.status})`;
                      return (
                        <SelectItem key={odl.id} value={odl.id.toString()}>
                          {info}
                        </SelectItem>
                      );
                    })
                )}
              </SelectContent>
            </Select>
            {odlId && (
              <div className="text-xs text-muted-foreground">
                {(() => {
                  const info = getOdlInfo(Number(odlId));
                  if (!info) return null;
                  return `${info.part_number} - ${info.descrizione}`;
                })()}
              </div>
            )}
          </div>

          <div className="grid gap-2">
            <Label htmlFor="fase">Fase</Label>
            <Select 
              value={fase} 
              onValueChange={(value: "laminazione" | "attesa_cura" | "cura") => setFase(value)} 
              disabled={isEditing}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleziona una fase" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="laminazione">Laminazione</SelectItem>
                <SelectItem value="attesa_cura">Attesa Cura</SelectItem>
                <SelectItem value="cura">Cura</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="inizio_fase">Inizio Fase</Label>
            <Input
              id="inizio_fase"
              type="datetime-local"
              value={inizioFase}
              onChange={(e) => setInizioFase(e.target.value)}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="fine_fase">Fine Fase (opzionale)</Label>
            <Input
              id="fine_fase"
              type="datetime-local"
              value={fineFase}
              onChange={(e) => setFineFase(e.target.value)}
              placeholder="Lascia vuoto se la fase è ancora in corso"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="note">Note (opzionale)</Label>
            <Textarea
              id="note"
              placeholder="Note aggiuntive sul monitoraggio..."
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Annulla
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading}>
            {isLoading ? "Salvataggio..." : isEditing ? "Aggiorna" : "Registra"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
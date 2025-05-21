import React, { useEffect, useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useRouter } from 'next/router';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

interface Parte {
  id: number;
  part_number: string;
  descrizione_breve: string;
  status: string;
  tools: Array<{
    id: number;
    codice: string;
    descrizione: string;
  }>;
}

interface ODL {
  id: number;
  code: string;
  description: string;
  status: ODLStatus;
  current_phase: ODLPhase;
  created_at: string;
  updated_at: string;
  parti: Parte[];
}

type ODLStatus = 'created' | 'in_progress' | 'completed' | 'cancelled';
type ODLPhase = 'laminazione' | 'pre_nesting' | 'nesting' | 'autoclave' | 'post';

const phaseColors: Record<ODLPhase, string> = {
  laminazione: 'bg-blue-100 text-blue-800',
  pre_nesting: 'bg-yellow-100 text-yellow-800',
  nesting: 'bg-purple-100 text-purple-800',
  autoclave: 'bg-green-100 text-green-800',
  post: 'bg-gray-100 text-gray-800',
};

const statusColors: Record<ODLStatus, string> = {
  created: 'bg-gray-100 text-gray-800',
  in_progress: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
};

export function ODLList() {
  const [odls, setODLs] = useState<ODL[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    fetchODLs();
  }, []);

  const fetchODLs = async () => {
    try {
      const response = await fetch('/api/odl');
      const data = await response.json();
      setODLs(data);
    } catch (error) {
      console.error('Errore nel caricamento degli ODL:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAdvancePhase = async (odlId: number) => {
    try {
      const response = await fetch(`/api/odl/${odlId}/advance`, {
        method: 'POST',
      });
      if (response.ok) {
        fetchODLs(); // Ricarica la lista
      } else {
        const error = await response.json();
        alert(error.detail || 'Errore nell\'avanzamento della fase');
      }
    } catch (error) {
      console.error('Errore nell\'avanzamento della fase:', error);
      alert('Errore nell\'avanzamento della fase');
    }
  };

  if (loading) {
    return <div>Caricamento...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Ordini di Lavorazione</h2>
        <Button onClick={() => router.push('/odl/new')}>
          Nuovo ODL
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Codice</TableHead>
            <TableHead>Descrizione</TableHead>
            <TableHead>Stato</TableHead>
            <TableHead>Fase</TableHead>
            <TableHead>Parti</TableHead>
            <TableHead>Ultimo Aggiornamento</TableHead>
            <TableHead>Azioni</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {odls.map((odl) => (
            <TableRow key={odl.id}>
              <TableCell>{odl.code}</TableCell>
              <TableCell>{odl.description}</TableCell>
              <TableCell>
                <Badge className={statusColors[odl.status as ODLStatus]}>
                  {odl.status}
                </Badge>
              </TableCell>
              <TableCell>
                <Badge className={phaseColors[odl.current_phase as ODLPhase]}>
                  {odl.current_phase}
                </Badge>
              </TableCell>
              <TableCell>
                <div className="space-y-1">
                  {odl.parti.map((parte) => (
                    <div key={parte.id} className="flex items-center space-x-2">
                      <span>{parte.part_number}</span>
                      <Badge variant="outline">{parte.status}</Badge>
                      <span className="text-sm text-gray-500">
                        ({parte.tools.map(t => t.codice).join(', ')})
                      </span>
                    </div>
                  ))}
                </div>
              </TableCell>
              <TableCell>
                {format(new Date(odl.updated_at), 'dd/MM/yyyy HH:mm', { locale: it })}
              </TableCell>
              <TableCell>
                <div className="space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => router.push(`/odl/${odl.id}`)}
                  >
                    Dettagli
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAdvancePhase(odl.id)}
                  >
                    Avanza Fase
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
} 
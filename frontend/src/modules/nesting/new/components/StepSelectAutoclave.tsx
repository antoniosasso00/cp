'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card';
import { Checkbox } from '@/shared/components/ui/checkbox';
import { Badge } from '@/shared/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/components/ui/table';
import { Factory, CheckCircle2, Thermometer, Gauge } from 'lucide-react';

interface AutoclaveData {
  id: number;
  nome: string;
  codice: string;
  lunghezza: number;
  larghezza_piano: number;
  stato: string;
  num_linee_vuoto: number;
  temperatura_max: number;
  pressione_max: number;
  max_load_kg?: number;
}

interface StepSelectAutoclaveProps {
  autoclaveList: AutoclaveData[];
  selectedAutoclavi: string[];
  onSelectionChange: (autoclaveId: string, checked: boolean) => void;
  isCompleted: boolean;
}

export const StepSelectAutoclave: React.FC<StepSelectAutoclaveProps> = ({ 
  autoclaveList, 
  selectedAutoclavi, 
  onSelectionChange,
  isCompleted
}) => {
  const getStatoBadge = (stato: string) => {
    switch (stato?.toLowerCase()) {
      case 'disponibile':
        return <Badge variant="outline" className="bg-green-50 text-green-700">Disponibile</Badge>;
      case 'in_uso':
        return <Badge variant="outline" className="bg-red-50 text-red-700">In Uso</Badge>;
      case 'manutenzione':
        return <Badge variant="outline" className="bg-yellow-50 text-yellow-700">Manutenzione</Badge>;
      default:
        return <Badge variant="outline">{stato}</Badge>;
    }
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Factory className="h-5 w-5" />
            Seleziona Autoclavi
            {isCompleted && (
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            )}
          </div>
          <Badge variant="outline" className="bg-green-50 text-green-700">
            {selectedAutoclavi.length} selezionate
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {autoclaveList.length === 0 ? (
          <div className="text-center py-8">
            <Factory className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              Nessuna autoclave disponibile
            </p>
          </div>
        ) : (
          <div className="max-h-80 overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12"></TableHead>
                  <TableHead>Autoclave</TableHead>
                  <TableHead className="text-center">Dimensioni</TableHead>
                  <TableHead className="text-center">Spec</TableHead>
                  <TableHead className="text-center">Stato</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {autoclaveList.map((autoclave) => {
                  const isDisponibile = autoclave.stato?.toLowerCase() === 'disponibile';
                  return (
                    <TableRow 
                      key={autoclave.id} 
                      className={`hover:bg-muted/50 cursor-pointer ${
                        selectedAutoclavi.includes(autoclave.id.toString()) ? 'bg-green-50' : ''
                      } ${!isDisponibile ? 'opacity-50' : ''}`}
                      onClick={() => isDisponibile && onSelectionChange(
                        autoclave.id.toString(), 
                        !selectedAutoclavi.includes(autoclave.id.toString())
                      )}
                    >
                      <TableCell>
                        <Checkbox
                          checked={selectedAutoclavi.includes(autoclave.id.toString())}
                          disabled={!isDisponibile}
                          onCheckedChange={(checked) => 
                            onSelectionChange(autoclave.id.toString(), checked as boolean)
                          }
                          onClick={(e) => e.stopPropagation()}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="font-medium text-sm">
                            {autoclave.nome}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {autoclave.codice}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="text-xs">
                          <div>{autoclave.lunghezza}×{autoclave.larghezza_piano} mm</div>
                          <div className="text-muted-foreground">
                            {autoclave.max_load_kg ? `${autoclave.max_load_kg}kg max` : 'N/A'}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="space-y-1">
                          <div className="flex items-center justify-center gap-1 text-xs">
                            <Thermometer className="h-3 w-3" />
                            {autoclave.temperatura_max}°C
                          </div>
                          <div className="flex items-center justify-center gap-1 text-xs">
                            <Gauge className="h-3 w-3" />
                            {autoclave.pressione_max} bar
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {autoclave.num_linee_vuoto} linee vuoto
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        {getStatoBadge(autoclave.stato)}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}; 
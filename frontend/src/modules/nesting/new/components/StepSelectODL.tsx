'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card';
import { Checkbox } from '@/shared/components/ui/checkbox';
import { Badge } from '@/shared/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/components/ui/table';
import { Package, CheckCircle2 } from 'lucide-react';

interface ODLData {
  id: number;
  parte: {
    id: number;
    part_number: string;
    descrizione_breve: string;
    num_valvole_richieste: number;
  };
  tool: {
    id: number;
    part_number_tool: string;
    descrizione?: string;
  };
  status: string;
  priorita: number;
  created_at: string;
}

interface StepSelectODLProps {
  odlList: ODLData[];
  selectedOdl: string[];
  onSelectionChange: (odlId: string, checked: boolean) => void;
  isCompleted: boolean;
}

export const StepSelectODL: React.FC<StepSelectODLProps> = ({ 
  odlList, 
  selectedOdl, 
  onSelectionChange,
  isCompleted
}) => {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Seleziona ODL
            {isCompleted && (
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            )}
          </div>
          <Badge variant="outline" className="bg-blue-50 text-blue-700">
            {selectedOdl.length} selezionati
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {odlList.length === 0 ? (
          <div className="text-center py-8">
            <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              Nessun ODL disponibile per il nesting
            </p>
          </div>
        ) : (
          <div className="max-h-80 overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12"></TableHead>
                  <TableHead className="w-20">ODL</TableHead>
                  <TableHead>Parte & Tool</TableHead>
                  <TableHead className="text-center w-20">Priorità</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {odlList.map((odl) => (
                  <TableRow 
                    key={odl.id} 
                    className={`hover:bg-muted/50 cursor-pointer ${
                      selectedOdl.includes(odl.id.toString()) ? 'bg-blue-50' : ''
                    }`}
                    onClick={() => onSelectionChange(
                      odl.id.toString(), 
                      !selectedOdl.includes(odl.id.toString())
                    )}
                  >
                    <TableCell>
                      <Checkbox
                        checked={selectedOdl.includes(odl.id.toString())}
                        onCheckedChange={(checked) => 
                          onSelectionChange(odl.id.toString(), checked as boolean)
                        }
                        onClick={(e) => e.stopPropagation()}
                      />
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      #{odl.id}
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium text-sm">
                          {odl.parte.part_number}
                        </div>
                        <div className="text-xs text-muted-foreground line-clamp-1">
                          {odl.parte.descrizione_breve}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          <span className="bg-slate-100 px-2 py-0.5 rounded">
                            Tool: {odl.tool.part_number_tool}
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant="outline" className="text-xs">
                        P{odl.priorita}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}; 
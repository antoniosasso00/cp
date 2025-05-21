'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { nestingApi } from '@/lib/api/nestingApi';
import { AutoclaveLayout, NestingResultSummary, ODLLayout } from '@/lib/types/nesting';
import NestingVisualizer from '@/components/nesting/NestingVisualizer';
import { Loader2, ArrowLeft, Check, BarChart2, Calendar, Clock, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { Skeleton } from '@/components/ui/skeleton';

interface NestingDetail {
  id: number;
  codice: string;
  autoclave_id: number;
  autoclave_nome: string;
  confermato: boolean;
  data_conferma: string | null;
  efficienza_area: number;
  area_totale_mm2: number;
  area_utilizzata_mm2: number;
  valvole_utilizzate: number;
  valvole_totali: number;
  generato_manualmente: boolean;
  created_at: string;
  layout: AutoclaveLayout;
  odl_info: any[];
}

export default function NestingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<NestingDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [selectedOdlId, setSelectedOdlId] = useState<number>(-1);
  const [retryCount, setRetryCount] = useState(0);

  // Carica i dettagli del nesting con retry
  useEffect(() => {
    const fetchDetails = async () => {
      if (!params.id) return;
      
      try {
        setLoading(true);
        setError(null);
        const data = await nestingApi.getResultDetails(Number(params.id));
        setDetail(data);
        setRetryCount(0); // Reset retry count on success
      } catch (err: any) {
        console.error('Errore nel caricamento dei dettagli:', err);
        setError(err.message || 'Errore nel caricamento dei dettagli del nesting');
        
        // Implementa retry automatico fino a 3 tentativi
        if (retryCount < 3) {
          setRetryCount(prev => prev + 1);
          setTimeout(() => fetchDetails(), 2000); // Riprova dopo 2 secondi
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchDetails();
  }, [params.id, retryCount]);

  // Formatta la data in formato italiano
  const formatDate = (date: string | null) => {
    if (!date) return 'Non confermato';
    try {
      return format(new Date(date), 'dd MMM yyyy, HH:mm', { locale: it });
    } catch (e) {
      return 'Data non valida';
    }
  };

  // Conferma il nesting
  const handleConfirm = async () => {
    if (!detail) return;
    
    try {
      setConfirming(true);
      await nestingApi.confirmNesting(detail.id);
      
      toast({
        title: "Nesting confermato",
        description: "Il nesting è stato confermato e gli ODL aggiornati con successo.",
        variant: "success"
      });
      
      // Aggiorna i dettagli
      const updatedData = await nestingApi.getResultDetails(detail.id);
      setDetail(updatedData);
    } catch (err: any) {
      toast({
        title: "Errore",
        description: err.message || "Si è verificato un errore durante la conferma del nesting",
        variant: "destructive"
      });
    } finally {
      setConfirming(false);
    }
  };

  // Componente di caricamento
  if (loading) {
    return (
      <div className="container mx-auto py-8">
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <Skeleton className="h-8 w-32" />
            <Skeleton className="h-8 w-64" />
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <Skeleton className="h-6 w-48" />
                  <Skeleton className="h-4 w-32" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-[400px] w-full" />
                </CardContent>
              </Card>
            </div>
            
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <Skeleton className="h-6 w-32" />
                </CardHeader>
                <CardContent className="space-y-4">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <Skeleton className="h-6 w-32" />
                </CardHeader>
                <CardContent className="space-y-4">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Componente di errore
  if (error || !detail) {
    return (
      <div className="container mx-auto py-8">
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Errore</AlertTitle>
          <AlertDescription>
            {error || 'Dettagli non trovati'}
            {retryCount > 0 && (
              <div className="mt-2 text-sm">
                Tentativo {retryCount} di 3...
              </div>
            )}
          </AlertDescription>
        </Alert>
        
        <div className="flex gap-4">
          <Button 
            onClick={() => router.back()}
            variant="outline"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Torna indietro
          </Button>
          
          <Button 
            onClick={() => {
              setRetryCount(0);
              setLoading(true);
            }}
            variant="secondary"
          >
            <Loader2 className="h-4 w-4 mr-2" />
            Riprova
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <div className="mb-6">
        <div className="flex items-center mb-2">
          <Button 
            variant="outline"
            size="sm"
            onClick={() => router.push('/dashboard/nesting')}
            className="mr-3"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Indietro
          </Button>
          <h1 className="text-2xl font-bold">Dettaglio Nesting: {detail.codice}</h1>
        </div>
        <div className="flex space-x-2 mt-2">
          <Badge variant={detail.confermato ? "success" : "outline"}>
            {detail.confermato ? 'Confermato' : 'Non confermato'}
          </Badge>
          <Badge variant="secondary">
            {detail.generato_manualmente ? 'Manuale' : 'Automatico'}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Colonna principale: Visualizzazione e Tabella ODL */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle>Visualizzazione Layout</CardTitle>
              <CardDescription>
                Autoclave: {detail.autoclave_nome}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <NestingVisualizer 
                layout={detail.layout}
                onSelect={setSelectedOdlId}
                selectedOdlId={selectedOdlId}
              />
            </CardContent>
            {!detail.confermato && (
              <CardFooter className="border-t bg-gray-50">
                <Button 
                  onClick={handleConfirm}
                  disabled={confirming}
                  className="ml-auto bg-green-600 hover:bg-green-700"
                >
                  {confirming ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Confermando...
                    </>
                  ) : (
                    <>
                      <Check className="h-4 w-4 mr-2" />
                      Conferma Nesting
                    </>
                  )}
                </Button>
              </CardFooter>
            )}
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Parti incluse</CardTitle>
              <CardDescription>
                ODL inclusi in questo nesting
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID ODL</TableHead>
                      <TableHead>Parte</TableHead>
                      <TableHead>Tool</TableHead>
                      <TableHead>Posizione</TableHead>
                      <TableHead>Dimensioni</TableHead>
                      <TableHead>Valvole</TableHead>
                      <TableHead>Priorità</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {detail.layout.odl_layout.map((odl: ODLLayout) => (
                      <TableRow 
                        key={odl.odl_id} 
                        className={`cursor-pointer transition-colors ${
                          selectedOdlId === odl.odl_id ? "bg-blue-50" : "hover:bg-gray-50"
                        }`}
                        onClick={() => setSelectedOdlId(odl.odl_id)}
                      >
                        <TableCell className="font-medium">{odl.odl_id}</TableCell>
                        <TableCell>{odl.parte_nome}</TableCell>
                        <TableCell>{odl.tool_codice}</TableCell>
                        <TableCell>
                          ({odl.x.toFixed(0)}, {odl.y.toFixed(0)})
                        </TableCell>
                        <TableCell>
                          {odl.lunghezza.toFixed(0)} × {odl.larghezza.toFixed(0)} mm
                        </TableCell>
                        <TableCell>{odl.valvole_utilizzate}</TableCell>
                        <TableCell>
                          <Badge variant={odl.priorita > 5 ? "destructive" : "outline"}>
                            {odl.priorita}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Colonna laterale: Informazioni e Metriche */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Informazioni</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="text-sm text-gray-500 mb-1">Stato</div>
                <div className="flex items-center">
                  {detail.confermato ? (
                    <Badge className="bg-green-600">Confermato</Badge>
                  ) : (
                    <Badge variant="outline">Non confermato</Badge>
                  )}
                </div>
              </div>

              <div>
                <div className="text-sm text-gray-500 mb-1">Tipo</div>
                <div>
                  {detail.generato_manualmente ? "Nesting Manuale" : "Nesting Automatico"}
                </div>
              </div>

              <div>
                <div className="text-sm text-gray-500 mb-1">Data creazione</div>
                <div className="flex items-center">
                  <Calendar className="h-4 w-4 mr-2 text-gray-500" />
                  {formatDate(detail.created_at)}
                </div>
              </div>

              {detail.confermato && (
                <div>
                  <div className="text-sm text-gray-500 mb-1">Data conferma</div>
                  <div className="flex items-center">
                    <Check className="h-4 w-4 mr-2 text-green-500" />
                    {formatDate(detail.data_conferma)}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Metriche</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="text-sm text-gray-500 mb-1">Efficienza area</div>
                <div className="text-2xl font-bold">
                  {(detail.efficienza_area * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-gray-500">
                  {detail.area_utilizzata_mm2.toLocaleString('it-IT')} mm² / {detail.area_totale_mm2.toLocaleString('it-IT')} mm²
                </div>
              </div>

              <div>
                <div className="text-sm text-gray-500 mb-1">Valvole</div>
                <div className="text-2xl font-bold">
                  {detail.valvole_utilizzate} / {detail.valvole_totali}
                </div>
                <div className="text-xs text-gray-500">
                  {((detail.valvole_utilizzate / detail.valvole_totali) * 100).toFixed(1)}% utilizzate
                </div>
              </div>

              <div>
                <div className="text-sm text-gray-500 mb-1">Parti</div>
                <div className="text-2xl font-bold">
                  {detail.layout.odl_layout.length}
                </div>
              </div>
            </CardContent>
          </Card>

          {!detail.confermato && (
            <Button 
              onClick={handleConfirm}
              disabled={confirming}
              className="w-full bg-green-600 hover:bg-green-700"
              size="lg"
            >
              {confirming ? (
                <>
                  <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                  Confermando...
                </>
              ) : (
                <>
                  <Check className="h-5 w-5 mr-2" />
                  Conferma Nesting
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
} 
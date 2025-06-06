'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/shared/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card';
import { Badge } from '@/shared/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/components/ui/tabs';
import { LayoutGrid, Package, Plus, Search, Activity, Eye, Trash2 } from 'lucide-react';

export default function CuringNestingPage() {
  const router = useRouter();
  const [batches, setBatches] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchBatches();
  }, []);

  const fetchBatches = async () => {
    try {
      const response = await fetch('/api/batch_nesting/', {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setBatches(data);
      }
    } catch (error) {
      console.error('Errore nel caricamento dei batch:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatoBadge = (stato: string) => {
    const variants: Record<string, { variant: any; label: string }> = {
      'draft': { variant: 'secondary', label: 'Bozza' },
      'sospeso': { variant: 'warning', label: 'Sospeso' },
      'confermato': { variant: 'success', label: 'Confermato' },
      'loaded': { variant: 'info', label: 'Caricato' },
      'cured': { variant: 'primary', label: 'Curato' },
      'terminato': { variant: 'default', label: 'Terminato' }
    };

    const config = variants[stato] || { variant: 'secondary', label: stato };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const handleViewResult = (batchId: string) => {
    router.push(`/dashboard/curing/nesting/result/${batchId}`);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Nesting & Batch</h1>
          <p className="text-muted-foreground">
            Gestisci i batch di nesting per la cura delle parti
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/nesting">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Nuovo Nesting
            </Button>
          </Link>
        </div>
      </div>

      {/* Tabs per organizzare i batch */}
      <Tabs defaultValue="active" className="w-full">
        <TabsList>
          <TabsTrigger value="active">Batch Attivi</TabsTrigger>
          <TabsTrigger value="completed">Completati</TabsTrigger>
          <TabsTrigger value="all">Tutti</TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4">
          <div className="grid gap-4">
            {isLoading ? (
              <div className="text-center py-8">Caricamento batch...</div>
            ) : (
              batches
                .filter(batch => !['terminato'].includes(batch.stato))
                .map((batch) => (
                  <Card key={batch.id} className="hover:shadow-md transition-shadow">
                    <CardHeader className="pb-4">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">
                          {batch.nome || `Batch ${batch.id.slice(0, 8)}`}
                        </CardTitle>
                        {getStatoBadge(batch.stato)}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                        <div>
                          <p className="text-sm text-muted-foreground">Autoclave</p>
                          <p className="font-medium">{batch.autoclave_id}</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Nesting</p>
                          <p className="font-medium">{batch.numero_nesting}</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Peso Totale</p>
                          <p className="font-medium">{batch.peso_totale_kg} kg</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Creato</p>
                          <p className="font-medium">
                            {new Date(batch.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleViewResult(batch.id)}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          Visualizza
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))
            )}
          </div>
        </TabsContent>

        <TabsContent value="completed" className="space-y-4">
          <div className="grid gap-4">
            {batches
              .filter(batch => batch.stato === 'terminato')
              .map((batch) => (
                <Card key={batch.id} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">
                        {batch.nome || `Batch ${batch.id.slice(0, 8)}`}
                      </CardTitle>
                      {getStatoBadge(batch.stato)}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Completato</p>
                        <p className="font-medium">
                          {batch.data_completamento 
                            ? new Date(batch.data_completamento).toLocaleDateString()
                            : 'N/A'
                          }
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Durata</p>
                        <p className="font-medium">
                          {batch.durata_ciclo_minuti ? `${batch.durata_ciclo_minuti} min` : 'N/A'}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Peso</p>
                        <p className="font-medium">{batch.peso_totale_kg} kg</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Efficienza</p>
                        <p className="font-medium">{batch.efficiency?.toFixed(1)}%</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleViewResult(batch.id)}
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        Visualizza Report
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
          </div>
        </TabsContent>

        <TabsContent value="all" className="space-y-4">
          <div className="grid gap-4">
            {batches.map((batch) => (
              <Card key={batch.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-4">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">
                      {batch.nome || `Batch ${batch.id.slice(0, 8)}`}
                    </CardTitle>
                    {getStatoBadge(batch.stato)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Autoclave</p>
                      <p className="font-medium">{batch.autoclave_id}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Nesting</p>
                      <p className="font-medium">{batch.numero_nesting}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Peso</p>
                      <p className="font-medium">{batch.peso_totale_kg} kg</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Stato</p>
                      <p className="font-medium">{batch.stato}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-end gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewResult(batch.id)}
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      Visualizza
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
} 
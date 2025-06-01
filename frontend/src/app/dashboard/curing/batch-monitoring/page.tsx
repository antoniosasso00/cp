'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Package, Activity, PlayCircle, CheckCircle } from 'lucide-react';
import BatchListWithControls from '@/components/batch-nesting/BatchListWithControls';

export default function BatchMonitoringPage() {
  return (
    <div className="container mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">🎯 Monitoraggio Batch</h1>
          <p className="text-muted-foreground mt-1">
            Gestisci e controlla tutti i batch di nesting esistenti
          </p>
        </div>
      </div>

      {/* Statistiche Rapide */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Batch In Sospeso</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">-</div>
            <p className="text-xs text-muted-foreground">In attesa di conferma</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Batch In Cura</CardTitle>
            <PlayCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">-</div>
            <p className="text-xs text-muted-foreground">Ciclo di cura attivo</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Batch Completati</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">-</div>
            <p className="text-xs text-muted-foreground">Ultimi 30 giorni</p>
          </CardContent>
        </Card>
      </div>

      {/* Lista Batch Tutti */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Tutti i Batch
          </CardTitle>
          <CardDescription>
            Vista completa di tutti i batch con controlli di stato avanzati
          </CardDescription>
        </CardHeader>
        <CardContent>
          <BatchListWithControls
            title="Gestione Completa Batch"
            editableOnly={false}
            onBatchUpdated={(batchId, newData) => {
              console.log(`✅ Batch ${batchId} aggiornato:`, newData);
            }}
            userInfo={{ userId: 'utente_frontend', userRole: 'Curing' }}
          />
        </CardContent>
      </Card>

      {/* Lista Batch Solo Editabili */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PlayCircle className="h-5 w-5" />
            Batch Attivi
          </CardTitle>
          <CardDescription>
            Solo batch che richiedono azione (sospesi o confermati)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <BatchListWithControls
            title="Batch da Gestire"
            editableOnly={true}
            initialStatusFilter=""
            onBatchUpdated={(batchId, newData) => {
              console.log(`🔄 Batch attivo ${batchId} aggiornato:`, newData);
            }}
            userInfo={{ userId: 'utente_frontend', userRole: 'Curing' }}
          />
        </CardContent>
      </Card>
    </div>
  );
} 
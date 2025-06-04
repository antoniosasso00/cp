'use client';

import React from 'react';
import { OdlProgressBar, createTestODLData, ODLProgressData } from './OdlProgressBar';
import { Card, CardContent, CardHeader, CardTitle } from './card';

export function OdlProgressBarTest() {
  // Scenario 1: ODL senza timestamps (caso più comune del problema)
  const odlSenzaTimestamps = createTestODLData({
    id: 1,
    status: 'Laminazione',
    timestamps: []
  });

  // Scenario 2: ODL con timestamps completi
  const odlConTimestamps = createTestODLData({
    id: 2,
    status: 'Cura',
    timestamps: [
      {
        stato: 'Preparazione',
        inizio: '2025-01-28T08:00:00Z',
        fine: '2025-01-28T09:00:00Z',
        durata_minuti: 60
      },
      {
        stato: 'Laminazione',
        inizio: '2025-01-28T09:00:00Z',
        fine: '2025-01-28T11:00:00Z',
        durata_minuti: 120
      },
      {
        stato: 'Attesa Cura',
        inizio: '2025-01-28T11:00:00Z',
        fine: '2025-01-28T12:00:00Z',
        durata_minuti: 60
      },
      {
        stato: 'Cura',
        inizio: '2025-01-28T12:00:00Z',
        fine: undefined,
        durata_minuti: 180
      }
    ]
  });

  // Scenario 3: ODL finito
  const odlFinito = createTestODLData({
    id: 3,
    status: 'Finito',
    timestamps: [
      {
        stato: 'Preparazione',
        inizio: '2025-01-28T08:00:00Z',
        fine: '2025-01-28T09:00:00Z',
        durata_minuti: 60
      },
      {
        stato: 'Laminazione',
        inizio: '2025-01-28T09:00:00Z',
        fine: '2025-01-28T11:00:00Z',
        durata_minuti: 120
      },
      {
        stato: 'Attesa Cura',
        inizio: '2025-01-28T11:00:00Z',
        fine: '2025-01-28T12:00:00Z',
        durata_minuti: 60
      },
      {
        stato: 'Cura',
        inizio: '2025-01-28T12:00:00Z',
        fine: '2025-01-28T17:00:00Z',
        durata_minuti: 300
      },
      {
        stato: 'Finito',
        inizio: '2025-01-28T17:00:00Z',
        fine: '2025-01-28T17:00:00Z',
        durata_minuti: 0
      }
    ]
  });

  // Scenario 4: ODL con stato non standard
  const odlStatoCustom = createTestODLData({
    id: 4,
    status: 'Stato Personalizzato',
    timestamps: []
  });

  // Scenario 5: ODL in ritardo
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 2);
  const odlInRitardo = createTestODLData({
    id: 5,
    status: 'Preparazione',
    created_at: yesterday.toISOString(),
    updated_at: yesterday.toISOString(),
    timestamps: []
  });

  const scenarios = [
    {
      title: 'ODL senza Timeline (Caso Comune)',
      description: 'ODL appena creato o senza state logs - mostra dati stimati',
      odl: odlSenzaTimestamps
    },
    {
      title: 'ODL con Timeline Completa',
      description: 'ODL con tutti i timestamps disponibili',
      odl: odlConTimestamps
    },
    {
      title: 'ODL Completato',
      description: 'ODL finito con timeline completa',
      odl: odlFinito
    },
    {
      title: 'ODL con Stato Personalizzato',
      description: 'ODL con stato non presente nella configurazione standard',
      odl: odlStatoCustom
    },
    {
      title: 'ODL in Ritardo',
      description: 'ODL che è rimasto nello stesso stato per più di 24h',
      odl: odlInRitardo
    }
  ];

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold mb-2">Test Barra di Progresso ODL</h1>
        <p className="text-muted-foreground">
          Verifica del funzionamento della barra di progresso in diversi scenari
        </p>
      </div>

      {scenarios.map((scenario, index) => (
        <Card key={index}>
          <CardHeader>
            <CardTitle className="text-lg">{scenario.title}</CardTitle>
            <p className="text-sm text-muted-foreground">{scenario.description}</p>
          </CardHeader>
          <CardContent>
            <OdlProgressBar 
              odl={scenario.odl}
              showDetails={true}
              onTimelineClick={() => console.log(`Timeline clicked for ODL ${scenario.odl.id}`)}
            />
            
            {/* Debug info */}
            <details className="mt-4">
              <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                Mostra dati raw (debug)
              </summary>
              <pre className="text-xs bg-gray-100 p-2 rounded mt-2 overflow-auto">
                {JSON.stringify(scenario.odl, null, 2)}
              </pre>
            </details>
          </CardContent>
        </Card>
      ))}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Legenda</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 rounded"></div>
            <span>Segmento con dati reali da timeline</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 opacity-75 border-2 border-dashed border-gray-400 rounded"></div>
            <span>Segmento con dati stimati (fallback)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-1 h-4 bg-blue-600 rounded animate-pulse"></div>
            <span>Indicatore stato corrente</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 
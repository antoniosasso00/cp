'use client'

import React from 'react'
import { ThemeSelector } from '@/components/ui/theme-toggle'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Settings, Palette, Database, Zap } from 'lucide-react'

export default function ImpostazioniPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Settings className="h-8 w-8" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Impostazioni</h1>
          <p className="text-muted-foreground">
            Configura le preferenze dell'applicazione CarbonPilot
          </p>
        </div>
      </div>

      <div className="grid gap-6">
        {/* Sezione Tema */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="h-5 w-5" />
              Aspetto e Tema
            </CardTitle>
            <CardDescription>
              Personalizza l'aspetto dell'interfaccia utente
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="text-sm font-medium mb-3">Modalità del tema</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Scegli il tema dell'interfaccia. La modalità "Sistema" seguirà le preferenze del tuo dispositivo.
              </p>
              <ThemeSelector />
            </div>
          </CardContent>
        </Card>

        {/* Sezione Database */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Database
            </CardTitle>
            <CardDescription>
              Informazioni sulla configurazione del database
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Tipo database:</span>
                <span className="text-sm text-muted-foreground">SQLite (Sviluppo)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Stato connessione:</span>
                <span className="text-sm text-green-600 font-medium">🟢 Connesso</span>
              </div>
              <Separator />
              <p className="text-xs text-muted-foreground">
                💡 Il database è attualmente configurato per SQLite in modalità sviluppo. 
                Per passare a PostgreSQL in produzione, modifica il flag nel file di configurazione backend.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Sezione Performance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Prestazioni e Aggiornamenti
            </CardTitle>
            <CardDescription>
              Configurazioni relative alla velocità e al refresh dell'applicazione
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Aggiornamento automatico:</span>
                <span className="text-sm text-green-600 font-medium">🟢 Attivo</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Refresh cache:</span>
                <span className="text-sm text-muted-foreground">5 secondi</span>
              </div>
              <Separator />
              <p className="text-xs text-muted-foreground">
                📈 Gli ODL e Tool vengono aggiornati automaticamente per mantenere i dati sincronizzati tra le fasi di produzione.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 
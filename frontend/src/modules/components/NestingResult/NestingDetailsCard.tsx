'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'
import { 
  Package, 
  Flame, 
  Target, 
  Weight, 
  Ruler,
  Clock
} from 'lucide-react'

interface AutoclaveInfo {
  id: number
  nome: string
  lunghezza: number
  larghezza_piano: number
  codice: string
  produttore?: string
}

interface BatchNestingResult {
  id: string
  nome: string
  stato: string
  autoclave_id: number
  autoclave?: AutoclaveInfo
  odl_ids: number[]
  created_at: string
  updated_at?: string
  numero_nesting: number
  peso_totale_kg?: number
  area_totale_utilizzata?: number
  valvole_totali_utilizzate?: number
  note?: string
  configurazione_json: {
    canvas_width: number
    canvas_height: number
    tool_positions: any[]
  } | null
  metrics?: {
    efficiency_percentage?: number
    total_area_used_mm2?: number
    total_weight_kg?: number
  }
}

interface NestingDetailsCardProps {
  batch: BatchNestingResult
}

export default function NestingDetailsCard({ batch }: NestingDetailsCardProps) {
  const toolsPositioned = batch.configurazione_json?.tool_positions?.length || 0
  const efficiency = batch.metrics?.efficiency_percentage || 0

  const getEfficiencyColor = (eff: number) => {
    if (eff >= 80) return 'text-green-600 bg-green-50 border-green-200'
    if (eff >= 60) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    return 'text-red-600 bg-red-50 border-red-200'
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Package className="h-5 w-5" />
          Panoramica Batch
        </CardTitle>
        <CardDescription>
          Informazioni generali e metriche di efficienza
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Informazioni base */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">Nome Batch</p>
            <p className="font-semibold text-sm">{batch.nome}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">N° Nesting</p>
            <p className="font-semibold text-sm">#{batch.numero_nesting}</p>
          </div>
        </div>

        {/* Data creazione */}
        <div className="flex items-center gap-2 p-2 bg-muted/50 rounded">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <div className="text-sm">
            <span className="text-muted-foreground">Creato: </span>
            <span className="font-medium">
              {new Date(batch.created_at).toLocaleString('it-IT')}
            </span>
          </div>
        </div>

        {/* Autoclave */}
        {batch.autoclave && (
          <div className="space-y-2">
            <h4 className="font-medium text-sm flex items-center gap-2">
              <Flame className="h-4 w-4" />
              Autoclave
            </h4>
            <div className="p-3 bg-muted/30 rounded space-y-1">
              <p className="font-semibold text-sm">{batch.autoclave.nome}</p>
              <p className="text-xs text-muted-foreground">
                {batch.autoclave.larghezza_piano} × {batch.autoclave.lunghezza} mm
              </p>
              {batch.autoclave.produttore && (
                <p className="text-xs text-muted-foreground">
                  {batch.autoclave.produttore}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Efficienza */}
        <div className="space-y-2">
          <h4 className="font-medium text-sm flex items-center gap-2">
            <Target className="h-4 w-4" />
            Efficienza
          </h4>
          <div className={`p-3 rounded border ${getEfficiencyColor(efficiency)}`}>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {efficiency.toFixed(1)}%
              </div>
              <p className="text-xs opacity-80">
                Area utilizzata
              </p>
            </div>
          </div>
        </div>

        {/* Statistiche */}
        <div className="grid grid-cols-1 gap-3">
          <div className="flex items-center justify-between p-2 bg-muted/30 rounded">
            <div className="flex items-center gap-2">
              <Package className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">ODL Totali</span>
            </div>
            <span className="font-semibold">{batch.odl_ids.length}</span>
          </div>

          <div className="flex items-center justify-between p-2 bg-muted/30 rounded">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">ODL Posizionati</span>
            </div>
            <span className="font-semibold">{toolsPositioned}</span>
          </div>

          {batch.peso_totale_kg && (
            <div className="flex items-center justify-between p-2 bg-muted/30 rounded">
              <div className="flex items-center gap-2">
                <Weight className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Peso Totale</span>
              </div>
              <span className="font-semibold">{batch.peso_totale_kg.toFixed(2)} kg</span>
            </div>
          )}

          {batch.area_totale_utilizzata && (
            <div className="flex items-center justify-between p-2 bg-muted/30 rounded">
              <div className="flex items-center gap-2">
                <Ruler className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Area Utilizzata</span>
              </div>
              <span className="font-semibold">{batch.area_totale_utilizzata.toFixed(2)} cm²</span>
            </div>
          )}

          {batch.valvole_totali_utilizzate && (
            <div className="flex items-center justify-between p-2 bg-muted/30 rounded">
              <div className="flex items-center gap-2">
                <Package className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Valvole</span>
              </div>
              <span className="font-semibold">{batch.valvole_totali_utilizzate}</span>
            </div>
          )}
        </div>

        {/* Note */}
        {batch.note && (
          <div className="space-y-2">
            <h4 className="font-medium text-sm">Note</h4>
            <div className="p-2 bg-muted/30 rounded">
              <p className="text-xs text-muted-foreground">{batch.note}</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 
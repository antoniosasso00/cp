'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Package, 
  Clock, 
  CheckCircle, 
  XCircle,
  Loader2,
  RefreshCw,
  Eye,
  Plus,
  AlertTriangle
} from 'lucide-react'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { nestingApi, type NestingResponse } from '@/lib/api'
import { useUserRole } from '@/hooks/useUserRole'
import { NestingStatusBadge } from '@/components/nesting/NestingStatusBadge'
import { formatDateIT } from '@/lib/utils'

/**
 * Componente per visualizzare una panoramica dei nesting nella dashboard
 * Mostra i nesting raggruppati per stato con azioni specifiche per ruolo
 */
export function NestingStatusCard() {
  const { role } = useUserRole()
  const [nestings, setNestings] = useState<NestingResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchNestings = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await nestingApi.getAll({ 
        ruolo_utente: role || undefined
      })
      setNestings(data)
    } catch (err) {
      console.error('Errore nel caricamento nesting:', err)
      setError('Errore nel caricamento dei dati')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (role) {
      fetchNestings()
    }
  }, [role])

  const handleRefresh = () => {
    fetchNestings()
  }

  // Raggruppa i nesting per stato
  const nestingsByStatus = {
    'In sospeso': nestings.filter(n => n.stato === 'In sospeso'),
    'Confermato': nestings.filter(n => n.stato === 'Confermato'),
    'Completato': nestings.filter(n => n.stato === 'Completato'),
    'Annullato': nestings.filter(n => n.stato === 'Annullato')
  }

  // Calcola statistiche
  const stats = {
    total: nestings.length,
    inSospeso: nestingsByStatus['In sospeso'].length,
    confermati: nestingsByStatus['Confermato'].length,
    completati: nestingsByStatus['Completato'].length,
    annullati: nestingsByStatus['Annullato'].length
  }

  // Determina il messaggio e le azioni in base al ruolo
  const getRoleSpecificContent = () => {
    if (role === 'AUTOCLAVISTA') {
      return {
        title: 'Nesting da Confermare',
        description: 'Nesting in attesa della tua conferma di carico',
        primaryAction: stats.inSospeso > 0 ? 'Conferma Carichi' : 'Nessun carico in attesa',
        showInSospeso: true
      }
    } else if (role === 'RESPONSABILE') {
      return {
        title: 'Gestione Nesting',
        description: 'Panoramica completa di tutti i nesting',
        primaryAction: 'Gestisci Tutti',
        showInSospeso: false
      }
    } else {
      return {
        title: 'Stato Nesting',
        description: 'Panoramica dei nesting di produzione',
        primaryAction: 'Visualizza Tutti',
        showInSospeso: false
      }
    }
  }

  const roleContent = getRoleSpecificContent()

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              {roleContent.title}
            </CardTitle>
            <CardDescription>
              {roleContent.description}
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="text-center py-4">
            <AlertTriangle className="h-8 w-8 text-destructive mx-auto mb-2" />
            <p className="text-sm text-muted-foreground mb-3">{error}</p>
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Riprova
            </Button>
          </div>
        ) : isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">Caricamento...</span>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Statistiche rapide */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="text-center p-3 rounded-lg bg-yellow-50 border border-yellow-200">
                <div className="text-2xl font-bold text-yellow-700">{stats.inSospeso}</div>
                <div className="text-xs text-yellow-600">In Sospeso</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-blue-50 border border-blue-200">
                <div className="text-2xl font-bold text-blue-700">{stats.confermati}</div>
                <div className="text-xs text-blue-600">Confermati</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-green-50 border border-green-200">
                <div className="text-2xl font-bold text-green-700">{stats.completati}</div>
                <div className="text-xs text-green-600">Completati</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-gray-50 border border-gray-200">
                <div className="text-2xl font-bold text-gray-700">{stats.annullati}</div>
                <div className="text-xs text-gray-600">Annullati</div>
              </div>
            </div>

            {/* Lista nesting prioritari */}
            {roleContent.showInSospeso && stats.inSospeso > 0 ? (
              <div>
                <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                  <Clock className="h-4 w-4 text-yellow-600" />
                  Nesting in Attesa di Conferma ({stats.inSospeso})
                </h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {nestingsByStatus['In sospeso'].slice(0, 5).map((nesting) => (
                    <div
                      key={nesting.id}
                      className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium">Nesting #{nesting.id}</span>
                          <NestingStatusBadge 
                            stato={nesting.stato} 
                            confermato_da_ruolo={nesting.confermato_da_ruolo}
                          />
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {nesting.autoclave.nome} • {nesting.odl_list.length} ODL
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Creato: {formatDateIT(new Date(nesting.created_at))}
                        </p>
                      </div>
                      <div className="text-right">
                        <Badge variant="secondary" className="text-xs">
                          {Math.round((nesting.area_utilizzata / nesting.area_totale) * 100)}% area
                        </Badge>
                      </div>
                    </div>
                  ))}
                  {stats.inSospeso > 5 && (
                    <div className="text-center py-2">
                      <span className="text-xs text-muted-foreground">
                        +{stats.inSospeso - 5} altri nesting in sospeso
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div>
                <h4 className="text-sm font-medium mb-3">Nesting Recenti</h4>
                {nestings.length === 0 ? (
                  <div className="text-center py-6">
                    <Package className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                    <p className="text-sm text-muted-foreground">Nessun nesting trovato</p>
                  </div>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {nestings.slice(0, 3).map((nesting) => (
                      <div
                        key={nesting.id}
                        className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm font-medium">Nesting #{nesting.id}</span>
                            <NestingStatusBadge 
                              stato={nesting.stato} 
                              confermato_da_ruolo={nesting.confermato_da_ruolo}
                            />
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {nesting.autoclave.nome} • {nesting.odl_list.length} ODL
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-muted-foreground">
                            {formatDateIT(new Date(nesting.created_at))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Azioni */}
            <div className="pt-3 border-t space-y-2">
              <Link href="/dashboard/nesting">
                <Button className="w-full" variant="outline">
                  <Eye className="h-4 w-4 mr-2" />
                  {roleContent.primaryAction}
                </Button>
              </Link>
              
              {role === 'RESPONSABILE' && (
                <Link href="/dashboard/nesting?tab=manual">
                  <Button className="w-full" variant="secondary" size="sm">
                    <Plus className="h-4 w-4 mr-2" />
                    Crea Nesting Manuale
                  </Button>
                </Link>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 
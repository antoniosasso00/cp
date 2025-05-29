'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Plus } from 'lucide-react'
import { NestingTable } from '@/components/nesting/NestingTable'
import { EmptyState } from '@/components/ui/EmptyState'
import { nestingApi, NestingResponse } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AlertTriangle } from 'lucide-react'
import { Package } from 'lucide-react'

interface NestingManualTabProps {
  nestingList: NestingResponse[]
  isLoading: boolean
  onRefresh: () => Promise<void>
}

export function NestingManualTab({ nestingList, isLoading, onRefresh }: NestingManualTabProps) {
  const [isCreating, setIsCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  // Funzione per creare un nuovo nesting manuale
  const handleCreateNesting = async () => {
    try {
      setIsCreating(true)
      const newNesting = await nestingApi.create({})
      
      toast({
        title: "Nesting Creato",
        description: `Nuovo nesting manuale #${newNesting.id} creato con successo`,
      })
      
      onRefresh()
    } catch (error) {
      toast({
        title: "Errore",
        description: "Impossibile creare il nuovo nesting",
        variant: "destructive",
      })
    } finally {
      setIsCreating(false)
    }
  }

  // Fallback per errori
  if (error && !isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Nesting Manuali</CardTitle>
          <CardDescription>
            Gestisci i nesting creati manualmente
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Errore</AlertTitle>
            <AlertDescription>
              Errore nel caricamento dei nesting manuali. Riprova più tardi.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Nesting Manuali</CardTitle>
            <CardDescription>
              Gestisci i nesting creati manualmente. Puoi creare nuovi nesting vuoti e configurarli secondo le tue esigenze.
            </CardDescription>
          </div>
          <Button
            onClick={handleCreateNesting}
            disabled={isCreating}
            className="flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            {isCreating ? 'Creazione...' : 'Nuovo Nesting'}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {/* Fallback per lista vuota */}
        {!isLoading && nestingList.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium">Nessun nesting disponibile</p>
            <p className="text-sm">Crea il primo nesting manuale utilizzando i pulsanti sopra.</p>
          </div>
        ) : (
          <NestingTable 
            data={nestingList} 
            isLoading={isLoading}
            onRefresh={onRefresh}
          />
        )}
      </CardContent>
    </Card>
  )
} 
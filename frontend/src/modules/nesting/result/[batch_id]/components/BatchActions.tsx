'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card'
import { Button } from '@/shared/components/ui/button'
import { Badge } from '@/shared/components/ui/badge'
import { Separator } from '@/shared/components/ui/separator'
import { 
  Save, 
  CheckCircle2, 
  X, 
  Trash2,
  AlertTriangle,
  Loader2,
  Download,
  FileText
} from 'lucide-react'
import { useToast } from '@/shared/components/ui/use-toast'

interface BatchActionsProps {
  batchId: string
  batchState: string
  onSaveDraft?: () => Promise<void>
  onConfirm?: () => Promise<void>
  onCancel?: () => Promise<void>
  onDelete?: () => Promise<void>
  onDownload?: () => void
  onExportReport?: () => void
  isLoading?: boolean
  className?: string
}

const BatchActions: React.FC<BatchActionsProps> = ({
  batchId,
  batchState,
  onSaveDraft,
  onConfirm,
  onCancel,
  onDelete,
  onDownload,
  onExportReport,
  isLoading = false,
  className = ''
}) => {
  const { toast } = useToast()
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const handleAction = async (action: string, callback?: () => Promise<void>) => {
    if (!callback) return
    
    setActionLoading(action)
    try {
      await callback()
      toast({
        title: "Successo",
        description: `Azione ${action} completata con successo`,
      })
    } catch (error) {
      toast({
        title: "Errore",
        description: `Errore durante l'azione ${action}`,
        variant: "destructive"
      })
    } finally {
      setActionLoading(null)
    }
  }

  const getStateInfo = (state: string) => {
    switch (state?.toLowerCase()) {
      case 'draft':
        return {
          label: 'Draft',
          color: 'bg-orange-100 text-orange-800 border-orange-200',
          actions: ['save', 'cancel', 'delete']
        }
      case 'sospeso':
        return {
          label: 'Sospeso',
          color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
          actions: ['confirm', 'cancel', 'delete']
        }
      case 'confermato':
        return {
          label: 'Confermato',
          color: 'bg-green-100 text-green-800 border-green-200',
          actions: ['download', 'export']
        }
      case 'loaded':
        return {
          label: 'Caricato',
          color: 'bg-blue-100 text-blue-800 border-blue-200',
          actions: ['download', 'export']
        }
      case 'cured':
        return {
          label: 'In Cura',
          color: 'bg-red-100 text-red-800 border-red-200',
          actions: ['download', 'export']
        }
      case 'completato':
        return {
          label: 'Completato',
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          actions: ['download', 'export']
        }
      default:
        return {
          label: state,
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          actions: ['download', 'export']
        }
    }
  }

  const stateInfo = getStateInfo(batchState)

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-sm">
          <span>Azioni Batch</span>
          <Badge variant="outline" className={stateInfo.color}>
            {stateInfo.label}
          </Badge>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-3">
        {/* Azioni principali basate sullo stato */}
        <div className="space-y-2">
          {stateInfo.actions.includes('save') && onSaveDraft && (
            <Button
              onClick={() => handleAction('salva draft', onSaveDraft)}
              disabled={isLoading || actionLoading !== null}
              className="w-full"
              variant="default"
            >
              {actionLoading === 'salva draft' ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              Salva Draft
            </Button>
          )}

          {stateInfo.actions.includes('confirm') && onConfirm && (
            <Button
              onClick={() => handleAction('conferma', onConfirm)}
              disabled={isLoading || actionLoading !== null}
              className="w-full"
              variant="default"
            >
              {actionLoading === 'conferma' ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle2 className="h-4 w-4 mr-2" />
              )}
              Conferma Batch
            </Button>
          )}

          {stateInfo.actions.includes('download') && onDownload && (
            <Button
              onClick={onDownload}
              disabled={isLoading}
              className="w-full"
              variant="outline"
            >
              <Download className="h-4 w-4 mr-2" />
              Download
            </Button>
          )}

          {stateInfo.actions.includes('export') && onExportReport && (
            <Button
              onClick={onExportReport}
              disabled={isLoading}
              className="w-full"
              variant="outline"
            >
              <FileText className="h-4 w-4 mr-2" />
              Export Report
            </Button>
          )}
        </div>

        <Separator />

        {/* Azioni secondarie */}
        <div className="space-y-2">
          {stateInfo.actions.includes('cancel') && onCancel && (
            <Button
              onClick={() => handleAction('annulla', onCancel)}
              disabled={isLoading || actionLoading !== null}
              className="w-full"
              variant="outline"
            >
              {actionLoading === 'annulla' ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <X className="h-4 w-4 mr-2" />
              )}
              Annulla
            </Button>
          )}

          {stateInfo.actions.includes('delete') && onDelete && (
            <Button
              onClick={() => handleAction('elimina', onDelete)}
              disabled={isLoading || actionLoading !== null}
              className="w-full"
              variant="destructive"
            >
              {actionLoading === 'elimina' ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4 mr-2" />
              )}
              Elimina
            </Button>
          )}
        </div>

        {/* Info batch */}
        <Separator />
        <div className="text-xs text-gray-500 space-y-1">
          <div>Batch ID: {batchId.slice(0, 8)}...</div>
          <div>Stato: {stateInfo.label}</div>
        </div>

        {/* Warning per stati critici */}
        {(batchState === 'draft' || batchState === 'sospeso') && (
          <div className="flex items-start gap-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs">
            <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="text-yellow-800">
              {batchState === 'draft' 
                ? 'Batch in modalità draft. Salvare per rendere permanente.'
                : 'Batch sospeso. Confermare per procedere con la produzione.'
              }
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default BatchActions 
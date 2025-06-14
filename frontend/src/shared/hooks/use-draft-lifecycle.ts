import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useStandardToast } from './use-standard-toast'
import { useNavigationGuard } from './use-navigation-guard'

// Interfaccia allineata con BatchData dalla pagina nesting
interface DraftBatch {
  id: string
  nome: string
  stato: string
  autoclave_id?: number | null
  created_at?: string | null
  updated_at?: string | null
  // Aggiungi altre proprietà opzionali se necessarie
  [key: string]: any
}

interface UseDraftLifecycleProps {
  allBatches: DraftBatch[]
  selectedBatchId: string
  onBatchChange: (batchId: string, batchData: DraftBatch) => void
  onBatchRemoved: (batchId: string) => void
}

interface DraftLifecycleState {
  hasUnsavedDrafts: boolean
  showExitDialog: boolean
  pendingNavigation: (() => void) | null
  savingDraft: string | null
}

export function useDraftLifecycle({
  allBatches,
  selectedBatchId,
  onBatchChange,
  onBatchRemoved
}: UseDraftLifecycleProps) {
  const router = useRouter()
  const { toast } = useStandardToast()
  
  // 🚀 PERFORMANCE: Use ref to avoid stale closures
  const onBatchChangeRef = useRef(onBatchChange)
  const onBatchRemovedRef = useRef(onBatchRemoved)
  
  useEffect(() => {
    onBatchChangeRef.current = onBatchChange
    onBatchRemovedRef.current = onBatchRemoved
  }, [onBatchChange, onBatchRemoved])

  const [state, setState] = useState<DraftLifecycleState>({
    hasUnsavedDrafts: false,
    showExitDialog: false,
    pendingNavigation: null,
    savingDraft: null
  })

  // 🛡️ HELPER: Verifica se un batch è draft (memoized for performance)
  const isDraftBatch = useCallback((batch: DraftBatch | null): boolean => {
    if (!batch?.stato) return false
    const stato = batch.stato.toLowerCase()
    return stato === 'draft' || stato === 'bozza'
  }, [])

  // 🚀 PERFORMANCE: Memoized draft count calculation
  const draftCount = useMemo(() => {
    return allBatches.filter(isDraftBatch).length
  }, [allBatches, isDraftBatch])

  // 🚀 PERFORMANCE: Memoized draft batches list
  const draftBatches = useMemo(() => {
    return allBatches.filter(isDraftBatch)
  }, [allBatches, isDraftBatch])

  // 🔄 AGGIORNA STATO: Monitora i draft non salvati
  useEffect(() => {
    setState(prev => ({ ...prev, hasUnsavedDrafts: draftCount > 0 }))
  }, [draftCount])

  // 🚫 NAVIGATION GUARD: Intercetta navigazione interna
  const handleAttemptedNavigation = useCallback((href: string, navigationFn: () => void) => {
    console.log(`🚫 Navigazione intercettata verso: ${href}`, { draftCount })
    
    if (draftCount > 0) {
      setState(prev => ({ 
        ...prev, 
        pendingNavigation: navigationFn,
        showExitDialog: true 
      }))
    } else {
      navigationFn()
    }
  }, [draftCount])

  // Attiva il guard solo se ci sono draft
  useNavigationGuard({
    enabled: draftCount > 0,
    onAttemptedNavigation: handleAttemptedNavigation
  })

  // 🛡️ LIFECYCLE MANAGEMENT: Setup cleanup automatico con edge cases
  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (draftCount > 0) {
        event.preventDefault()
        const message = `Hai ${draftCount} bozze non salvate che andranno perse. Sei sicuro di voler uscire?`
        event.returnValue = message
        return message
      }
    }

    // 🛡️ EDGE CASE: Only add listener if there are drafts
    if (draftCount > 0) {
      window.addEventListener('beforeunload', handleBeforeUnload)
    }
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
      // 🛡️ EDGE CASE: Only cleanup if component unmounting with drafts
      if (draftCount > 0) {
        // Delayed cleanup to avoid race conditions
        setTimeout(() => {
          cleanupAllDrafts().catch(console.warn)
        }, 100)
      }
    }
  }, [draftCount])

  // 🧹 CLEANUP: Elimina tutti i draft con retry logic (generale)
  const cleanupAllDrafts = useCallback(async (retries = 3) => {
    if (draftBatches.length === 0) return

    try {
      console.log(`🧹 Cleanup automatico: eliminazione ${draftBatches.length} draft`)
      
      const response = await fetch('/api/batch_nesting/draft/cleanup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // ✅ TIMEOUT RIMOSSO: Sincrono senza AbortSignal.timeout problematico
      })

      if (!response.ok && retries > 0) {
        console.warn(`⚠️ Cleanup tentativo fallito, retry... (${retries} rimanenti)`)
        await new Promise(resolve => setTimeout(resolve, 1000))
        return cleanupAllDrafts(retries - 1)
      }

      if (response.ok) {
        console.log('✅ Cleanup automatico draft completato')
      } else {
        console.warn('⚠️ Cleanup automatico fallito definitivamente')
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'TimeoutError') {
        console.warn('⚠️ Timeout cleanup automatico draft')
      } else {
        console.warn('⚠️ Errore cleanup automatico draft:', error)
      }
      
      // 🛡️ EDGE CASE: Retry on network errors
      if (retries > 0) {
        await new Promise(resolve => setTimeout(resolve, 2000))
        return cleanupAllDrafts(retries - 1)
      }
    }
  }, [draftBatches])

  // 🗑️ DELETE ALL CURRENT DRAFTS: Elimina specificamente tutti i draft correnti
  const deleteAllCurrentDrafts = useCallback(async () => {
    if (draftBatches.length === 0) return { successful: 0, failed: 0 }

    console.log(`🗑️ Eliminazione specifica di ${draftBatches.length} draft correnti`)

    const deletePromises = draftBatches.map(batch => 
      Promise.race([
        fetch(`/api/batch_nesting/draft/${batch.id}`, {
          method: 'DELETE'
        }).then(response => ({
          batchId: batch.id,
          batchName: batch.nome,
          success: response.ok,
          response
        })),
        // Timeout per ogni richiesta
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Timeout')), 10000)
        )
      ])
    )

    const results = await Promise.allSettled(deletePromises)
    
    let successful = 0
    let failed = 0
    const deletedBatches: string[] = []

    results.forEach((result, index) => {
      if (result.status === 'fulfilled' && (result.value as any).success) {
        successful++
        deletedBatches.push(draftBatches[index].id)
        console.log(`✅ Draft eliminato: ${(result.value as any).batchName}`)
      } else {
        failed++
        console.warn(`❌ Errore eliminazione draft: ${draftBatches[index].nome}`, 
          result.status === 'rejected' ? result.reason : 'Response non OK')
      }
    })

    console.log(`🗑️ Eliminazione completata: ${successful} successi, ${failed} fallimenti`)
    
    return { 
      successful, 
      failed, 
      deletedBatches,
      totalAttempted: draftBatches.length 
    }
  }, [draftBatches])

  // 🔒 NAVIGATION GUARD: Intercetta navigazione
  const handleNavigation = useCallback((navigationFn: () => void) => {
    if (state.hasUnsavedDrafts) {
      setState(prev => ({ 
        ...prev, 
        pendingNavigation: () => navigationFn,
        showExitDialog: true 
      }))
    } else {
      navigationFn()
    }
  }, [state.hasUnsavedDrafts])

  // 🛡️ CONFIRM EXIT: Gestisce conferma uscita
  const handleConfirmExit = useCallback(async () => {
    setState(prev => ({ ...prev, showExitDialog: false }))
    await cleanupAllDrafts()
    if (state.pendingNavigation) {
      state.pendingNavigation()
      setState(prev => ({ ...prev, pendingNavigation: null }))
    }
  }, [cleanupAllDrafts, state.pendingNavigation])

  // 💾 SAVE ALL: Salva tutte le bozze con ottimizzazioni
  const handleSaveAllDrafts = useCallback(async () => {
    if (draftBatches.length === 0) {
      setState(prev => ({ ...prev, showExitDialog: false }))
      if (state.pendingNavigation) {
        state.pendingNavigation()
        setState(prev => ({ ...prev, pendingNavigation: null }))
      }
      return
    }

    try {
      setState(prev => ({ ...prev, savingDraft: 'all' }))
      toast({
        title: 'Salvataggio bozze',
        description: `Salvataggio di ${draftBatches.length} bozze in corso...`
      })

      // 🚀 PERFORMANCE: Batch save with parallel processing and timeout
      const savePromises = draftBatches.map(batch => 
        Promise.race([
          fetch(`/api/batch_nesting/draft/${batch.id}/confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              confermato_da_utente: 'ADMIN',
              confermato_da_ruolo: 'ADMIN'
            })
          }),
          // 🛡️ EDGE CASE: Timeout per request
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Timeout')), 15000)
          )
        ])
      )

      const results = await Promise.allSettled(savePromises)
      
      // 🛡️ EDGE CASE: Better error analysis
      const successful = results.filter(r => 
        r.status === 'fulfilled' && (r.value as Response).ok
      ).length
      const failed = results.length - successful
      const timeouts = results.filter(r => 
        r.status === 'rejected' && r.reason?.message === 'Timeout'
      ).length

      if (successful > 0) {
        toast({
          title: '✅ Bozze salvate',
          description: `${successful} bozze salvate con successo${failed > 0 ? `, ${failed} fallite` : ''}${timeouts > 0 ? ` (${timeouts} timeout)` : ''}`
        })
      }

      if (failed > 0) {
        toast({
          title: '⚠️ Salvataggio parziale',
          description: `${failed} bozze non sono state salvate${timeouts > 0 ? ` (${timeouts} per timeout)` : ''}`,
          variant: 'destructive'
        })
      }

      setState(prev => ({ ...prev, showExitDialog: false }))
      if (state.pendingNavigation) {
        state.pendingNavigation()
        setState(prev => ({ ...prev, pendingNavigation: null }))
      }

    } catch (error) {
      console.error('Errore salvataggio bozze:', error)
      toast({
        title: 'Errore salvataggio',
        description: error instanceof Error ? error.message : 'Impossibile salvare tutte le bozze',
        variant: 'destructive'
      })
    } finally {
      setState(prev => ({ ...prev, savingDraft: null }))
    }
  }, [draftBatches, toast, state.pendingNavigation])

  // 🔄 SWITCH TAB: Passa al prossimo batch disponibile con ottimizzazioni
  const switchToNextAvailableBatch = useCallback(() => {
    // 🚀 PERFORMANCE: Use memoized filtered batches
    const remainingBatches = allBatches.filter(batch => batch.id !== selectedBatchId)
    
    if (remainingBatches.length > 0) {
      // 🛡️ EDGE CASE: Priorità ottimizzata - prima i draft da gestire, poi gli altri
      const nextDraft = remainingBatches.find(isDraftBatch)
      const nextBatch = nextDraft || remainingBatches[0]
      
      console.log(`🔄 Switch automatico: ${selectedBatchId} → ${nextBatch.id}`)
      onBatchChange(nextBatch.id, nextBatch)
      
      toast({
        title: 'Passaggio automatico',
        description: `Visualizzo il batch ${nextBatch.nome}`,
        variant: 'default'
      })
    } else {
      // Nessun batch rimanente, torna alla lista
      console.log('🔄 Nessun batch rimanente, redirect alla lista')
      toast({
        title: 'Gestione completata',
        description: 'Tutti i batch sono stati gestiti. Torno alla lista...',
        variant: 'default'
      })
      setTimeout(() => router.push('/nesting/list'), 2000)
    }
  }, [allBatches, selectedBatchId, isDraftBatch, onBatchChange, toast, router])

  // 💾 SAVE DRAFT: Salva singola bozza
  const handleSaveDraft = useCallback(async (batchId: string) => {
    try {
      setState(prev => ({ ...prev, savingDraft: batchId }))
      toast({
        title: 'Salvataggio bozza',
        description: 'Promozione a stato "Sospeso" in corso...'
      })
      
      const response = await fetch(`/api/batch_nesting/draft/${batchId}/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          confermato_da_utente: 'ADMIN',
          confermato_da_ruolo: 'ADMIN'
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Errore durante il salvataggio')
      }

      const result = await response.json()
      
      // Rimuovi il batch dalla lista locale (ora è SOSPESO)
      onBatchRemoved(batchId)
      
      toast({
        title: '✅ Bozza salvata con successo',
        description: `Batch promosso a stato "Sospeso" (ID: ${result.persistent_batch_id})`
      })
      
      // Switch automatico se abbiamo salvato il batch corrente
      if (batchId === selectedBatchId) {
        setTimeout(switchToNextAvailableBatch, 1500)
      }
      
    } catch (error) {
      console.error('Errore salvataggio bozza:', error)
      toast({
        title: 'Errore salvataggio',
        description: `Impossibile salvare la bozza: ${error instanceof Error ? error.message : 'Errore sconosciuto'}`,
        variant: 'destructive'
      })
    } finally {
      setState(prev => ({ ...prev, savingDraft: null }))
    }
  }, [selectedBatchId, onBatchRemoved, switchToNextAvailableBatch, toast])

  // 🗑️ DELETE DRAFT: Elimina singola bozza (senza conferma - sarà gestita dal dialog)
  const handleDeleteDraft = useCallback(async (batchId: string) => {
    const batch = allBatches.find(b => b.id === batchId)
    const batchName = batch?.nome || batchId

    try {
      setState(prev => ({ ...prev, savingDraft: batchId }))
      toast({
        title: 'Eliminazione bozza',
        description: `Eliminazione "${batchName}" in corso...`
      })
      
      const response = await fetch(`/api/batch_nesting/draft/${batchId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Errore durante l\'eliminazione')
      }

      // Rimuovi dalla lista locale
      onBatchRemoved(batchId)
      
      toast({
        title: '🗑️ Bozza eliminata',
        description: `"${batchName}" eliminata con successo`
      })
      
      // Switch automatico se abbiamo eliminato il batch corrente
      if (batchId === selectedBatchId) {
        setTimeout(switchToNextAvailableBatch, 1500)
      }
      
    } catch (error) {
      console.error('Errore eliminazione bozza:', error)
      toast({
        title: 'Errore eliminazione',
        description: `Impossibile eliminare la bozza: ${error instanceof Error ? error.message : 'Errore sconosciuto'}`,
        variant: 'destructive'
      })
    } finally {
      setState(prev => ({ ...prev, savingDraft: null }))
    }
  }, [allBatches, selectedBatchId, onBatchRemoved, switchToNextAvailableBatch, toast])

  // 🚪 FORCED EXIT: Gestione uscita forzata dalla pagina
  const handleExitWithoutSaving = useCallback(async () => {
    try {
      console.log('🚪 Uscita forzata: eliminazione bozze in corso...')
      
      setState(prev => ({ ...prev, showExitDialog: false }))
      
      if (draftBatches.length === 0) {
        console.log('🚪 Nessuna bozza da eliminare, navigazione diretta')
        if (state.pendingNavigation) {
          state.pendingNavigation()
          setState(prev => ({ ...prev, pendingNavigation: null }))
        }
        return
      }
      
      // Toast di conferma eliminazione
      toast({
        title: '🗑️ Eliminazione bozze',
        description: `Eliminazione di ${draftBatches.length} bozze in corso...`
      })
      
      // Elimina specificamente tutti i draft correnti dal database
      const deleteResult = await deleteAllCurrentDrafts()
      
      // Rimuovi i draft eliminati con successo dalla lista locale
      if (deleteResult?.deletedBatches) {
        deleteResult.deletedBatches.forEach(batchId => {
          onBatchRemoved(batchId)
        })
      }
      
      // Toast di feedback basato sui risultati
      if (deleteResult && deleteResult.successful > 0) {
        if (deleteResult.failed === 0) {
          toast({
            title: '✅ Bozze eliminate',
            description: `Tutte le ${deleteResult.successful} bozze sono state eliminate con successo`
          })
        } else {
          toast({
            title: '⚠️ Eliminazione parziale',
            description: `${deleteResult.successful} bozze eliminate, ${deleteResult.failed} fallite`,
            variant: 'destructive'
          })
        }
      } else {
        toast({
          title: '❌ Errore eliminazione',
          description: 'Nessuna bozza è stata eliminata dal database',
          variant: 'destructive'
        })
      }
      
      // Esegui la navigazione pendente dopo un breve delay
      setTimeout(() => {
        if (state.pendingNavigation) {
          console.log('🚪 Eseguendo navigazione pendente...')
          state.pendingNavigation()
          setState(prev => ({ ...prev, pendingNavigation: null }))
        }
      }, 1000)
      
    } catch (error) {
      console.error('Errore durante uscita forzata:', error)
      toast({
        title: 'Errore durante l\'uscita',
        description: 'Si è verificato un errore durante l\'eliminazione delle bozze',
        variant: 'destructive'
      })
      
      // Anche in caso di errore, esegui la navigazione per non bloccare l'utente
      setTimeout(() => {
        if (state.pendingNavigation) {
          console.log('🚪 Eseguendo navigazione pendente (dopo errore)...')
          state.pendingNavigation()
          setState(prev => ({ ...prev, pendingNavigation: null }))
        }
      }, 1500)
    }
  }, [deleteAllCurrentDrafts, state.pendingNavigation, draftBatches, onBatchRemoved, toast])

  // 🛡️ STAY ON PAGE: Rimani nella pagina
  const handleStayOnPage = useCallback(() => {
    setState(prev => ({ 
      ...prev, 
      showExitDialog: false,
      pendingNavigation: null
    }))
  }, [])

  // 💾 SAVE AND EXIT: Salva tutto ed esci
  const handleSaveAndExit = useCallback(async () => {
    try {
      console.log('💾 Salvataggio e uscita: inizio processo...')
      
      setState(prev => ({ ...prev, showExitDialog: false }))
      
      if (draftBatches.length === 0) {
        console.log('💾 Nessuna bozza da salvare, navigazione diretta')
        if (state.pendingNavigation) {
          state.pendingNavigation()
          setState(prev => ({ ...prev, pendingNavigation: null }))
        }
        return
      }

      // Usa la logica di salvataggio esistente ma con navigazione garantita
      setState(prev => ({ ...prev, savingDraft: 'all' }))
      toast({
        title: 'Salvataggio bozze',
        description: `Salvataggio di ${draftBatches.length} bozze in corso...`
      })

      // 🚀 PERFORMANCE: Batch save with parallel processing and timeout
      const savePromises = draftBatches.map(batch => 
        Promise.race([
          fetch(`/api/batch_nesting/draft/${batch.id}/confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              confermato_da_utente: 'ADMIN',
              confermato_da_ruolo: 'ADMIN'
            })
          }),
          // 🛡️ EDGE CASE: Timeout per request
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Timeout')), 15000)
          )
        ])
      )

      const results = await Promise.allSettled(savePromises)
      
      // 🛡️ EDGE CASE: Better error analysis
      const successful = results.filter(r => 
        r.status === 'fulfilled' && (r.value as Response).ok
      ).length
      const failed = results.length - successful
      const timeouts = results.filter(r => 
        r.status === 'rejected' && r.reason?.message === 'Timeout'
      ).length

      // Rimuovi i batch salvati con successo dalla lista locale
      if (successful > 0) {
        const successfulBatches = draftBatches.slice(0, successful)
        successfulBatches.forEach(batch => {
          onBatchRemoved(batch.id)
        })
      }

      if (successful > 0) {
        toast({
          title: '✅ Bozze salvate',
          description: `${successful} bozze salvate con successo${failed > 0 ? `, ${failed} fallite` : ''}${timeouts > 0 ? ` (${timeouts} timeout)` : ''}`
        })
      }

      if (failed > 0) {
        toast({
          title: '⚠️ Salvataggio parziale',
          description: `${failed} bozze non sono state salvate${timeouts > 0 ? ` (${timeouts} per timeout)` : ''}`,
          variant: 'destructive'
        })
      }

      // Esegui SEMPRE la navigazione, anche in caso di errori parziali
      setTimeout(() => {
        if (state.pendingNavigation) {
          console.log('💾 Eseguendo navigazione pendente dopo salvataggio...')
          state.pendingNavigation()
          setState(prev => ({ ...prev, pendingNavigation: null }))
        }
      }, 1500)

    } catch (error) {
      console.error('Errore salvataggio e uscita:', error)
      toast({
        title: 'Errore salvataggio',
        description: error instanceof Error ? error.message : 'Impossibile salvare tutte le bozze',
        variant: 'destructive'
      })
      
      // Anche in caso di errore totale, esegui la navigazione
      setTimeout(() => {
        if (state.pendingNavigation) {
          console.log('💾 Eseguendo navigazione pendente (dopo errore)...')
          state.pendingNavigation()
          setState(prev => ({ ...prev, pendingNavigation: null }))
        }
      }, 2000)
    } finally {
      setState(prev => ({ ...prev, savingDraft: null }))
    }
  }, [draftBatches, state.pendingNavigation, onBatchRemoved, toast])

  // 🔄 DIALOG HANDLERS
  const setShowExitDialog = useCallback((show: boolean) => {
    setState(prev => ({ ...prev, showExitDialog: show }))
  }, [])

  return {
    // 🚀 PERFORMANCE: Memoized state values
    hasUnsavedDrafts: state.hasUnsavedDrafts,
    showExitDialog: state.showExitDialog,
    savingDraft: state.savingDraft,
    draftCount, // Already memoized
    
    // 🛡️ EDGE CASE: Enhanced actions with error handling
    handleNavigation,
    handleConfirmExit,
    handleSaveAllDrafts,
    handleSaveDraft,
    handleDeleteDraft,
    setShowExitDialog,
    switchToNextAvailableBatch,
    isDraftBatch,
    
    // 🚪 NEW: Page exit management
    handleExitWithoutSaving,
    handleStayOnPage,
    handleSaveAndExit,
    
    // 🧹 INTEGRATION: Cleanup and utility functions
    cleanupAllDrafts,
    deleteAllCurrentDrafts,
    draftBatches // Provide access to memoized draft batches list
  }
} 
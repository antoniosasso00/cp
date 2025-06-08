/**
 * Sistema di notifiche standardizzato per CarbonPilot
 * 
 * Questo servizio centralizza tutte le notifiche dell'app con:
 * - Posizionamento uniforme e non invasivo
 * - Tipologie standard (success, error, warning, info)
 * - Durate ottimizzate per leggibilità
 * - Prevenzione duplicati
 * - Template per messaggi comuni
 */

import { toast } from '@/components/ui/use-toast'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface ToastOptions {
  type: ToastType
  title: string
  message?: string
  duration?: number
  priority?: 'high' | 'normal' | 'low'
  context?: string // per debugging e analytics
}

export interface OperationToastOptions {
  operation: string
  entity?: string
  entityId?: string | number
  details?: string
}

/**
 * Servizio centralizzato per notifiche standardizzate
 */
export class ToastService {
  private static instance: ToastService
  private activeToasts = new Set<string>()
  private readonly MAX_CONCURRENT_TOASTS = 3
  
  // Durate standard per ogni tipo di notifica
  private readonly DURATIONS = {
    success: 3000,    // Breve, messaggio positivo
    error: 6000,      // Più lungo per permettere lettura errore
    warning: 5000,    // Medio per warning importanti
    info: 4000        // Standard per informazioni
  }

  static getInstance(): ToastService {
    if (!ToastService.instance) {
      ToastService.instance = new ToastService()
    }
    return ToastService.instance
  }

  /**
   * Mostra notifica standardizzata
   */
  show(options: ToastOptions): void {
    const {
      type,
      title,
      message,
      duration = this.DURATIONS[type],
      priority = 'normal',
      context
    } = options

    // Prevenzione duplicati basata su titolo+messaggio
    const key = `${title}-${message || ''}`
    if (this.activeToasts.has(key)) {
      console.warn('Toast duplicato prevenuto:', { title, message, context })
      return
    }

    // Gestione priorità: toast ad alta priorità rimuovono quelli normali
    if (priority === 'high' && this.activeToasts.size >= this.MAX_CONCURRENT_TOASTS) {
      this.clearLowPriorityToasts()
    }

    // Aggiungi alla lista attivi
    this.activeToasts.add(key)

    // Mostra toast con configurazione standard
    const toastResult = toast({
      title: this.formatTitle(type, title),
      description: message,
      variant: this.getToastVariant(type),
      duration,
    })

    // Rimuovi dalla lista quando si chiude
    setTimeout(() => {
      this.activeToasts.delete(key)
    }, duration)

    // Log per debugging in development
    if (process.env.NODE_ENV === 'development') {
      console.log('🔔 Toast mostrato:', {
        type,
        title,
        message,
        duration,
        context,
        activeCount: this.activeToasts.size
      })
    }
  }

  /**
   * Template per operazioni CRUD comuni
   */
  showOperation(result: 'success' | 'error', options: OperationToastOptions): void {
    const { operation, entity = 'elemento', entityId, details } = options

    if (result === 'success') {
      this.show({
        type: 'success',
        title: `${operation} completato`,
        message: `${entity}${entityId ? ` #${entityId}` : ''} ${this.getOperationPastTense(operation)} con successo${details ? `. ${details}` : ''}`,
        context: `crud-${operation}-${entity}`
      })
    } else {
      this.show({
        type: 'error',
        title: `Errore ${operation.toLowerCase()}`,
        message: `Impossibile ${this.getOperationInfinitive(operation)} ${entity}${entityId ? ` #${entityId}` : ''}${details ? `. ${details}` : ''}`,
        priority: 'high',
        context: `crud-error-${operation}-${entity}`
      })
    }
  }

  /**
   * Template per errori API standardizzati
   */
  showApiError(error: {
    status?: number
    message: string
    endpoint?: string
    operation?: string
  }): void {
    const { status, message, endpoint, operation } = error

    let title = 'Errore API'
    let description = message
    let priority: 'high' | 'normal' = 'high'

    // Personalizza in base al tipo di errore
    if (status === 0) {
      title = 'Errore di Connessione'
      description = 'Impossibile connettersi al server. Verifica la connessione.'
    } else if (status === 404) {
      title = 'Risorsa Non Trovata'
      description = `Endpoint non disponibile${endpoint ? `: ${endpoint}` : ''}`
      priority = 'normal'
    } else if (status === 422) {
      title = 'Dati Non Validi'
      description = 'I dati inseriti non sono corretti. Controlla i campi richiesti.'
    } else if (status && status >= 500) {
      title = 'Errore del Server'
      description = 'Si è verificato un errore interno. Riprova più tardi.'
    }

    this.show({
      type: 'error',
      title,
      message: description,
      priority,
      duration: 7000, // Errori API hanno durata più lunga
      context: `api-error-${status || 'unknown'}-${operation || endpoint}`
    })
  }

  /**
   * Template per conferme di stato
   */
  showStatusChange(entity: string, fromStatus: string, toStatus: string, entityId?: string | number): void {
    this.show({
      type: 'success',
      title: 'Stato Aggiornato',
      message: `${entity}${entityId ? ` #${entityId}` : ''} aggiornato da "${fromStatus}" a "${toStatus}"`,
      context: `status-change-${entity}`
    })
  }

  /**
   * Template per warning di efficienza/qualità
   */
  showQualityWarning(type: 'efficiency' | 'quality' | 'validation', value: number | string, threshold?: number): void {
    let title: string
    let message: string

    switch (type) {
      case 'efficiency':
        title = `⚠️ Efficienza ${value}%`
        message = `Il batch ha un'efficienza${threshold ? ` sotto il ${threshold}%` : ' bassa'}. Considera di rigenerare il layout.`
        break
      case 'quality':
        title = '⚠️ Controllo Qualità'
        message = `Rilevato problema di qualità: ${value}. Verifica i parametri.`
        break
      case 'validation':
        title = '⚠️ Validazione'
        message = `${value}. Controlla i dati inseriti.`
        break
    }

    this.show({
      type: 'warning',
      title,
      message,
      context: `quality-warning-${type}`
    })
  }

  /**
   * Utility methods
   */
  private formatTitle(type: ToastType, title: string): string {
    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    }
    
    // Se il titolo contiene già un'emoji, non aggiungere l'icona
    if (/[\u2600-\u26FF]|[\u2700-\u27BF]|[\uD83C-\uDBFF][\uDC00-\uDFFF]/.test(title)) {
      return title
    }
    
    return `${icons[type]} ${title}`
  }

  private getToastVariant(type: ToastType): 'default' | 'destructive' | 'success' | 'warning' | 'info' {
    switch (type) {
      case 'success':
        return 'success'
      case 'error':
        return 'destructive'
      case 'warning':
        return 'warning'
      case 'info':
        return 'info'
      default:
        return 'default'
    }
  }

  private getOperationPastTense(operation: string): string {
    const mapping: Record<string, string> = {
      'Creazione': 'creato',
      'Aggiornamento': 'aggiornato',
      'Eliminazione': 'eliminato',
      'Salvataggio': 'salvato',
      'Caricamento': 'caricato',
      'Conferma': 'confermato',
      'Avvio': 'avviato',
      'Terminazione': 'terminato'
    }
    return mapping[operation] || operation.toLowerCase()
  }

  private getOperationInfinitive(operation: string): string {
    const mapping: Record<string, string> = {
      'Creazione': 'creare',
      'Aggiornamento': 'aggiornare',
      'Eliminazione': 'eliminare',
      'Salvataggio': 'salvare',
      'Caricamento': 'caricare',
      'Conferma': 'confermare',
      'Avvio': 'avviare',
      'Terminazione': 'terminare'
    }
    return mapping[operation] || operation.toLowerCase()
  }

  private clearLowPriorityToasts(): void {
    // In una implementazione futura, qui si potrebbero chiudere i toast esistenti
    // Per ora, semplicemente limitiamo il numero massimo
    console.log('Limite toast raggiunti, alcuni potrebbero essere nascosti')
  }

  /**
   * Metodi di convenienza per uso rapido
   */
  success(title: string, message?: string): void {
    this.show({ type: 'success', title, message })
  }

  error(title: string, message?: string, priority?: 'high' | 'normal'): void {
    this.show({ type: 'error', title, message, priority })
  }

  warning(title: string, message?: string): void {
    this.show({ type: 'warning', title, message })
  }

  info(title: string, message?: string): void {
    this.show({ type: 'info', title, message })
  }
}

// Export istanza singleton per uso diretto
export const toastService = ToastService.getInstance()

// Export metodi di convenienza
export const showSuccess = (title: string, message?: string) => toastService.success(title, message)
export const showError = (title: string, message?: string, priority?: 'high' | 'normal') => toastService.error(title, message, priority)
export const showWarning = (title: string, message?: string) => toastService.warning(title, message)
export const showInfo = (title: string, message?: string) => toastService.info(title, message)

// Export template methods  
export const showOperationResult = (result: 'success' | 'error', options: OperationToastOptions) => toastService.showOperation(result, options)
export const showApiError = (error: Parameters<typeof toastService.showApiError>[0]) => toastService.showApiError(error)
export const showStatusChange = (entity: string, fromStatus: string, toStatus: string, entityId?: string | number) => toastService.showStatusChange(entity, fromStatus, toStatus, entityId)
export const showQualityWarning = (type: 'efficiency' | 'quality' | 'validation', value: number | string, threshold?: number) => toastService.showQualityWarning(type, value, threshold) 
import { useCallback } from 'react'

interface NestingAuditResult {
  success: boolean
  missing: string[]
  warnings: string[]
}

export function useNestingAudit() {
  const runNestingAudit = useCallback((): NestingAuditResult => {
    const missing: string[] = []
    const warnings: string[] = []

    // Verifica presenza bottoni essenziali nel DOM
    const confirmButton = document.querySelector('[data-nesting-action="confirm"]')
    const deleteButton = document.querySelector('[data-nesting-action="delete"]')
    const viewButton = document.querySelector('[data-nesting-action="view"]')
    const backButton = document.querySelector('[data-nesting-action="back"]')

    if (!confirmButton) missing.push("❌ Pulsante Conferma mancante")
    if (!deleteButton) missing.push("❌ Pulsante Elimina mancante")
    if (!viewButton) missing.push("❌ Pulsante Visualizza mancante")
    if (!backButton) missing.push("❌ Pulsante Torna indietro mancante")

    // Verifica canvas nesting
    const nestingCanvas = document.querySelector('[data-nesting-canvas]')
    if (!nestingCanvas) missing.push("❌ Canvas nesting non visibile")

    // Verifica presenza dati ODL
    const odlList = document.querySelector('[data-odl-list]')
    const odlItems = document.querySelectorAll('[data-odl-item]')
    if (!odlList) warnings.push("⚠️ Lista ODL non trovata")
    if (odlItems.length === 0) warnings.push("⚠️ Nessun ODL visualizzato")

    // Verifica stato API endpoints
    const apiStatusElement = document.querySelector('[data-api-status]')
    if (apiStatusElement) {
      const status = apiStatusElement.getAttribute('data-status')
      if (status === 'error') missing.push("❌ Errore API backend")
      if (status === 'loading') warnings.push("⚠️ API ancora in caricamento")
    }

    // Verifica selezione modalità nesting
    const nestingModeSelector = document.querySelector('[data-nesting-mode-selector]')
    if (!nestingModeSelector) missing.push("❌ Selettore modalità nesting mancante")

    // Verifica presenza step indicator
    const stepIndicator = document.querySelector('[data-step-indicator]')
    if (!stepIndicator) warnings.push("⚠️ Indicatore di progresso step mancante")

    const success = missing.length === 0

    // Log risultati audit
    if (success && warnings.length === 0) {
      console.log("✅ Nesting Audit: Tutto OK")
    } else {
      if (missing.length > 0) {
        console.error("📋 Nesting Audit - Errori critici:", missing)
      }
      if (warnings.length > 0) {
        console.warn("📋 Nesting Audit - Avvisi:", warnings)
      }
    }

    return { success, missing, warnings }
  }, [])

  return { runNestingAudit }
} 
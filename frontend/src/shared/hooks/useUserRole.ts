'use client'

import { useState, useEffect, useCallback } from 'react'

// Definizione dei ruoli disponibili
export type UserRole = 'ADMIN' | 'Management' | 'Clean Room' | 'Curing'

// Chiave per localStorage
const STORAGE_KEY = 'userRole'

/**
 * Hook personalizzato per gestire il ruolo dell'utente
 * 
 * Questo hook:
 * - Legge il ruolo da localStorage al primo caricamento
 * - Mantiene il ruolo in uno state React per performance
 * - Fornisce funzioni per impostare, leggere e cancellare il ruolo
 * - Sincronizza automaticamente localStorage e state
 */
export function useUserRole() {
  const [role, setRoleState] = useState<UserRole | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Carica il ruolo da localStorage al primo mount
  useEffect(() => {
    try {
      const savedRole = localStorage.getItem(STORAGE_KEY) as UserRole | null
      if (savedRole && ['ADMIN', 'Management', 'Clean Room', 'Curing'].includes(savedRole)) {
        setRoleState(savedRole)
      }
    } catch (error) {
      console.error('Errore nel caricamento del ruolo da localStorage:', error)
    } finally {
      setIsLoading(false)
    }
  }, [])

  /**
   * Imposta un nuovo ruolo
   * Aggiorna sia localStorage che lo state React
   */
  const setRole = useCallback((newRole: UserRole) => {
    try {
      localStorage.setItem(STORAGE_KEY, newRole)
      setRoleState(newRole)
    } catch (error) {
      console.error('Errore nel salvare il ruolo in localStorage:', error)
    }
  }, [])

  /**
   * Ottiene il ruolo corrente
   * Restituisce il ruolo dallo state React (più veloce di localStorage)
   */
  const getRole = useCallback((): UserRole | null => {
    return role
  }, [role])

  /**
   * Cancella il ruolo corrente
   * Rimuove sia da localStorage che dallo state React
   */
  const clearRole = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY)
      setRoleState(null)
    } catch (error) {
      console.error('Errore nella rimozione del ruolo da localStorage:', error)
    }
  }, [])

  /**
   * Verifica se l'utente ha un ruolo specifico
   */
  const hasRole = useCallback((targetRole: UserRole): boolean => {
    return role === targetRole
  }, [role])

  /**
   * Verifica se l'utente è un admin
   */
  const isAdmin = useCallback((): boolean => {
    return role === 'ADMIN'
  }, [role])

  return {
    role,
    isLoading,
    setRole,
    getRole,
    clearRole,
    hasRole,
    isAdmin
  }
} 
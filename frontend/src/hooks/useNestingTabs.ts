'use client'

import { useState, useEffect } from 'react'
import { useSearchParams, useRouter, usePathname } from 'next/navigation'

export type NestingTabValue = 
  | 'manual' 
  | 'preview' 
  | 'parameters' 
  | 'multi-autoclave' 
  | 'confirmed' 
  | 'reports'

const STORAGE_KEY = 'nesting-active-tab'
const DEFAULT_TAB: NestingTabValue = 'manual'

export function useNestingTabs() {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  
  // Ottieni il tab dall'URL o dal localStorage
  const getInitialTab = (): NestingTabValue => {
    // Prima controlla l'URL
    const urlTab = searchParams.get('tab') as NestingTabValue
    if (urlTab && isValidTab(urlTab)) {
      return urlTab
    }
    
    // Poi controlla il localStorage
    if (typeof window !== 'undefined') {
      const savedTab = localStorage.getItem(STORAGE_KEY) as NestingTabValue
      if (savedTab && isValidTab(savedTab)) {
        return savedTab
      }
    }
    
    return DEFAULT_TAB
  }

  const [activeTab, setActiveTab] = useState<NestingTabValue>(getInitialTab)

  // Funzione per validare se un tab è valido
  function isValidTab(tab: string): tab is NestingTabValue {
    return ['manual', 'preview', 'parameters', 'multi-autoclave', 'confirmed', 'reports'].includes(tab)
  }

  // Funzione per cambiare tab
  const changeTab = (newTab: NestingTabValue) => {
    setActiveTab(newTab)
    
    // Salva nel localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, newTab)
    }
    
    // Aggiorna l'URL
    const params = new URLSearchParams(searchParams.toString())
    params.set('tab', newTab)
    router.push(`${pathname}?${params.toString()}`, { scroll: false })
  }

  // Effetto per sincronizzare con i cambiamenti dell'URL
  useEffect(() => {
    const urlTab = searchParams.get('tab') as NestingTabValue
    if (urlTab && isValidTab(urlTab) && urlTab !== activeTab) {
      setActiveTab(urlTab)
      // Salva anche nel localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem(STORAGE_KEY, urlTab)
      }
    }
  }, [searchParams, activeTab])

  return {
    activeTab,
    changeTab,
    isValidTab
  }
} 
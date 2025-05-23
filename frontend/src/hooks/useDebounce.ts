import { useState, useEffect } from 'react'

/**
 * Hook personalizzato per implementare il debounce su un valore
 * Utile per ottimizzare le chiamate API durante la digitazione
 * 
 * @param value - Il valore da "debounceare"
 * @param delay - Il ritardo in millisecondi (default: 500ms)
 * @returns Il valore debounced
 */
export function useDebounce<T>(value: T, delay: number = 500): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    // Imposta un timer per aggiornare il valore debounced
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    // Pulisce il timer se il valore cambia prima che scada
    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
} 
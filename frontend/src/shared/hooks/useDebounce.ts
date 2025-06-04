import { useState, useEffect } from 'react'

/**
 * Hook personalizzato per implementare il debounce
 * @param value - Il valore da "debounceare"
 * @param delay - Il ritardo in millisecondi (default: 300ms)
 * @returns Il valore debouncato
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    // Imposta un timer per aggiornare il valore debouncato
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
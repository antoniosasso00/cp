import * as React from "react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface SafeSelectProps {
  value?: string | null
  onValueChange: (value: string) => void
  placeholder?: string
  children: React.ReactNode
  className?: string
  disabled?: boolean
  allOptionLabel?: string
  allOptionValue?: string
}

/**
 * SafeSelect - Wrapper per Select che gestisce automaticamente i valori vuoti
 * 
 * Questo componente risolve il problema di Radix UI Select che non accetta
 * valori vuoti ("") per le SelectItem. Converte automaticamente:
 * - Valori vuoti/null in input → valore "all" per il Select
 * - Valore "all" dal Select → stringa vuota per l'applicazione
 * 
 * Uso:
 * <SafeSelect 
 *   value={filter} 
 *   onValueChange={setFilter}
 *   allOptionLabel="Tutti gli elementi"
 * >
 *   <SelectItem value="option1">Opzione 1</SelectItem>
 *   <SelectItem value="option2">Opzione 2</SelectItem>
 * </SafeSelect>
 */
export function SafeSelect({
  value,
  onValueChange,
  placeholder,
  children,
  className,
  disabled = false,
  allOptionLabel = "Tutti",
  allOptionValue = "all"
}: SafeSelectProps) {
  // Converte il valore in input per il Select
  const selectValue = value || allOptionValue

  // Gestisce il cambio valore dal Select
  const handleValueChange = (newValue: string) => {
    // Se è il valore "all", passa stringa vuota all'applicazione
    const appValue = newValue === allOptionValue ? "" : newValue
    onValueChange(appValue)
  }

  return (
    <Select 
      value={selectValue} 
      onValueChange={handleValueChange}
      disabled={disabled}
    >
      <SelectTrigger className={className}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={allOptionValue}>{allOptionLabel}</SelectItem>
        {children}
      </SelectContent>
    </Select>
  )
}

export default SafeSelect 
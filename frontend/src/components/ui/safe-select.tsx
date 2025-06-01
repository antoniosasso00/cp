import * as React from "react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface SafeSelectProps {
  value?: string | number | null
  onValueChange: (value: string) => void
  placeholder?: string
  children: React.ReactNode
  className?: string
  disabled?: boolean
  allOptionLabel?: string
  allOptionValue?: string
  required?: boolean
}

/**
 * SafeSelect - Wrapper per Select che gestisce automaticamente i valori vuoti
 * 
 * Questo componente risolve il problema di Radix UI Select che non accetta
 * valori vuoti ("") per le SelectItem. Converte automaticamente:
 * - Valori vuoti/null/undefined in input → valore "all" (o valore specificato) per il Select
 * - Valore "all" dal Select → stringa vuota per l'applicazione
 * 
 * Uso:
 * <SafeSelect 
 *   value={filter} 
 *   onValueChange={setFilter}
 *   allOptionLabel="Tutti gli elementi"
 *   placeholder="Seleziona un'opzione"
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
  allOptionValue = "all",
  required = false
}: SafeSelectProps) {
  // Converte il valore in input per il Select - gestisce tutti i casi null/undefined/""
  const selectValue = React.useMemo(() => {
    if (value === null || value === undefined || value === "") {
      return allOptionValue
    }
    return String(value)
  }, [value, allOptionValue])

  // Gestisce il cambio valore dal Select
  const handleValueChange = React.useCallback((newValue: string) => {
    // Se è il valore "all", passa stringa vuota all'applicazione
    const appValue = newValue === allOptionValue ? "" : newValue
    onValueChange(appValue)
  }, [onValueChange, allOptionValue])

  return (
    <Select 
      value={selectValue} 
      onValueChange={handleValueChange}
      disabled={disabled}
      required={required}
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
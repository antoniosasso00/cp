'use client'

import React from 'react'
import { cn } from '@/lib/utils'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { AlertCircle } from 'lucide-react'

interface SelectOption {
  value: string | number
  label: string
  disabled?: boolean
}

interface FormSelectProps {
  label: string
  name: string
  value: string | number | undefined
  onChange: (value: any) => void
  options: SelectOption[]
  placeholder?: string
  disabled?: boolean
  loading?: boolean
  error?: string
  description?: string
  required?: boolean
  className?: string
  selectClassName?: string
  emptyMessage?: string
}

export function FormSelect({
  label,
  name,
  value,
  onChange,
  options,
  placeholder = "Seleziona un'opzione",
  disabled = false,
  loading = false,
  error,
  description,
  required = false,
  className,
  selectClassName,
  emptyMessage = "Nessuna opzione disponibile"
}: FormSelectProps) {
  const handleValueChange = (newValue: string) => {
    // Converti il valore in numero se necessario
    const option = options.find(opt => String(opt.value) === newValue)
    if (option) {
      onChange(option.value)
    }
  }

  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={name} className="text-sm font-medium">
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>
      
              <Select
          value={value && value !== 0 ? String(value) : undefined}
          onValueChange={handleValueChange}
          disabled={disabled || loading}
        >
        <SelectTrigger 
          className={cn(
            "transition-colors",
            error && "border-destructive focus:ring-destructive",
            loading && "animate-pulse cursor-not-allowed",
            selectClassName
          )}
        >
          <SelectValue placeholder={loading ? "Caricamento..." : placeholder} />
        </SelectTrigger>
        <SelectContent>
          {options.length === 0 ? (
            <SelectItem value="__empty__" disabled>
              {emptyMessage}
            </SelectItem>
          ) : (
            options
              .filter(option => option.value !== "" && option.value !== null && option.value !== undefined)
              .map((option) => (
                <SelectItem 
                  key={String(option.value)} 
                  value={String(option.value)}
                  disabled={option.disabled}
                >
                  {option.label}
                </SelectItem>
              ))
          )}
        </SelectContent>
      </Select>
      
      {description && (
        <p className="text-xs text-muted-foreground">
          {description}
        </p>
      )}
      
      {error && (
        <div className="flex items-center gap-2 text-xs text-destructive">
          <AlertCircle className="h-3 w-3" />
          <span>{error}</span>
        </div>
      )}
    </div>
  )
} 
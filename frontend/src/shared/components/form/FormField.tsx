'use client'

import React from 'react'
import { cn } from '@/lib/utils'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { AlertCircle } from 'lucide-react'

interface FormFieldProps {
  label: string
  name: string
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'textarea'
  value: string | number | undefined | null
  onChange: (value: string | number | null) => void
  onBlur?: () => void
  placeholder?: string
  disabled?: boolean
  loading?: boolean
  error?: string
  description?: string
  required?: boolean
  className?: string
  inputClassName?: string
  rows?: number // per textarea
  min?: number // per number input
  max?: number // per number input
  step?: number // per number input
  allowEmpty?: boolean // per campi numerici opzionali
}

export function FormField({
  label,
  name,
  type = 'text',
  value,
  onChange,
  onBlur,
  placeholder,
  disabled = false,
  loading = false,
  error,
  description,
  required = false,
  className,
  inputClassName,
  rows = 3,
  min,
  max,
  step,
  allowEmpty = false
}: FormFieldProps) {
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const inputValue = e.target.value
    
    if (type === 'number') {
      // Se il campo è vuoto
      if (inputValue === '' || inputValue === null) {
        // Per campi opzionali o che permettono valori vuoti, restituisci null
        if (allowEmpty || !required) {
          onChange(null)
        } else {
          // Per campi obbligatori, mantieni il valore vuoto temporaneamente
          // Il validation dello schema gestirà l'errore
          onChange(null)
        }
        return
      }
      
      // Converti a numero
      const numericValue = parseFloat(inputValue)
      
      // Se la conversione fallisce (es. testo non numerico)
      if (isNaN(numericValue)) {
        // Mantieni il valore attuale se non è valido, per permettere editing
        // Il validation dello schema gestirà l'errore
        return
      }
      
      // Valore numerico valido
      onChange(numericValue)
    } else {
      // Campi di testo normali
      onChange(inputValue)
    }
  }

  // Gestione del valore da mostrare nell'input
  const getDisplayValue = () => {
    if (type === 'number') {
      // Se il valore è null o undefined, mostra stringa vuota
      if (value === null || value === undefined) {
        return ''
      }
      // Altrimenti mostra il valore numerico
      return String(value)
    }
    // Per campi di testo, mostra il valore o stringa vuota
    return value ?? ''
  }

  const commonProps = {
    id: name,
    name,
    value: getDisplayValue(),
    onChange: handleChange,
    onBlur,
    placeholder,
    disabled: disabled || loading,
    className: cn(
      "transition-colors",
      error && "border-destructive focus-visible:ring-destructive",
      loading && "animate-pulse",
      inputClassName
    )
  }

  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={name} className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>
      
      {type === 'textarea' ? (
        <Textarea
          {...commonProps}
          rows={rows}
        />
      ) : (
        <Input
          {...commonProps}
          type={type}
          min={min}
          max={max}
          step={step}
        />
      )}
      
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
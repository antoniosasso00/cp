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
  value: string | number | undefined
  onChange: (value: string | number) => void
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
  step
}: FormFieldProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const newValue = type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value
    onChange(newValue)
  }

  const commonProps = {
    id: name,
    name,
    value: value ?? '',
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
'use client'

import React from 'react'
import { cn } from '@/lib/utils'
import { Form } from '@/components/ui/form'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { UseFormReturn } from 'react-hook-form'
import { Loader2, Save, X } from 'lucide-react'

interface FormWrapperProps {
  form: UseFormReturn<any>
  onSubmit: (data: any) => void | Promise<void>
  children: React.ReactNode
  title?: string
  description?: string
  isLoading?: boolean
  submitText?: string
  submitVariant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'
  showCancel?: boolean
  onCancel?: () => void
  cancelText?: string
  className?: string
  cardClassName?: string
  headerClassName?: string
  contentClassName?: string
  footerClassName?: string
  disabled?: boolean
  // Opzioni aggiuntive per form avanzati
  showSaveAndNew?: boolean
  onSaveAndNew?: (data: any) => void | Promise<void>
  saveAndNewText?: string
}

export function FormWrapper({
  form,
  onSubmit,
  children,
  title,
  description,
  isLoading = false,
  submitText = "Salva",
  submitVariant = "default",
  showCancel = false,
  onCancel,
  cancelText = "Annulla",
  className,
  cardClassName,
  headerClassName,
  contentClassName,
  footerClassName,
  disabled = false,
  showSaveAndNew = false,
  onSaveAndNew,
  saveAndNewText = "Salva e Nuovo"
}: FormWrapperProps) {
  const handleSubmit = async (data: any) => {
    try {
      await onSubmit(data)
    } catch (error) {
      console.error('Form submission error:', error)
    }
  }

  const handleSaveAndNew = async (data: any) => {
    if (onSaveAndNew) {
      try {
        await onSaveAndNew(data)
      } catch (error) {
        console.error('Save and new error:', error)
      }
    }
  }

  const isFormDisabled = disabled || isLoading

  return (
    <div className={cn("space-y-6", className)}>
      <Card className={cn("", cardClassName)}>
        {(title || description) && (
          <CardHeader className={cn("", headerClassName)}>
            {title && (
              <CardTitle className="text-xl font-semibold">
                {title}
              </CardTitle>
            )}
            {description && (
              <p className="text-sm text-muted-foreground">
                {description}
              </p>
            )}
          </CardHeader>
        )}
        
        <CardContent className={cn("space-y-6 p-4 sm:p-6", contentClassName)}>
          <Form {...form}>
            <form 
              onSubmit={form.handleSubmit(handleSubmit)}
              className="space-y-6"
            >
              <div className="space-y-4">
                {children}
              </div>
              
              <div className={cn(
                "flex flex-col-reverse sm:flex-row sm:justify-end gap-2 pt-4 border-t border-border",
                footerClassName
              )}>
                {showCancel && onCancel && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={onCancel}
                    disabled={isFormDisabled}
                    className="w-full sm:w-auto"
                  >
                    <X className="h-4 w-4 mr-2" />
                    {cancelText}
                  </Button>
                )}
                
                {showSaveAndNew && onSaveAndNew && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={form.handleSubmit(handleSaveAndNew)}
                    disabled={isFormDisabled}
                    className="w-full sm:w-auto"
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4 mr-2" />
                    )}
                    {saveAndNewText}
                  </Button>
                )}
                
                <Button
                  type="submit"
                  variant={submitVariant}
                  disabled={isFormDisabled}
                  className="w-full sm:w-auto"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4 mr-2" />
                  )}
                  {submitText}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  )
} 
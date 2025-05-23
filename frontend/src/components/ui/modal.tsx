"use client"

import * as React from "react"
import { 
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
  DialogClose,
} from "./dialog"
import { Button } from "./button"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"

interface ModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  children: React.ReactNode
  size?: "sm" | "md" | "lg" | "xl" | "full"
  showCloseButton?: boolean
  onConfirm?: () => void
  onCancel?: () => void
  confirmText?: string
  cancelText?: string
  confirmVariant?: "default" | "destructive" | "success" | "warning"
  isLoading?: boolean
  className?: string
}

const sizeClasses = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-xl",
  full: "max-w-[90vw] max-h-[90vh]"
}

export function Modal({
  open,
  onOpenChange,
  title,
  description,
  children,
  size = "md",
  showCloseButton = true,
  onConfirm,
  onCancel,
  confirmText = "Conferma",
  cancelText = "Annulla",
  confirmVariant = "default",
  isLoading = false,
  className,
}: ModalProps) {
  const handleConfirm = () => {
    if (onConfirm && !isLoading) {
      onConfirm()
    }
  }

  const handleCancel = () => {
    if (onCancel && !isLoading) {
      onCancel()
    } else {
      onOpenChange(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent 
        className={cn(
          "shadow-modal rounded-2xl",
          sizeClasses[size],
          className
        )}
      >
        <DialogHeader className="space-y-3">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-xl font-semibold text-foreground">
              {title}
            </DialogTitle>
            {showCloseButton && (
              <DialogClose asChild>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-8 w-8 rounded-full"
                  disabled={isLoading}
                >
                  <X className="h-4 w-4" />
                  <span className="sr-only">Chiudi</span>
                </Button>
              </DialogClose>
            )}
          </div>
          {description && (
            <DialogDescription className="text-muted-foreground leading-relaxed">
              {description}
            </DialogDescription>
          )}
        </DialogHeader>

        <div className="py-4">
          {children}
        </div>

        {(onConfirm || onCancel) && (
          <DialogFooter className="gap-2 pt-4 border-t border-border">
            {onCancel && (
              <Button
                variant="outline"
                onClick={handleCancel}
                disabled={isLoading}
                className="flex-1 sm:flex-none"
              >
                {cancelText}
              </Button>
            )}
            {onConfirm && (
              <Button
                variant={confirmVariant}
                onClick={handleConfirm}
                loading={isLoading}
                className="flex-1 sm:flex-none"
              >
                {confirmText}
              </Button>
            )}
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  )
}

// Hook per gestire facilmente lo stato del modal
export function useModal(initialOpen = false) {
  const [open, setOpen] = React.useState(initialOpen)
  
  const openModal = React.useCallback(() => setOpen(true), [])
  const closeModal = React.useCallback(() => setOpen(false), [])
  const toggleModal = React.useCallback(() => setOpen(prev => !prev), [])

  return {
    open,
    setOpen,
    openModal,
    closeModal,
    toggleModal,
  }
} 
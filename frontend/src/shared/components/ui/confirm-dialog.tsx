"use client"

import * as React from "react"
import { Modal, useModal } from "./modal"
import { AlertTriangle, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface ConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title?: string
  description?: string
  confirmText?: string
  cancelText?: string
  onConfirm: () => void | Promise<void>
  isLoading?: boolean
  variant?: "danger" | "warning" | "info"
  itemName?: string
}

const variantConfig = {
  danger: {
    icon: Trash2,
    confirmVariant: "destructive" as const,
    iconColor: "text-destructive",
    defaultTitle: "Elimina elemento",
    defaultDescription: "Questa azione non può essere annullata.",
  },
  warning: {
    icon: AlertTriangle,
    confirmVariant: "warning" as const,
    iconColor: "text-warning",
    defaultTitle: "Conferma azione",
    defaultDescription: "Sei sicuro di voler procedere?",
  },
  info: {
    icon: AlertTriangle,
    confirmVariant: "default" as const,
    iconColor: "text-info",
    defaultTitle: "Conferma",
    defaultDescription: "Confermi questa azione?",
  },
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmText = "Conferma",
  cancelText = "Annulla",
  onConfirm,
  isLoading = false,
  variant = "danger",
  itemName,
}: ConfirmDialogProps) {
  const config = variantConfig[variant]
  const Icon = config.icon

  const handleConfirm = async () => {
    try {
      await onConfirm()
    } catch (error) {
      console.error("Errore durante la conferma:", error)
    }
  }

  const finalTitle = title || (itemName ? `${config.defaultTitle}: ${itemName}` : config.defaultTitle)
  const finalDescription = description || config.defaultDescription

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title={finalTitle}
      description={finalDescription}
      size="sm"
      onConfirm={handleConfirm}
      onCancel={() => onOpenChange(false)}
      confirmText={confirmText}
      cancelText={cancelText}
      confirmVariant={config.confirmVariant}
      isLoading={isLoading}
      className="text-center"
    >
      <div className="flex flex-col items-center space-y-4 py-4">
        <div className={cn(
          "rounded-full p-3 bg-opacity-10",
          config.iconColor,
          variant === "danger" && "bg-destructive/10",
          variant === "warning" && "bg-warning/10",
          variant === "info" && "bg-info/10"
        )}>
          <Icon className={cn("h-8 w-8", config.iconColor)} />
        </div>
        
        {itemName && (
          <div className="text-center space-y-2">
            <p className="text-sm text-muted-foreground">
              Elemento selezionato:
            </p>
            <p className="font-medium text-foreground bg-muted px-3 py-1 rounded-lg">
              {itemName}
            </p>
          </div>
        )}
      </div>
    </Modal>
  )
}

// Hook per gestire facilmente i dialoghi di conferma
export function useConfirmDialog() {
  const { open, openModal, closeModal, setOpen } = useModal()
  const [config, setConfig] = React.useState<Partial<ConfirmDialogProps>>({})

  const confirm = React.useCallback((options: Omit<ConfirmDialogProps, 'open' | 'onOpenChange'>) => {
    return new Promise<boolean>((resolve) => {
      setConfig({
        ...options,
        onConfirm: async () => {
          try {
            await options.onConfirm()
            resolve(true)
            closeModal()
          } catch (error) {
            resolve(false)
            // Non chiudiamo il modal in caso di errore
          }
        },
      })
      openModal()
    })
  }, [openModal, closeModal])

  const ConfirmDialogComponent = React.useCallback(() => {
    if (!config.onConfirm) return null
    
    return (
      <ConfirmDialog
        open={open}
        onOpenChange={setOpen}
        {...config}
        onConfirm={config.onConfirm}
      />
    )
  }, [open, setOpen, config])

  return {
    confirm,
    ConfirmDialog: ConfirmDialogComponent,
    isOpen: open,
  }
} 
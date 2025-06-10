'use client'

import React, { useState, useCallback } from 'react'
import { cn } from '@/shared/lib/utils'
import { ChevronDown, ChevronUp, Info, AlertCircle, CheckCircle, XCircle } from 'lucide-react'
import { Badge } from '@/shared/components/ui/badge'
import { Button } from '@/shared/components/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/components/ui/card'

export interface AccordionPanelItem {
  /** ID univoco del pannello */
  id: string
  /** Titolo del pannello */
  title: string
  /** Contenuto del pannello */
  content: React.ReactNode
  /** Badge opzionale */
  badge?: string
  /** Variante del badge */
  badgeVariant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning'
  /** Icona del pannello */
  icon?: 'info' | 'warning' | 'success' | 'error' | React.ReactNode
  /** Se il pannello è disabilitato */
  disabled?: boolean
  /** Stato iniziale (aperto/chiuso) */
  defaultOpen?: boolean
  /** Callback quando il pannello viene aperto/chiuso */
  onToggle?: (isOpen: boolean) => void
}

export interface AccordionPanelProps {
  /** Lista dei pannelli */
  items: AccordionPanelItem[]
  /** Se permettere apertura multipla */
  allowMultiple?: boolean
  /** Pannelli aperti inizialmente */
  defaultOpenItems?: string[]
  /** Variante dell'accordion */
  variant?: 'default' | 'minimal' | 'bordered'
  /** Classname aggiuntive */
  className?: string
  /** Se mostrare separatori tra pannelli */
  showSeparators?: boolean
}

const getIcon = (icon: AccordionPanelItem['icon']) => {
  if (React.isValidElement(icon)) {
    return icon
  }
  
  switch (icon) {
    case 'info':
      return <Info className="h-4 w-4 text-blue-600" />
    case 'warning':
      return <AlertCircle className="h-4 w-4 text-yellow-600" />
    case 'success':
      return <CheckCircle className="h-4 w-4 text-green-600" />
    case 'error':
      return <XCircle className="h-4 w-4 text-red-600" />
    default:
      return null
  }
}

const getVariantStyles = (variant: AccordionPanelProps['variant']) => {
  switch (variant) {
    case 'minimal':
      return 'border-0 shadow-none bg-transparent'
    case 'bordered':
      return 'border-2 shadow-md'
    default:
      return 'border shadow-sm'
  }
}

export const AccordionPanel: React.FC<AccordionPanelProps> = ({
  items,
  allowMultiple = false,
  defaultOpenItems = [],
  variant = 'default',
  className,
  showSeparators = true
}) => {
  const [openItems, setOpenItems] = useState<Set<string>>(
    new Set(defaultOpenItems)
  )

  const toggleItem = useCallback((itemId: string) => {
    const item = items.find(i => i.id === itemId)
    if (item?.disabled) return

    setOpenItems(prev => {
      const newOpenItems = new Set(prev)
      
      if (newOpenItems.has(itemId)) {
        newOpenItems.delete(itemId)
        item?.onToggle?.(false)
      } else {
        if (!allowMultiple) {
          newOpenItems.clear()
        }
        newOpenItems.add(itemId)
        item?.onToggle?.(true)
      }
      
      return newOpenItems
    })
  }, [items, allowMultiple])

  const isOpen = useCallback((itemId: string) => {
    return openItems.has(itemId)
  }, [openItems])

  return (
    <div className={cn('w-full space-y-2', className)}>
      {items.map((item, index) => {
        const itemIsOpen = isOpen(item.id)
        const showSeparator = showSeparators && index > 0

        return (
          <div key={item.id}>
            {showSeparator && <hr className="border-border" />}
            
            <Card className={cn(
              getVariantStyles(variant),
              'transition-all duration-200',
              item.disabled && 'opacity-50 cursor-not-allowed'
            )}>
              <CardHeader
                className={cn(
                  'p-4 cursor-pointer hover:bg-accent/50 transition-colors',
                  item.disabled && 'cursor-not-allowed hover:bg-transparent'
                )}
                onClick={() => toggleItem(item.id)}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {/* Icon */}
                    {item.icon && (
                      <div className="flex-shrink-0">
                        {getIcon(item.icon)}
                      </div>
                    )}

                    {/* Title */}
                    <h3 className="text-sm font-medium truncate flex-1">
                      {item.title}
                    </h3>

                    {/* Badge */}
                    {item.badge && (
                      <Badge 
                        variant={item.badgeVariant || 'secondary'} 
                        className="text-xs flex-shrink-0"
                      >
                        {item.badge}
                      </Badge>
                    )}
                  </div>

                  {/* Toggle Icon */}
                  <div className="flex-shrink-0">
                    {itemIsOpen ? (
                      <ChevronUp className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                </div>
              </CardHeader>

              {/* Content */}
              {itemIsOpen && (
                <CardContent className="pt-0 pb-4 px-4">
                  <div className="animate-in slide-in-from-top-2 duration-200">
                    {item.content}
                  </div>
                </CardContent>
              )}
            </Card>
          </div>
        )
      })}
    </div>
  )
}

// Hook per gestire lo stato dell'accordion
export const useAccordionState = (initialOpen: string[] = []) => {
  const [openItems, setOpenItems] = useState<Set<string>>(new Set(initialOpen))

  const toggle = useCallback((itemId: string) => {
    setOpenItems(prev => {
      const newSet = new Set(prev)
      if (newSet.has(itemId)) {
        newSet.delete(itemId)
      } else {
        newSet.add(itemId)
      }
      return newSet
    })
  }, [])

  const open = useCallback((itemId: string) => {
    setOpenItems(prev => {
      const newSet = new Set(prev)
      newSet.add(itemId)
      return newSet
    })
  }, [])

  const close = useCallback((itemId: string) => {
    setOpenItems(prev => {
      const newSet = new Set(prev)
      newSet.delete(itemId)
      return newSet
    })
  }, [])

  const closeAll = useCallback(() => {
    setOpenItems(new Set())
  }, [])

  const openAll = useCallback((itemIds: string[]) => {
    setOpenItems(new Set(itemIds))
  }, [])

  const isOpen = useCallback((itemId: string) => {
    return openItems.has(itemId)
  }, [openItems])

  return {
    openItems: Array.from(openItems),
    toggle,
    open,
    close,
    closeAll,
    openAll,
    isOpen
  }
}

// Componente singolo pannello per uso standalone
export interface SingleAccordionProps extends Omit<AccordionPanelItem, 'id'> {
  className?: string
  variant?: AccordionPanelProps['variant']
}

export const SingleAccordion: React.FC<SingleAccordionProps> = ({
  title,
  content,
  badge,
  badgeVariant,
  icon,
  disabled = false,
  defaultOpen = false,
  onToggle,
  className,
  variant = 'default'
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  const handleToggle = useCallback(() => {
    if (disabled) return
    
    const newState = !isOpen
    setIsOpen(newState)
    onToggle?.(newState)
  }, [isOpen, disabled, onToggle])

  return (
    <Card className={cn(
      getVariantStyles(variant),
      'transition-all duration-200',
      disabled && 'opacity-50 cursor-not-allowed',
      className
    )}>
      <CardHeader
        className={cn(
          'p-4 cursor-pointer hover:bg-accent/50 transition-colors',
          disabled && 'cursor-not-allowed hover:bg-transparent'
        )}
        onClick={handleToggle}
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            {icon && (
              <div className="flex-shrink-0">
                {getIcon(icon)}
              </div>
            )}

            <h3 className="text-sm font-medium truncate flex-1">
              {title}
            </h3>

            {badge && (
              <Badge 
                variant={badgeVariant || 'secondary'} 
                className="text-xs flex-shrink-0"
              >
                {badge}
              </Badge>
            )}
          </div>

          <div className="flex-shrink-0">
            {isOpen ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        </div>
      </CardHeader>

      {isOpen && (
        <CardContent className="pt-0 pb-4 px-4">
          <div className="animate-in slide-in-from-top-2 duration-200">
            {content}
          </div>
        </CardContent>
      )}
    </Card>
  )
}

export default AccordionPanel 
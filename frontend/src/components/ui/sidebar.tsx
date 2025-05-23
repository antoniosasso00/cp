"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "./button"
import { Badge } from "./badge"
import { ChevronLeft, ChevronRight, Menu, X } from "lucide-react"

interface SidebarItem {
  id: string
  label: string
  href: string
  icon?: React.ElementType
  badge?: {
    text: string
    variant?: "default" | "success" | "warning" | "error" | "info"
  }
  children?: SidebarItem[]
}

interface SidebarProps {
  items: SidebarItem[]
  className?: string
  collapsed?: boolean
  onCollapsedChange?: (collapsed: boolean) => void
  showToggle?: boolean
  logo?: React.ReactNode
  footer?: React.ReactNode
}

interface SidebarContextType {
  collapsed: boolean
  setCollapsed: (collapsed: boolean) => void
}

const SidebarContext = React.createContext<SidebarContextType | undefined>(undefined)

export function useSidebar() {
  const context = React.useContext(SidebarContext)
  if (!context) {
    throw new Error("useSidebar deve essere usato all'interno di un SidebarProvider")
  }
  return context
}

// Provider per gestire lo stato globale della sidebar
export function SidebarProvider({ 
  children, 
  defaultCollapsed = false 
}: { 
  children: React.ReactNode
  defaultCollapsed?: boolean 
}) {
  const [collapsed, setCollapsed] = React.useState(defaultCollapsed)

  return (
    <SidebarContext.Provider value={{ collapsed, setCollapsed }}>
      {children}
    </SidebarContext.Provider>
  )
}

// Componente principale Sidebar
export function Sidebar({
  items,
  className,
  collapsed: controlledCollapsed,
  onCollapsedChange,
  showToggle = true,
  logo,
  footer,
}: SidebarProps) {
  const pathname = usePathname()
  const context = React.useContext(SidebarContext)
  
  // Usa lo stato dal context se disponibile, altrimenti usa lo stato locale
  const [localCollapsed, setLocalCollapsed] = React.useState(false)
  const collapsed = controlledCollapsed ?? context?.collapsed ?? localCollapsed
  const setCollapsed = onCollapsedChange ?? context?.setCollapsed ?? setLocalCollapsed

  const handleToggle = () => {
    setCollapsed(!collapsed)
  }

  return (
    <div
      className={cn(
        "flex flex-col bg-sidebar-bg border-r border-border transition-all duration-300",
        collapsed ? "w-16" : "w-64",
        className
      )}
    >
      {/* Header con logo e toggle */}
      <div className="flex items-center justify-between p-4 border-b border-border/50">
        {!collapsed && logo && (
          <div className="flex items-center space-x-2">
            {logo}
          </div>
        )}
        {showToggle && (
          <Button
            variant="ghost"
            size="icon"
            onClick={handleToggle}
            className="h-8 w-8 ml-auto"
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        )}
      </div>

      {/* Navigation items */}
      <nav className="flex-1 p-2 space-y-1">
        {items.map((item) => (
          <SidebarNavItem
            key={item.id}
            item={item}
            collapsed={collapsed}
            currentPath={pathname}
          />
        ))}
      </nav>

      {/* Footer */}
      {footer && !collapsed && (
        <div className="p-4 border-t border-border/50">
          {footer}
        </div>
      )}
    </div>
  )
}

// Componente per singolo item di navigazione
function SidebarNavItem({
  item,
  collapsed,
  currentPath,
  level = 0,
}: {
  item: SidebarItem
  collapsed: boolean
  currentPath: string
  level?: number
}) {
  const [isOpen, setIsOpen] = React.useState(false)
  const hasChildren = item.children && item.children.length > 0
  const isActive = currentPath === item.href || currentPath.startsWith(item.href + "/")
  const Icon = item.icon

  const handleClick = () => {
    if (hasChildren) {
      setIsOpen(!isOpen)
    }
  }

  return (
    <div>
      <div
        className={cn(
          "group relative flex items-center rounded-xl transition-all duration-200",
          level > 0 && "ml-4",
          collapsed ? "justify-center p-2" : "px-3 py-2"
        )}
      >
        {hasChildren ? (
          <button
            onClick={handleClick}
            className={cn(
              "flex items-center w-full text-left rounded-xl transition-all duration-200",
              "hover:bg-sidebar-hover",
              isActive && "bg-sidebar-active text-white font-medium",
              collapsed && "justify-center"
            )}
          >
            <SidebarItemContent
              item={item}
              collapsed={collapsed}
              isActive={isActive}
              Icon={Icon}
            />
          </button>
        ) : (
          <Link
            href={item.href}
            className={cn(
              "flex items-center w-full rounded-xl transition-all duration-200",
              "hover:bg-sidebar-hover",
              isActive && "bg-sidebar-active text-white font-medium",
              collapsed && "justify-center"
            )}
          >
            <SidebarItemContent
              item={item}
              collapsed={collapsed}
              isActive={isActive}
              Icon={Icon}
            />
          </Link>
        )}

        {/* Tooltip per versione collapsed */}
        {collapsed && (
          <div className="absolute left-full ml-2 px-2 py-1 bg-popover text-popover-foreground text-sm rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 whitespace-nowrap">
            {item.label}
          </div>
        )}
      </div>

      {/* Submenu */}
      {hasChildren && !collapsed && isOpen && (
        <div className="mt-1 space-y-1">
          {item.children?.map((childItem) => (
            <SidebarNavItem
              key={childItem.id}
              item={childItem}
              collapsed={collapsed}
              currentPath={currentPath}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// Componente per il contenuto dell'item
function SidebarItemContent({
  item,
  collapsed,
  isActive,
  Icon,
}: {
  item: SidebarItem
  collapsed: boolean
  isActive: boolean
  Icon?: React.ElementType
}) {
  return (
    <>
      {Icon && (
        <Icon className={cn("h-5 w-5 flex-shrink-0", !collapsed && "mr-3")} />
      )}
      {!collapsed && (
        <span className="flex-1 truncate">{item.label}</span>
      )}
      {!collapsed && item.badge && (
        <Badge variant={item.badge.variant} className="ml-auto">
          {item.badge.text}
        </Badge>
      )}
    </>
  )
}

// Mobile Sidebar Component
export function MobileSidebar({
  items,
  logo,
  className,
}: {
  items: SidebarItem[]
  logo?: React.ReactNode
  className?: string
}) {
  const [isOpen, setIsOpen] = React.useState(false)
  const pathname = usePathname()

  React.useEffect(() => {
    setIsOpen(false)
  }, [pathname])

  return (
    <>
      {/* Mobile Menu Button */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setIsOpen(true)}
        className="md:hidden"
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Mobile Sidebar Overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div 
            className="fixed inset-0 bg-background/80 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          />
          <div className={cn(
            "fixed left-0 top-0 h-full w-64 bg-sidebar-bg border-r border-border",
            className
          )}>
            <div className="flex items-center justify-between p-4 border-b border-border/50">
              {logo}
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsOpen(false)}
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
            <nav className="p-2 space-y-1">
              {items.map((item) => (
                <SidebarNavItem
                  key={item.id}
                  item={item}
                  collapsed={false}
                  currentPath={pathname}
                />
              ))}
            </nav>
          </div>
        </div>
      )}
    </>
  )
} 
'use client'

import { UserCog, Settings, Wrench, Thermometer, User } from 'lucide-react'
import { useUserRole, UserRole } from '@/hooks/useUserRole'
import { motion } from 'framer-motion'

interface RoleBadgeProps {
  className?: string
  showIcon?: boolean
  showLabel?: boolean
  onClick?: () => void
}

const roleConfig = {
  'ADMIN': {
    label: 'Amministratore',
    icon: Settings,
    bgColor: 'bg-red-100',
    textColor: 'text-red-700',
    borderColor: 'border-red-200'
  },
  'Management': {
    label: 'Responsabile',
    icon: UserCog,
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-700',
    borderColor: 'border-blue-200'
  },
  'Clean Room': {
    label: 'Laminatore',
    icon: Wrench,
    bgColor: 'bg-green-100',
    textColor: 'text-green-700',
    borderColor: 'border-green-200'
  },
  'Curing': {
    label: 'Autoclavista',
    icon: Thermometer,
    bgColor: 'bg-orange-100',
    textColor: 'text-orange-700',
    borderColor: 'border-orange-200'
  }
}

export function RoleBadge({ 
  className = '', 
  showIcon = true, 
  showLabel = true,
  onClick 
}: RoleBadgeProps) {
  const { role, isLoading } = useUserRole()

  // Se sta caricando o non c'è ruolo, non mostrare nulla
  if (isLoading || !role) {
    return null
  }

  const config = roleConfig[role as keyof typeof roleConfig]
  
  if (!config) {
    return (
      <div className={`inline-flex items-center px-3 py-1 rounded-full border bg-gray-100 text-gray-700 border-gray-200 ${className}`}>
        <User className="w-4 h-4 mr-2" />
        <span className="text-sm font-medium">Ruolo Sconosciuto</span>
      </div>
    )
  }

  const IconComponent = config.icon
  const isClickable = onClick !== undefined

  const badge = (
    <div className={`
      inline-flex items-center px-3 py-1 rounded-full border transition-all duration-200
      ${config.bgColor} ${config.textColor} ${config.borderColor}
      ${isClickable ? 'cursor-pointer hover:shadow-md hover:scale-105' : ''}
      ${className}
    `}>
      {showIcon && (
        <IconComponent className="w-4 h-4 mr-2" />
      )}
      {showLabel && (
        <span className="text-sm font-medium">
          {config.label}
        </span>
      )}
    </div>
  )

  if (isClickable) {
    return (
      <motion.div
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onClick}
      >
        {badge}
      </motion.div>
    )
  }

  return badge
}

// Componente per un badge minimal (solo icona)
export function RoleBadgeIcon({ className = '', onClick }: Omit<RoleBadgeProps, 'showIcon' | 'showLabel'>) {
  return (
    <RoleBadge 
      className={className}
      showIcon={true}
      showLabel={false}
      onClick={onClick}
    />
  )
}

// Componente per un badge completo con tooltip
export function RoleBadgeWithTooltip({ className = '', onClick }: Omit<RoleBadgeProps, 'showIcon' | 'showLabel'>) {
  const { role } = useUserRole()
  
  if (!role) return null
  
  const config = roleConfig[role as keyof typeof roleConfig]
  
  return (
    <div className="group relative">
      <RoleBadge 
        className={className}
        showIcon={true}
        showLabel={true}
        onClick={onClick}
      />
      
      {/* Tooltip */}
      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap">
        Ruolo attuale: {config?.label || role}
        <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-2 border-r-2 border-t-2 border-l-transparent border-r-transparent border-t-gray-900"></div>
      </div>
    </div>
  )
} 
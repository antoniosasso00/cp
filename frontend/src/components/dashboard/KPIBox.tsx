'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LucideIcon } from 'lucide-react'

interface KPIBoxProps {
  title: string
  value: string | number
  trend?: string
  status: 'success' | 'warning' | 'info' | 'error'
  icon: LucideIcon
  loading?: boolean
  description?: string
}

export function KPIBox({ 
  title, 
  value, 
  trend, 
  status, 
  icon: Icon, 
  loading = false,
  description 
}: KPIBoxProps) {
  const getStatusColor = (status: string) => {
    const colors = {
      success: 'text-green-600',
      warning: 'text-yellow-600',
      info: 'text-blue-600',
      error: 'text-red-600'
    }
    return colors[status as keyof typeof colors] || 'text-gray-600'
  }

  const getBadgeVariant = (status: string) => {
    const variants = {
      success: 'default',
      warning: 'secondary',
      info: 'outline',
      error: 'destructive'
    }
    return variants[status as keyof typeof variants] || 'outline'
  }

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={`h-4 w-4 ${getStatusColor(status)}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {loading ? (
            <div className="animate-pulse bg-gray-200 h-8 w-16 rounded"></div>
          ) : (
            value
          )}
        </div>
        {trend && (
          <p className={`text-xs mt-1 ${getStatusColor(status)}`}>
            {trend}
          </p>
        )}
        {description && (
          <p className="text-xs text-muted-foreground mt-1">
            {description}
          </p>
        )}
      </CardContent>
    </Card>
  )
} 
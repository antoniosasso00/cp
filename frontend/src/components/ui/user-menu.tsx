'use client'

import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { 
  User, 
  Settings, 
  RefreshCw, 
  LogOut,
  UserCog
} from 'lucide-react'
import { useUserRole, type UserRole } from '@/hooks/useUserRole'

interface UserMenuProps {
  className?: string
}

export function UserMenu({ className }: UserMenuProps) {
  const { role, clearRole } = useUserRole()
  const router = useRouter()

  const handleRoleChange = () => {
    clearRole()
    router.push('/select-role')
  }

  const handleLogout = () => {
    clearRole()
    router.push('/role')
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className={`relative h-10 w-10 rounded-full ${className}`}
        >
          <span className="sr-only">Menu utente</span>
          <User className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">Utente</p>
            {role && (
              <div className="flex items-center gap-2">
                <UserCog className="h-3 w-3 text-primary" />
                <p className="text-xs leading-none text-primary font-medium">
                  {role}
                </p>
              </div>
            )}
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        {/* Impostazioni - accessibile a tutti i ruoli */}
        <DropdownMenuItem asChild>
          <Link href="/dashboard/impostazioni" className="cursor-pointer">
            <Settings className="mr-2 h-4 w-4" />
            <span>Impostazioni</span>
          </Link>
        </DropdownMenuItem>
        
        <DropdownMenuSeparator />
        
        {/* Cambio ruolo - solo in sviluppo */}
        {process.env.NODE_ENV !== 'production' && (
          <DropdownMenuItem onClick={handleRoleChange} className="cursor-pointer">
            <RefreshCw className="mr-2 h-4 w-4" />
            <span>Cambia Ruolo</span>
          </DropdownMenuItem>
        )}
        
        {/* Logout */}
        <DropdownMenuItem onClick={handleLogout} className="cursor-pointer">
          <LogOut className="mr-2 h-4 w-4" />
          <span>Logout</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
} 
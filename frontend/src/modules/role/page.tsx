'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/shared/components/ui/button'
import { useUserRole } from '@/shared/hooks/useUserRole'
import type { UserRole } from '@/shared/types'
import { 
  Shield, 
  Users, 
  Wrench, 
  Flame
} from 'lucide-react'

// Definizione dei ruoli
const roles = [
  {
    id: 'ADMIN' as UserRole,
    title: 'Amministratore',
    icon: Shield,
    color: 'bg-slate-600 hover:bg-slate-700'
  },
  {
    id: 'Management' as UserRole,
    title: 'Management',
    icon: Users,
    color: 'bg-blue-600 hover:bg-blue-700'
  },
  {
    id: 'Clean Room' as UserRole,
    title: 'Clean Room',
    icon: Wrench,
    color: 'bg-green-600 hover:bg-green-700'
  },
  {
    id: 'Curing' as UserRole,
    title: 'Curing',
    icon: Flame,
    color: 'bg-orange-600 hover:bg-orange-700'
  }
]

export default function RolePage() {
  const router = useRouter()
  const { setRole } = useUserRole()

  const handleRoleSelect = async (selectedRole: UserRole) => {
    try {
      setRole(selectedRole)
      // Attendiamo un tick per assicurarci che localStorage sia aggiornato
      await new Promise(resolve => setTimeout(resolve, 100))
      router.replace('/dashboard')
    } catch (error) {
      console.error('Errore nella selezione del ruolo:', error)
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
      <div className="w-full max-w-md">
        
        {/* Header semplice */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary rounded-lg flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl font-bold text-white">MG</span>
          </div>
          <h1 className="text-2xl font-semibold text-gray-900 mb-2">
            Manta Group
          </h1>
          <p className="text-gray-600">
            Seleziona il tuo ruolo
          </p>
        </div>

        {/* Pulsanti ruoli */}
        <div className="space-y-3">
          {roles.map((role) => {
            const IconComponent = role.icon
            
            return (
              <Button
                key={role.id}
                onClick={() => handleRoleSelect(role.id)}
                className={`
                  w-full h-14 ${role.color} text-white
                  flex items-center justify-start px-6
                  transition-colors duration-200
                  text-left font-medium
                `}
                variant="default"
              >
                <IconComponent className="h-5 w-5 mr-3" />
                {role.title}
              </Button>
            )
          })}
        </div>
      </div>
    </main>
  )
} 
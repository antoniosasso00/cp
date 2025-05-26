'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useUserRole, type UserRole } from '@/hooks/useUserRole'
import { 
  Shield, 
  Users, 
  Wrench, 
  Flame,
  ArrowRight
} from 'lucide-react'

// Definizione dei ruoli con le loro caratteristiche
const roles = [
  {
    id: 'ADMIN' as UserRole,
    title: 'Amministratore',
    description: 'Accesso completo a tutte le funzionalità del sistema',
    icon: Shield,
    color: 'bg-red-500 hover:bg-red-600',
    permissions: [
      'Gestione completa del sistema',
      'Configurazione utenti e ruoli',
      'Accesso a tutti i moduli',
      'Gestione impostazioni avanzate'
    ]
  },
  {
    id: 'RESPONSABILE' as UserRole,
    title: 'Responsabile',
    description: 'Supervisione della produzione e gestione operativa',
    icon: Users,
    color: 'bg-blue-500 hover:bg-blue-600',
    permissions: [
      'Gestione ODL e produzione',
      'Supervisione operazioni',
      'Reports e statistiche',
      'Pianificazione attività'
    ]
  },
  {
    id: 'LAMINATORE' as UserRole,
    title: 'Laminatore',
    description: 'Operazioni di laminazione e gestione parti',
    icon: Wrench,
    color: 'bg-green-500 hover:bg-green-600',
    permissions: [
      'Gestione parti e catalogo',
      'Operazioni di laminazione',
      'Controllo qualità',
      'Registrazione attività'
    ]
  },
  {
    id: 'AUTOCLAVISTA' as UserRole,
    title: 'Autoclavista',
    description: 'Gestione autoclavi e cicli di cura',
    icon: Flame,
    color: 'bg-orange-500 hover:bg-orange-600',
    permissions: [
      'Gestione autoclavi',
      'Cicli di cura',
      'Nesting e scheduling',
      'Monitoraggio processi'
    ]
  }
]

export default function SelectRolePage() {
  const router = useRouter()
  const { setRole } = useUserRole()

  /**
   * Gestisce la selezione di un ruolo
   * Salva il ruolo e reindirizza alla dashboard
   */
  const handleRoleSelect = (selectedRole: UserRole) => {
    setRole(selectedRole)
    router.push('/dashboard')
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-6xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-6">
            <div className="bg-primary/10 rounded-full p-6 w-20 h-20 flex items-center justify-center">
              <span className="text-3xl font-bold text-primary">CP</span>
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Benvenuto in Manta Group
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Seleziona il tuo ruolo per accedere alle funzionalità appropriate del sistema
          </p>
        </div>

        {/* Grid dei ruoli */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {roles.map((role) => {
            const IconComponent = role.icon
            
            return (
              <Card 
                key={role.id}
                className="relative overflow-hidden hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 cursor-pointer group"
                onClick={() => handleRoleSelect(role.id)}
              >
                <CardHeader className="pb-4">
                  <div className={`w-12 h-12 rounded-lg ${role.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                    <IconComponent className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="text-xl font-bold text-gray-900 group-hover:text-primary transition-colors">
                    {role.title}
                  </CardTitle>
                  <CardDescription className="text-gray-600">
                    {role.description}
                  </CardDescription>
                </CardHeader>
                
                <CardContent className="pt-0">
                  <div className="space-y-2 mb-6">
                    {role.permissions.map((permission, index) => (
                      <div key={index} className="flex items-center text-sm text-gray-600">
                        <div className="w-1.5 h-1.5 bg-primary rounded-full mr-2 flex-shrink-0" />
                        {permission}
                      </div>
                    ))}
                  </div>
                  
                  <Button 
                    className={`w-full ${role.color} text-white border-0 group-hover:shadow-lg transition-all duration-300`}
                    onClick={(e) => {
                      e.stopPropagation()
                      handleRoleSelect(role.id)
                    }}
                  >
                    Seleziona Ruolo
                    <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform duration-300" />
                  </Button>
                </CardContent>
                
                {/* Effetto hover */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent to-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
              </Card>
            )
          })}
        </div>

        {/* Footer informativo */}
        <div className="text-center mt-12">
          <p className="text-sm text-gray-500">
            Il ruolo selezionato determinerà le funzionalità disponibili nell'interfaccia.
            <br />
            Potrai sempre cambiare ruolo dalle impostazioni del sistema.
          </p>
        </div>
      </div>
    </main>
  )
} 
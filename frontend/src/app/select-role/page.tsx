'use client'

import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { UserCog, Settings, Wrench, Thermometer } from 'lucide-react'
import { useUserRole, UserRole } from '@/hooks/useUserRole'

interface RoleCardProps {
  role: UserRole
  title: string
  description: string
  icon: React.ReactNode
  color: string
  delay: number
  onClick: () => void
}

const RoleCard = ({ role, title, description, icon, color, delay, onClick }: RoleCardProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      whileHover={{ 
        scale: 1.02, 
        y: -4,
        transition: { type: "spring", stiffness: 300, damping: 20 }
      }}
      whileTap={{ scale: 0.98 }}
      className="cursor-pointer"
      onClick={onClick}
    >
      <div className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 p-8 h-full border border-gray-200 hover:border-gray-300">
        <div className="flex flex-col items-center text-center space-y-4">
          {/* Icona con background colorato */}
          <div className={`${color} rounded-full p-6 w-20 h-20 flex items-center justify-center shadow-lg`}>
            <div className="text-white text-3xl">
              {icon}
            </div>
          </div>
          
          {/* Titolo */}
          <h3 className="text-2xl font-bold text-gray-800">
            {title}
          </h3>
          
          {/* Descrizione */}
          <p className="text-gray-600 leading-relaxed">
            {description}
          </p>
          
          {/* Badge ruolo */}
          <div className="mt-4 px-4 py-2 bg-gray-100 rounded-full">
            <span className="text-sm font-medium text-gray-700">
              {role}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default function SelectRolePage() {
  const router = useRouter()
  const { setRole } = useUserRole()

  const handleRoleSelect = (role: UserRole) => {
    // Salva il ruolo in localStorage
    setRole(role)
    
    // Redirect alla dashboard
    router.push('/dashboard')
  }

  const roles = [
    {
      role: 'ADMIN' as UserRole,
      title: 'Amministratore',
      description: 'Accesso completo a tutte le funzionalità del sistema, gestione utenti e configurazioni.',
      icon: <Settings />,
      color: 'bg-red-500',
      delay: 0
    },
    {
      role: 'Management' as UserRole,
      title: 'Responsabile',
      description: 'Supervisione della produzione, gestione ordini di lavoro e pianificazione.',
      icon: <UserCog />,
      color: 'bg-blue-500',
      delay: 0.1
    },
    {
      role: 'Clean Room' as UserRole,
      title: 'Laminatore',
      description: 'Gestione operazioni in camera bianca, laminazione e preparazione parti.',
      icon: <Wrench />,
      color: 'bg-green-500',
      delay: 0.2
    },
    {
      role: 'Curing' as UserRole,
      title: 'Autoclavista',
      description: 'Gestione autoclavi, cicli di cura e monitoraggio processi termici.',
      icon: <Thermometer />,
      color: 'bg-orange-500',
      delay: 0.3
    }
  ]

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <div className="flex justify-center mb-6">
            <div className="bg-primary/10 rounded-full p-8 w-32 h-32 flex items-center justify-center shadow-lg">
              <span className="text-6xl font-bold text-primary">CP</span>
            </div>
          </div>
          
          <h1 className="text-5xl font-bold text-gray-800 mb-4">
            Manta Group
          </h1>
          <h2 className="text-2xl font-semibold text-gray-600 mb-2">
            Selezione Ruolo
          </h2>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            Seleziona il tuo ruolo per accedere alle funzionalità appropriate del sistema di gestione compositi
          </p>
        </motion.div>

        {/* Grid dei ruoli */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
          {roles.map((roleData) => (
            <RoleCard
              key={roleData.role}
              role={roleData.role}
              title={roleData.title}
              description={roleData.description}
              icon={roleData.icon}
              color={roleData.color}
              delay={roleData.delay}
              onClick={() => handleRoleSelect(roleData.role)}
            />
          ))}
        </div>

        {/* Footer */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="text-center"
        >
          <p className="text-sm text-gray-400">
            CarbonPilot v1.4.2 &copy; {new Date().getFullYear()} - Sistema Gestione Compositi Manta Group
          </p>
        </motion.div>
      </div>
    </main>
  )
} 
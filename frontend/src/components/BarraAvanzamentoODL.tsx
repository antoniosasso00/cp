'use client'

import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, Activity, CheckCircle2 } from 'lucide-react'

// Configurazione delle fasi di produzione
export const FASI_PRODUZIONE = [
  { 
    nome: "Preparazione", 
    icona: "⚙️", 
    colore: "bg-gray-500", 
    coloreCompleto: "bg-gray-600",
    durata: 30,
    descrizione: "Preparazione materiali e setup"
  },
  { 
    nome: "Laminazione", 
    icona: "🔨", 
    colore: "bg-blue-500", 
    coloreCompleto: "bg-blue-600",
    durata: 120,
    descrizione: "Processo di laminazione"
  },
  { 
    nome: "In Coda", 
    icona: "⏳", 
    colore: "bg-orange-500", 
    coloreCompleto: "bg-orange-600",
    durata: 0,
    descrizione: "In attesa di tool disponibili"
  },
  { 
    nome: "Attesa Cura", 
    icona: "⏱️", 
    colore: "bg-yellow-500", 
    coloreCompleto: "bg-yellow-600",
    durata: 60,
    descrizione: "In attesa di autoclave"
  },
  { 
    nome: "Cura", 
    icona: "🔥", 
    colore: "bg-red-500", 
    coloreCompleto: "bg-red-600",
    durata: 180,
    descrizione: "Processo di cura in autoclave"
  },
  { 
    nome: "Finito", 
    icona: "✅", 
    colore: "bg-green-500", 
    coloreCompleto: "bg-green-600",
    durata: 0,
    descrizione: "Processo completato"
  }
]

// Funzione per calcolare la priorità
export const getPriorityInfo = (priorita: number) => {
  if (priorita >= 8) return { label: "Critica", color: "bg-red-500", emoji: "🔴" }
  if (priorita >= 5) return { label: "Alta", color: "bg-orange-500", emoji: "🟠" }
  if (priorita >= 3) return { label: "Media", color: "bg-yellow-500", emoji: "🟡" }
  return { label: "Bassa", color: "bg-green-500", emoji: "🟢" }
}

interface BarraAvanzamentoODLProps {
  status: string
  priorita: number
  motivo_blocco?: string | null
  variant?: 'default' | 'compact'
  showDescription?: boolean
}

export function BarraAvanzamentoODL({ 
  status, 
  priorita, 
  motivo_blocco, 
  variant = 'default',
  showDescription = true 
}: BarraAvanzamentoODLProps) {
  const currentIndex = FASI_PRODUZIONE.findIndex(fase => fase.nome === status)
  const totalDuration = FASI_PRODUZIONE.reduce((sum, fase) => sum + fase.durata, 0)
  
  let progressValue = 0
  for (let i = 0; i <= currentIndex; i++) {
    progressValue += FASI_PRODUZIONE[i].durata
  }
  const progressPercent = totalDuration > 0 ? (progressValue / totalDuration) * 100 : 0
  
  const priorityInfo = getPriorityInfo(priorita)
  const currentPhase = FASI_PRODUZIONE[currentIndex]
  
  if (variant === 'compact') {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-2">
            <span className="text-lg">{currentPhase?.icona}</span>
            <span className="font-medium">{status}</span>
            {status === "In Coda" && motivo_blocco && (
              <Badge variant="outline" className="text-xs bg-orange-50">
                <AlertTriangle className="w-3 h-3 mr-1" />
                {motivo_blocco}
              </Badge>
            )}
          </span>
          <div className="flex items-center gap-1">
            <span className="text-xs">{priorityInfo.emoji}</span>
            <Badge variant="outline" className="text-xs">
              P{priorita}
            </Badge>
          </div>
        </div>
        <Progress value={progressPercent} className="h-2" />
        <div className="flex justify-between text-xs text-muted-foreground">
          {FASI_PRODUZIONE.map((fase, index) => (
            <span 
              key={fase.nome}
              className={`${index <= currentIndex ? 'text-foreground font-medium' : ''}`}
            >
              {fase.icona}
            </span>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Header con stato e priorità */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl">{currentPhase?.icona}</span>
          <div>
            <span className="font-semibold text-lg">{status}</span>
            {showDescription && currentPhase?.descrizione && (
              <p className="text-sm text-muted-foreground">
                {currentPhase.descrizione}
              </p>
            )}
          </div>
          {status === "In Coda" && motivo_blocco && (
            <Badge variant="outline" className="bg-orange-50 border-orange-200">
              <AlertTriangle className="w-4 h-4 mr-1" />
              {motivo_blocco}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="flex items-center gap-1">
            <span>{priorityInfo.emoji}</span>
            <span>Priorità {priorita}</span>
          </Badge>
        </div>
      </div>

      {/* Etichette delle fasi */}
      <div className="flex justify-between text-xs font-medium">
        {FASI_PRODUZIONE.map((fase, index) => (
          <div 
            key={fase.nome} 
            className={`flex flex-col items-center ${
              index <= currentIndex ? 'text-gray-900' : 'text-gray-400'
            }`}
          >
            <span className="text-lg mb-1">{fase.icona}</span>
            <span className="text-center leading-tight">
              {fase.nome.split(' ').map((word, i) => (
                <span key={i} className="block">{word}</span>
              ))}
            </span>
          </div>
        ))}
      </div>
      
      {/* Barra di progresso segmentata */}
      <div className="flex h-4 bg-gray-200 rounded-full overflow-hidden">
        {FASI_PRODUZIONE.map((fase, index) => {
          const percentuale = totalDuration > 0 ? (fase.durata / totalDuration) * 100 : 100 / FASI_PRODUZIONE.length
          const isCompleted = index < currentIndex
          const isCurrent = index === currentIndex
          
          return (
            <div
              key={fase.nome}
              className={`
                ${isCompleted ? fase.coloreCompleto : (isCurrent ? fase.colore : 'bg-gray-200')}
                transition-all duration-300 border-r border-white last:border-r-0
              `}
              style={{ width: `${percentuale}%` }}
            />
          )
        })}
      </div>
      
      {/* Indicatore di completamento */}
      <div className="flex justify-between text-sm text-gray-600">
        <span>Inizio</span>
        <span className="flex items-center gap-1">
          {currentIndex === FASI_PRODUZIONE.length - 1 ? (
            <>
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              Completato
            </>
          ) : (
            <>
              <Activity className="h-4 w-4 text-blue-600" />
              In corso: {currentPhase?.nome}
            </>
          )}
        </span>
      </div>
    </div>
  )
} 
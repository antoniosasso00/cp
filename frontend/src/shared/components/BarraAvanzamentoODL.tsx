'use client'

import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, Activity, CheckCircle2, TrendingUp, TrendingDown } from 'lucide-react'

// Configurazione delle fasi di produzione con durate medie bilanciate
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
    durata: 60,
    descrizione: "In attesa di tool disponibili"
  },
  { 
    nome: "Attesa Cura", 
    icona: "⏱️", 
    colore: "bg-yellow-500", 
    coloreCompleto: "bg-yellow-600",
    durata: 240,
    descrizione: "In attesa di autoclave"
  },
  { 
    nome: "Cura", 
    icona: "🔥", 
    colore: "bg-red-500", 
    coloreCompleto: "bg-red-600",
    durata: 360,
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

// Costanti per il bilanciamento della visualizzazione
const MIN_SEGMENT_WIDTH = 10; // Percentuale minima per ogni segmento
const MAX_SEGMENT_WIDTH = 50; // Percentuale massima per evitare dominanza

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
  
  // Calcola proporzioni bilanciate per una migliore visualizzazione
  const calcolaProporzioniEque = () => {
    const fasiFinoCorrente = FASI_PRODUZIONE.slice(0, currentIndex + 1)
    const totaleDurataNormale = fasiFinoCorrente.reduce((sum, fase) => sum + fase.durata, 0)
    
    if (totaleDurataNormale === 0) {
      // Distribuzione equa se non ci sono durate
      const percentualeEguale = 100 / fasiFinoCorrente.length
      return fasiFinoCorrente.map(() => percentualeEguale)
    }
    
    // Calcola percentuali originali
    const percentualiOriginali = fasiFinoCorrente.map(fase => 
      (fase.durata / totaleDurataNormale) * 100
    )
    
    // Bilancia le proporzioni applicando limiti
    let percentualiTotali = 0
    const percentualiBilanciate = percentualiOriginali.map(perc => {
      let percentualeBilanciata = perc
      
      // Applica limiti minimi e massimi
      if (percentualeBilanciata < MIN_SEGMENT_WIDTH && fasiFinoCorrente.length > 1) {
        percentualeBilanciata = MIN_SEGMENT_WIDTH
      } else if (percentualeBilanciata > MAX_SEGMENT_WIDTH && fasiFinoCorrente.length > 1) {
        percentualeBilanciata = MAX_SEGMENT_WIDTH
      }
      
      percentualiTotali += percentualeBilanciata
      return percentualeBilanciata
    })
    
    // Riscala per mantenere il 100% totale
    if (percentualiTotali !== 100) {
      const fattoreScala = 100 / percentualiTotali
      return percentualiBilanciate.map(perc => perc * fattoreScala)
    }
    
    return percentualiBilanciate
  }
  
  const proporzioniEque = calcolaProporzioniEque()
  const progressPercent = proporzioniEque.reduce((sum, perc) => sum + perc, 0)
  
  const priorityInfo = getPriorityInfo(priorita)
  const currentPhase = FASI_PRODUZIONE[currentIndex]
  
  // Determina se ci sono scostamenti significativi nelle proporzioni
  const totaleDurataNormale = FASI_PRODUZIONE.slice(0, currentIndex + 1).reduce((sum, fase) => sum + fase.durata, 0)
  const hasProportionAdjustment = totaleDurataNormale > 0 && 
    proporzioniEque.some((perc, i) => {
      const originalPerc = (FASI_PRODUZIONE[i].durata / totaleDurataNormale) * 100
      return Math.abs(perc - originalPerc) > 5
    })
  
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
        
        {/* Barra di progresso bilanciata */}
        <div className="flex h-3 bg-gray-200 rounded-full overflow-hidden">
          {proporzioniEque.map((percentuale, index) => {
            const fase = FASI_PRODUZIONE[index]
            const isCompleted = index < currentIndex
            const isCurrent = index === currentIndex
            
            return (
              <div
                key={fase.nome}
                className={`
                  ${isCompleted ? fase.coloreCompleto : (isCurrent ? fase.colore : 'bg-gray-200')}
                  transition-all duration-300
                  ${hasProportionAdjustment ? 'border-r border-white last:border-r-0' : ''}
                `}
                style={{ width: `${percentuale}%` }}
                title={`${fase.nome}: ${fase.durata}min`}
              />
            )
          })}
        </div>
        
        <div className="flex justify-between text-xs text-muted-foreground">
          {FASI_PRODUZIONE.slice(0, currentIndex + 1).map((fase, index) => (
            <span 
              key={fase.nome}
              className={`${index <= currentIndex ? 'text-foreground font-medium' : ''}`}
              title={fase.descrizione}
            >
              {fase.icona}
            </span>
          ))}
        </div>
        
        {hasProportionAdjustment && (
          <div className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
            ⚖️ Proporzioni bilanciate per miglior leggibilità
          </div>
        )}
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

      {/* Etichette delle fasi con durate stimata */}
      <div className="flex justify-between text-xs font-medium">
        {FASI_PRODUZIONE.slice(0, currentIndex + 1).map((fase, index) => (
          <div 
            key={fase.nome} 
            className={`flex flex-col items-center ${
              index <= currentIndex ? 'text-gray-900' : 'text-gray-400'
            }`}
            title={`${fase.descrizione} (${fase.durata}min)`}
          >
            <span className="text-lg mb-1">{fase.icona}</span>
            <span className="text-center leading-tight">
              {fase.nome.split(' ').map((word, i) => (
                <span key={i} className="block">{word}</span>
              ))}
            </span>
            <span className="text-xs text-gray-400 mt-1">
              {fase.durata > 0 ? `${fase.durata}min` : ''}
            </span>
          </div>
        ))}
      </div>
      
      {/* Barra di progresso segmentata bilanciata */}
      <div className="flex h-4 bg-gray-200 rounded-full overflow-hidden">
        {proporzioniEque.map((percentuale, index) => {
          const fase = FASI_PRODUZIONE[index]
          const isCompleted = index < currentIndex
          const isCurrent = index === currentIndex
          const originalPerc = totaleDurataNormale > 0 ? (fase.durata / totaleDurataNormale) * 100 : 100 / (currentIndex + 1)
          const hasAdjustment = Math.abs(percentuale - originalPerc) > 5
          
          return (
            <div
              key={fase.nome}
              className={`
                ${isCompleted ? fase.coloreCompleto : (isCurrent ? fase.colore : 'bg-gray-200')}
                transition-all duration-300 border-r border-white last:border-r-0
                ${hasAdjustment ? 'ring-1 ring-yellow-300' : ''}
              `}
              style={{ width: `${percentuale}%` }}
              title={`${fase.nome}: ${fase.durata}min (${percentuale.toFixed(1)}% visualizzato${hasAdjustment ? `, ${originalPerc.toFixed(1)}% reale` : ''})`}
            />
          )
        })}
      </div>
      
      {/* Indicatore di completamento con informazioni bilanciate */}
      <div className="flex justify-between items-center text-sm text-gray-600">
        <span>Inizio</span>
        <div className="flex items-center gap-2">
          {currentIndex === FASI_PRODUZIONE.length - 1 ? (
            <>
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <span>Completato</span>
            </>
          ) : (
            <>
              <Activity className="h-4 w-4 text-blue-600" />
              <span>In corso: {currentPhase?.nome}</span>
            </>
          )}
          {hasProportionAdjustment && (
            <Badge variant="outline" className="text-xs text-amber-600">
              <TrendingUp className="h-3 w-3 mr-1" />
              Bilanciato
            </Badge>
          )}
        </div>
      </div>
      
      {/* Informazioni aggiuntive sul bilanciamento */}
      {hasProportionAdjustment && (
        <div className="flex items-center gap-2 text-xs text-amber-600 bg-amber-50 p-2 rounded">
          <TrendingUp className="h-4 w-4" />
          <span>
            Le proporzioni sono state bilanciate per migliorare la leggibilità della barra di avanzamento.
            Passa il mouse sui segmenti per vedere i valori reali.
          </span>
        </div>
      )}
    </div>
  )
} 
import { NextRequest, NextResponse } from 'next/server'

// 🔧 DICHIARAZIONE TIPO GLOBAL per job results
declare global {
  var jobResults: Map<string, any> | undefined
}

// 🔧 FIX TIMEOUT: Configurazione timeout esteso per algoritmi 2L
// Next.js richiede valori statici per maxDuration
export const maxDuration = 300 // 5 minuti - massimo supportato in development
export const dynamic = 'force-dynamic'

// 🚀 SOLUZIONE ROBUSTA: Streaming response per algoritmi lunghi
export async function POST(request: NextRequest) {
  try {
    console.log('🚀 API Route 2L-Multi: Inizio richiesta con timeout esteso e streaming')
    
    // Estrai il body della richiesta
    const body = await request.json()
    
    console.log('📋 2L-Multi Request:', {
      autoclavi_count: body.autoclavi_2l?.length || 0,
      odl_count: body.odl_ids?.length || 0,
      use_cavalletti: body.use_cavalletti,
      environment: process.env.NODE_ENV
    })
    
    // 🔧 TIMEOUT DINAMICO: Basato su ambiente e complessità (esteso per 45+ ODL)
    const isProduction = process.env.NODE_ENV === 'production'
    const baseTimeout = isProduction ? 600000 : 300000 // 10min prod, 5min dev
    
    // Calcola timeout dinamico basato su complessità
    const odlCount = body.odl_ids?.length || 0
    const autoclaveCount = body.autoclavi_2l?.length || 0
    const complexityMultiplier = Math.min(2.0, 1 + (odlCount / 20) + (autoclaveCount / 5))
    const dynamicTimeout = Math.min(baseTimeout * complexityMultiplier, baseTimeout)
    
    console.log(`⏱️ Timeout calcolato: ${dynamicTimeout/1000}s (base: ${baseTimeout/1000}s, complessità: ${complexityMultiplier.toFixed(2)}x)`)
    
    // 🚀 IMPLEMENTAZIONE STREAMING: Per algoritmi lunghi (soglia molto alta per evitare asincrono)
    if (odlCount > 100 || autoclaveCount > 10) {
      return handleLongRunningRequest(body, dynamicTimeout)
    }
    
    // 🔧 RICHIESTA STANDARD: Per algoritmi veloci
    return handleStandardRequest(body, dynamicTimeout)
    
  } catch (error: any) {
    console.error('❌ Errore parsing richiesta:', error)
    return NextResponse.json(
      { 
        error: 'Bad Request',
        detail: 'Errore nel parsing della richiesta',
        timestamp: new Date().toISOString()
      },
      { status: 400 }
    )
  }
}

// 🚀 GESTIONE RICHIESTE STANDARD (< 2 minuti)
async function handleStandardRequest(body: any, timeout: number) {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => {
    console.warn(`⚠️ Timeout standard dopo ${timeout/1000}s`)
    controller.abort()
  }, timeout)
  
  try {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'
    const response = await fetch(`${backendUrl}/batch_nesting/2l-multi`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      console.error(`❌ Backend error: ${response.status} ${response.statusText}`)
      const errorText = await response.text()
      return NextResponse.json(
        { 
          error: `Backend error: ${response.status}`,
          detail: errorText,
          timestamp: new Date().toISOString()
        },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    
    console.log('✅ 2L-Multi completato (standard):', {
      success: data.success,
      batch_count: data.batch_results?.length || 0,
      best_batch_id: data.best_batch_id
    })
    
    return NextResponse.json(data)
    
  } catch (error: any) {
    clearTimeout(timeoutId)
    
    if (error.name === 'AbortError') {
      console.error(`⏰ Timeout: Algoritmo 2L ha superato i ${timeout/1000}s`)
      return NextResponse.json(
        { 
          error: 'Timeout',
          detail: `L'algoritmo 2L ha superato i ${timeout/1000} secondi. Il dataset potrebbe essere troppo complesso.`,
          suggestion: 'Prova a ridurre il numero di ODL o usa la modalità asincrona per dataset grandi.',
          timestamp: new Date().toISOString(),
          timeout_seconds: timeout/1000
        },
        { status: 408 } // Request Timeout
      )
    }
    
    console.error('❌ Errore chiamata backend:', error)
    return NextResponse.json(
      { 
        error: 'Internal Server Error',
        detail: error.message || 'Errore sconosciuto',
        timestamp: new Date().toISOString()
      },
      { status: 500 }
    )
  }
}

// 🚀 GESTIONE RICHIESTE LUNGHE (> 2 minuti) - MODALITÀ ASINCRONA
async function handleLongRunningRequest(body: any, timeout: number) {
  console.log('🔄 Modalità asincrona attivata per dataset complesso')
  
  // 1. Avvia elaborazione asincrona
  const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  
  // 2. Avvia elaborazione in background (non aspetta la risposta)
  startBackgroundProcessing(body, jobId).catch(error => {
    console.error(`❌ Errore elaborazione background ${jobId}:`, error)
  })
  
  // 3. Restituisce immediatamente job ID per polling
  return NextResponse.json({
    success: true,
    mode: 'async',
    job_id: jobId,
    message: 'Elaborazione avviata in modalità asincrona per dataset complesso',
    estimated_duration_minutes: Math.ceil(timeout / 60000),
    polling_url: `/api/batch_nesting/status/${jobId}`,
    timestamp: new Date().toISOString()
  })
}

// 🔄 ELABORAZIONE BACKGROUND ASINCRONA
async function startBackgroundProcessing(body: any, jobId: string) {
  console.log(`🚀 Avvio elaborazione background: ${jobId}`)
  
  try {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'
    
    // Timeout esteso per elaborazione background (15 minuti)
    const backgroundTimeout = 900000 // 15 minuti
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), backgroundTimeout)
    
    const response = await fetch(`${backendUrl}/batch_nesting/2l-multi`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Job-ID': jobId, // Header per tracking
      },
      body: JSON.stringify(body),
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    
    if (response.ok) {
      const data = await response.json()
      console.log(`✅ Elaborazione background completata: ${jobId}`)
      
      // Salva risultato in cache/database per polling
      await saveJobResult(jobId, {
        success: true,
        data: data,
        completed_at: new Date().toISOString()
      })
    } else {
      console.error(`❌ Errore elaborazione background ${jobId}: ${response.status}`)
      await saveJobResult(jobId, {
        success: false,
        error: `Backend error: ${response.status}`,
        completed_at: new Date().toISOString()
      })
    }
    
  } catch (error: any) {
    console.error(`❌ Errore elaborazione background ${jobId}:`, error)
    await saveJobResult(jobId, {
      success: false,
      error: error.message || 'Errore sconosciuto',
      completed_at: new Date().toISOString()
    })
  }
}

// 💾 SALVATAGGIO RISULTATI JOB (implementazione semplificata)
async function saveJobResult(jobId: string, result: any) {
  // In una implementazione reale, salveresti in Redis/Database
  // Per ora, salviamo in memoria (limitato ma funzionale per demo)
  if (typeof global !== 'undefined') {
    if (!global.jobResults) {
      global.jobResults = new Map()
    }
    global.jobResults.set(jobId, result)
    
    // Cleanup automatico dopo 1 ora
    setTimeout(() => {
      global.jobResults?.delete(jobId)
    }, 3600000)
  }
} 
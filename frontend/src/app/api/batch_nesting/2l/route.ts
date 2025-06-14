import { NextRequest, NextResponse } from 'next/server'

// 🔧 FIX TIMEOUT: Configurazione timeout esteso per algoritmi 2L
export const maxDuration = 300 // 5 minuti (300 secondi) per 2L singolo
export const dynamic = 'force-dynamic'

export async function POST(request: NextRequest) {
  try {
    console.log('🚀 API Route 2L-Single: Inizio richiesta con timeout esteso')
    
    // Estrai il body della richiesta
    const body = await request.json()
    
    console.log('📋 2L-Single Request:', {
      autoclave_id: body.autoclave_id,
      odl_count: body.odl_ids?.length || 0,
      use_cavalletti: body.use_cavalletti
    })
    
    // 🔧 TIMEOUT ESTESO: 5 minuti per algoritmi 2L singoli
    const BACKEND_TIMEOUT = 300000 // 5 minuti
    
    // Crea AbortController per gestire timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => {
      console.warn('⚠️ Timeout backend dopo 5 minuti')
      controller.abort()
    }, BACKEND_TIMEOUT)
    
    try {
      // Chiama il backend con timeout esteso
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'
      const response = await fetch(`${backendUrl}/batch_nesting/2l`, {
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
      
      console.log('✅ 2L-Single completato:', {
        success: data.success,
        batch_id: data.batch_id,
        efficiency: data.metrics?.efficiency_score || 0
      })
      
      return NextResponse.json(data)
      
    } catch (error: any) {
      clearTimeout(timeoutId)
      
      if (error.name === 'AbortError') {
        console.error('⏰ Timeout: Algoritmo 2L ha superato i 5 minuti')
        return NextResponse.json(
          { 
            error: 'Timeout',
            detail: 'L\'algoritmo 2L ha superato i 5 minuti. Il dataset potrebbe essere troppo complesso.',
            suggestion: 'Prova a ridurre il numero di ODL o contatta il supporto tecnico.',
            timestamp: new Date().toISOString()
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
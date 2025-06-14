import { NextRequest, NextResponse } from 'next/server'

// 🔧 DICHIARAZIONE TIPO GLOBAL per job results
declare global {
  var jobResults: Map<string, any> | undefined
}

export const dynamic = 'force-dynamic'

export async function GET(
  request: NextRequest,
  { params }: { params: { jobId: string } }
) {
  try {
    const { jobId } = params
    
    console.log(`🔍 Polling status per job: ${jobId}`)
    
    // Verifica se abbiamo risultati per questo job
    if (typeof global !== 'undefined' && global.jobResults) {
      const result = global.jobResults.get(jobId)
      
      if (result) {
        console.log(`✅ Job ${jobId} completato`)
        
        // Rimuovi il job dalla cache dopo averlo restituito
        global.jobResults.delete(jobId)
        
        return NextResponse.json({
          status: 'completed',
          job_id: jobId,
          result: result,
          timestamp: new Date().toISOString()
        })
      }
    }
    
    // Job ancora in elaborazione
    console.log(`⏳ Job ${jobId} ancora in elaborazione`)
    
    return NextResponse.json({
      status: 'processing',
      job_id: jobId,
      message: 'Elaborazione in corso...',
      timestamp: new Date().toISOString()
    })
    
  } catch (error: any) {
    console.error('❌ Errore polling status:', error)
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
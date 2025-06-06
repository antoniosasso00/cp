import Link from 'next/link'
import { Button } from '@/shared/components/ui/button'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gradient-to-b from-gray-50 to-gray-100">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm flex">
        <div className="bg-white shadow-xl rounded-xl p-8 w-full max-w-2xl">
          <div className="flex justify-center mb-6">
            <div className="bg-primary/10 rounded-full p-6 w-24 h-24 flex items-center justify-center">
              <span className="text-4xl font-bold text-primary">CP</span>
            </div>
          </div>
          
          <h1 className="text-4xl font-bold text-center mb-6 text-gray-800">Manta Group</h1>
          <p className="text-lg text-center mb-10 text-gray-600">
            Sistema di gestione della produzione di parti in composito
          </p>
          
          <div className="space-y-4">
            <div className="flex flex-col space-y-2">
              <Link href="/modules/role" className="w-full">
                <Button className="w-full text-lg py-6">
                  Accedi al Sistema
                </Button>
              </Link>
            </div>
            
            <p className="text-center text-sm text-gray-500 mt-8">
              Manta Group v0.4.0 &copy; {new Date().getFullYear()} - Sistema Gestione Compositi
            </p>
          </div>
        </div>
      </div>
    </main>
  )
} 
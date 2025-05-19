import Link from "next/link"

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">
          <code className="font-mono font-bold">CarbonPilot v0.1.0</code>
        </p>
        <div className="fixed bottom-0 left-0 flex h-48 w-full items-end justify-center bg-gradient-to-t from-white via-white dark:from-black dark:via-black lg:static lg:h-auto lg:w-auto lg:bg-none">
          <a
            className="pointer-events-none flex place-items-center gap-2 p-8 lg:pointer-events-auto lg:p-0"
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
          >
            Sviluppato con Next.js
          </a>
        </div>
      </div>

      <div className="flex justify-center items-center flex-col my-24">
        <h1 className="text-4xl font-bold text-center mb-8">
          Benvenuto in{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-500 to-blue-600">
            CarbonPilot
          </span>
        </h1>
        <p className="text-xl text-center max-w-2xl mb-12">
          Una piattaforma per ottimizzare i processi e ridurre l'impatto ambientale
        </p>
        <div className="flex gap-4">
          <Link 
            href="/dashboard" 
            className="px-5 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            Inizia
          </Link>
          <Link 
            href="/about" 
            className="px-5 py-3 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/90 transition-colors"
          >
            Scopri di più
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-5xl">
        <div className="p-6 bg-card text-card-foreground rounded-lg shadow-sm">
          <h2 className="text-xl font-semibold mb-3">Ottimizzazione Avanzata</h2>
          <p>Algoritmi di nesting e ottimizzazione per ridurre gli sprechi e massimizzare l'efficienza.</p>
        </div>
        <div className="p-6 bg-card text-card-foreground rounded-lg shadow-sm">
          <h2 className="text-xl font-semibold mb-3">Monitoraggio Impatto</h2>
          <p>Analisi in tempo reale dell'impatto ambientale delle tue operazioni industriali.</p>
        </div>
        <div className="p-6 bg-card text-card-foreground rounded-lg shadow-sm">
          <h2 className="text-xl font-semibold mb-3">Reportistica Dettagliata</h2>
          <p>Report dettagliati e dashboard intuitive per tenere sotto controllo ogni aspetto.</p>
        </div>
      </div>
    </main>
  )
} 
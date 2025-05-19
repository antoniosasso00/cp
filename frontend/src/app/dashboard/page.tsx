import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Benvenuto nel sistema di gestione CarbonPilot
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6 flex flex-col space-y-2">
            <h3 className="text-2xl font-bold tracking-tight">Catalogo</h3>
            <p className="text-sm text-muted-foreground">
              Gestisci il catalogo dei part number
            </p>
            <div className="mt-4">
              <Link href="/dashboard/catalog">
                <Button>Vai al Catalogo</Button>
              </Link>
            </div>
          </div>
        </div>

        <div className="rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6 flex flex-col space-y-2">
            <h3 className="text-2xl font-bold tracking-tight">Parti</h3>
            <p className="text-sm text-muted-foreground">
              Gestisci le parti in produzione
            </p>
            <div className="mt-4">
              <Link href="/dashboard/parts">
                <Button>Vai alle Parti</Button>
              </Link>
            </div>
          </div>
        </div>

        <div className="rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6 flex flex-col space-y-2">
            <h3 className="text-2xl font-bold tracking-tight">Cicli Cura</h3>
            <p className="text-sm text-muted-foreground">
              Gestisci i cicli di cura
            </p>
            <div className="mt-4">
              <Link href="/dashboard/cicli-cura">
                <Button>Vai ai Cicli</Button>
              </Link>
            </div>
          </div>
        </div>

        <div className="rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6 flex flex-col space-y-2">
            <h3 className="text-2xl font-bold tracking-tight">Tools/Stampi</h3>
            <p className="text-sm text-muted-foreground">
              Gestisci gli stampi di produzione
            </p>
            <div className="mt-4">
              <Link href="/dashboard/tools">
                <Button>Vai agli Stampi</Button>
              </Link>
            </div>
          </div>
        </div>

        <div className="rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6 flex flex-col space-y-2">
            <h3 className="text-2xl font-bold tracking-tight">Autoclavi</h3>
            <p className="text-sm text-muted-foreground">
              Gestisci le autoclavi
            </p>
            <div className="mt-4">
              <Link href="/dashboard/autoclavi">
                <Button>Vai alle Autoclavi</Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 
'use client'

import React, { useState } from 'react'
import { ThemeSelector } from '@/shared/components/ui/theme-toggle'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/card'
import { Separator } from '@/shared/components/ui/separator'
import { Button } from '@/shared/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/shared/components/ui/dialog'
import { Alert, AlertDescription } from '@/shared/components/ui/alert'
import { Input } from '@/shared/components/ui/input'
import { Label } from '@/shared/components/ui/label'
import { useToast } from '@/shared/components/ui/use-toast'
import { Settings, Palette, Database, Zap, Download, Upload, Trash2, AlertTriangle, Info } from 'lucide-react'

export default function ImpostazioniPage() {
  const [isExporting, setIsExporting] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [isResetting, setIsResetting] = useState(false)
  const [resetConfirmation, setResetConfirmation] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [showResetDialog, setShowResetDialog] = useState(false)
  const [showImportDialog, setShowImportDialog] = useState(false)
  const [dbInfo, setDbInfo] = useState<any>(null)
  const [loadingInfo, setLoadingInfo] = useState(false)
  
  const { toast } = useToast()

  // Funzione per esportare il database
  const handleExportDatabase = async () => {
    setIsExporting(true)
    try {
      const response = await fetch('/api/admin/backup', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Errore HTTP: ${response.status}`)
      }

      // Ottieni il nome del file dall'header Content-Disposition
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = 'carbonpilot_backup.json'
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
        if (filenameMatch) {
          filename = filenameMatch[1]
        }
      }

      // Scarica il file
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast({
        title: "✅ Export completato",
        description: `Database esportato con successo come ${filename}`,
      })
    } catch (error) {
      console.error('Errore durante l\'export:', error)
      toast({
        title: "❌ Errore Export",
        description: `Errore durante l'esportazione del database: ${error instanceof Error ? error.message : 'Errore sconosciuto'}`,
        variant: "destructive",
      })
    } finally {
      setIsExporting(false)
    }
  }

  // Funzione per importare il database
  const handleImportDatabase = async () => {
    if (!selectedFile) {
      toast({
        title: "⚠️ Nessun file selezionato",
        description: "Seleziona un file di backup prima di procedere",
        variant: "destructive",
      })
      return
    }

    setIsImporting(true)
    try {
      const formData = new FormData()
      formData.append('backup_file', selectedFile)

      const response = await fetch('/api/admin/restore', {
        method: 'POST',
        body: formData,
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.detail || `Errore HTTP: ${response.status}`)
      }

      toast({
        title: "✅ Import completato",
        description: `Database ripristinato con successo. Tabelle ripristinate: ${result.restored_tables?.length || 0}`,
      })
      
      setShowImportDialog(false)
      setSelectedFile(null)
      
      // Aggiorna le informazioni del database
      loadDatabaseInfo()
      
    } catch (error) {
      console.error('Errore durante l\'import:', error)
      toast({
        title: "❌ Errore Import",
        description: `Errore durante l'importazione del database: ${error instanceof Error ? error.message : 'Errore sconosciuto'}`,
        variant: "destructive",
      })
    } finally {
      setIsImporting(false)
    }
  }

  // Funzione per resettare il database
  const handleResetDatabase = async () => {
    if (resetConfirmation !== 'reset') {
      toast({
        title: "⚠️ Conferma non valida",
        description: "Digita 'reset' per confermare l'operazione",
        variant: "destructive",
      })
      return
    }

    setIsResetting(true)
    try {
      const response = await fetch('/api/admin/database/reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          confirmation: resetConfirmation
        }),
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.detail || `Errore HTTP: ${response.status}`)
      }

      toast({
        title: "✅ Reset completato",
        description: `Database svuotato con successo. Tabelle resettate: ${result.total_tables_reset}, Record eliminati: ${result.total_deleted_records}`,
      })
      
      setShowResetDialog(false)
      setResetConfirmation('')
      
      // Aggiorna le informazioni del database
      loadDatabaseInfo()
      
    } catch (error) {
      console.error('Errore durante il reset:', error)
      toast({
        title: "❌ Errore Reset",
        description: `Errore durante il reset del database: ${error instanceof Error ? error.message : 'Errore sconosciuto'}`,
        variant: "destructive",
      })
    } finally {
      setIsResetting(false)
    }
  }

  // Funzione per caricare informazioni del database
  const loadDatabaseInfo = async () => {
    setLoadingInfo(true)
    try {
      const response = await fetch('/api/admin/database/info')
      if (response.ok) {
        const info = await response.json()
        setDbInfo(info)
      }
    } catch (error) {
      console.error('Errore nel caricamento info database:', error)
    } finally {
      setLoadingInfo(false)
    }
  }

  // Carica le informazioni del database al mount del componente
  React.useEffect(() => {
    loadDatabaseInfo()
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Settings className="h-8 w-8" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Impostazioni</h1>
          <p className="text-muted-foreground">
            Configura le preferenze dell'applicazione Manta Group
          </p>
        </div>
      </div>

      <div className="grid gap-6">
        {/* Sezione Tema */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="h-5 w-5" />
              Aspetto e Tema
            </CardTitle>
            <CardDescription>
              Personalizza l'aspetto dell'interfaccia utente
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="text-sm font-medium mb-3">Modalità del tema</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Scegli il tema dell'interfaccia. La modalità "Sistema" seguirà le preferenze del tuo dispositivo.
              </p>
              <ThemeSelector />
            </div>
          </CardContent>
        </Card>

        {/* Sezione Database */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Database
            </CardTitle>
            <CardDescription>
              Informazioni sulla configurazione del database
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Tipo database:</span>
                <span className="text-sm text-muted-foreground">SQLite (Sviluppo)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Stato connessione:</span>
                <span className="text-sm text-green-600 font-medium">🟢 Connesso</span>
              </div>
              {dbInfo && (
                <>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Tabelle totali:</span>
                    <span className="text-sm text-muted-foreground">{dbInfo.total_tables}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Record totali:</span>
                    <span className="text-sm text-muted-foreground">{dbInfo.total_records}</span>
                  </div>
                </>
              )}
              <Separator />
              <p className="text-xs text-muted-foreground">
                💡 Il database è attualmente configurato per SQLite in modalità sviluppo. 
                Per passare a PostgreSQL in produzione, modifica il flag nel file di configurazione backend.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Sezione Gestione Database */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Gestione Database
            </CardTitle>
            <CardDescription>
              Operazioni di backup, ripristino e reset del database
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                <strong>Importante:</strong> Queste operazioni influenzano tutti i dati del sistema. 
                Assicurati di avere un backup aggiornato prima di procedere con operazioni di ripristino o reset.
              </AlertDescription>
            </Alert>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Export Database */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Export Database</h4>
                <p className="text-xs text-muted-foreground">
                  Scarica un backup completo del database in formato JSON
                </p>
                <Button 
                  onClick={handleExportDatabase}
                  disabled={isExporting}
                  className="w-full"
                  variant="outline"
                >
                  <Download className="h-4 w-4 mr-2" />
                  {isExporting ? 'Esportando...' : 'Esporta Database'}
                </Button>
              </div>

              {/* Import Database */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Import Database</h4>
                <p className="text-xs text-muted-foreground">
                  Ripristina il database da un file di backup JSON
                </p>
                <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
                  <DialogTrigger asChild>
                    <Button className="w-full" variant="outline">
                      <Upload className="h-4 w-4 mr-2" />
                      Importa Database
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Importa Database</DialogTitle>
                      <DialogDescription>
                        Seleziona un file di backup JSON per ripristinare il database. 
                        <strong>Attenzione:</strong> Questa operazione sovrascriverà tutti i dati esistenti.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="backup-file">File di Backup</Label>
                        <Input
                          id="backup-file"
                          type="file"
                          accept=".json"
                          onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                        />
                      </div>
                      {selectedFile && (
                        <Alert>
                          <Info className="h-4 w-4" />
                          <AlertDescription>
                            File selezionato: <strong>{selectedFile.name}</strong> ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setShowImportDialog(false)}>
                        Annulla
                      </Button>
                      <Button 
                        onClick={handleImportDatabase}
                        disabled={isImporting || !selectedFile}
                      >
                        {isImporting ? 'Importando...' : 'Importa'}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>

              {/* Reset Database */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Reset Database</h4>
                <p className="text-xs text-muted-foreground">
                  Svuota completamente il database eliminando tutti i dati
                </p>
                <Dialog open={showResetDialog} onOpenChange={setShowResetDialog}>
                  <DialogTrigger asChild>
                    <Button className="w-full" variant="destructive">
                      <Trash2 className="h-4 w-4 mr-2" />
                      Reset Database
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Reset Database</DialogTitle>
                      <DialogDescription>
                        <strong>ATTENZIONE:</strong> Questa operazione eliminerà TUTTI i dati dal database in modo permanente. 
                        Questa azione non può essere annullata.
                      </DialogDescription>
                    </DialogHeader>
                    <Alert variant="destructive">
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        Tutti gli ODL, autoclavi, parti, tool, cicli di cura e dati storici verranno eliminati definitivamente.
                      </AlertDescription>
                    </Alert>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="reset-confirmation">
                          Digita "reset" per confermare l'operazione
                        </Label>
                        <Input
                          id="reset-confirmation"
                          type="text"
                          placeholder="reset"
                          value={resetConfirmation}
                          onChange={(e) => setResetConfirmation(e.target.value)}
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => {
                        setShowResetDialog(false)
                        setResetConfirmation('')
                      }}>
                        Annulla
                      </Button>
                      <Button 
                        variant="destructive"
                        onClick={handleResetDatabase}
                        disabled={isResetting || resetConfirmation !== 'reset'}
                      >
                        {isResetting ? 'Resettando...' : 'Conferma Reset'}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Sezione Performance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Prestazioni e Aggiornamenti
            </CardTitle>
            <CardDescription>
              Configurazioni relative alla velocità e al refresh dell'applicazione
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Aggiornamento automatico:</span>
                <span className="text-sm text-green-600 font-medium">🟢 Attivo</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Refresh cache:</span>
                <span className="text-sm text-muted-foreground">5 secondi</span>
              </div>
              <Separator />
              <p className="text-xs text-muted-foreground">
                📈 Gli ODL e Tool vengono aggiornati automaticamente per mantenere i dati sincronizzati tra le fasi di produzione.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 
'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { CicloModal } from './components/ciclo-modal'
import { curingCyclesApi, type CicloCura } from '@/lib/api'
import { 
  Loader2, 
  MoreHorizontal, 
  Pencil, 
  Trash2 
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export default function CicliCuraPage() {
  const [cicli, setCicli] = useState<CicloCura[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<CicloCura | null>(null)
  const { toast } = useToast()

  const loadData = async () => {
    try {
      setIsLoading(true)
      const data = await curingCyclesApi.fetchCuringCycles()
      setCicli(data)
    } catch (error) {
      console.error('Errore nel caricamento dei cicli di cura:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare i cicli di cura.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleCreateClick = () => {
    setEditingItem(null)
    setModalOpen(true)
  }

  const handleEditClick = (item: CicloCura) => {
    setEditingItem(item)
    setModalOpen(true)
  }

  const handleDeleteClick = async (id: number) => {
    if (!window.confirm('Sei sicuro di voler eliminare questo ciclo di cura?')) {
      return
    }

    try {
      await curingCyclesApi.deleteCuringCycle(id)
      toast({
        title: 'Eliminato',
        description: 'Ciclo di cura eliminato con successo.',
      })
      loadData()
    } catch (error) {
      console.error('Errore durante l\'eliminazione del ciclo di cura:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile eliminare il ciclo di cura.',
      })
    }
  }

  const filteredCicli = cicli.filter(item => {
    const searchLower = searchQuery.toLowerCase()
    return item.nome.toLowerCase().includes(searchLower)
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Cicli di Cura</h1>
          <p className="text-muted-foreground">
            Gestisci i cicli di cura disponibili
          </p>
        </div>
        <Button onClick={handleCreateClick}>Nuovo Ciclo</Button>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <Input
          placeholder="Cerca nei cicli..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Caricamento in corso...</span>
        </div>
      ) : (
        <Table>
          <TableCaption>Lista dei cicli di cura disponibili</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Nome</TableHead>
              <TableHead className="text-center">Stasi 1</TableHead>
              <TableHead className="text-center">Stasi 2</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredCicli.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  Nessun ciclo trovato
                </TableCell>
              </TableRow>
            ) : (
              filteredCicli.map(item => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.nome}</TableCell>
                  <TableCell className="text-center">
                    {item.temperatura_stasi1}°C / {item.pressione_stasi1} bar / {item.durata_stasi1} min
                  </TableCell>
                  <TableCell className="text-center">
                    {item.attiva_stasi2 ? (
                      <>
                        {item.temperatura_stasi2}°C / {item.pressione_stasi2} bar / {item.durata_stasi2} min
                        <Badge variant="secondary" className="ml-2">Attiva</Badge>
                      </>
                    ) : (
                      <Badge variant="outline">Disattiva</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleEditClick(item)}>
                          <Pencil className="mr-2 h-4 w-4" />
                          <span>Modifica</span>
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => handleDeleteClick(item.id)}
                          className="text-destructive focus:text-destructive"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          <span>Elimina</span>
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      )}

      <CicloModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        editingItem={editingItem}
        onSuccess={loadData}
      />
    </div>
  )
} 
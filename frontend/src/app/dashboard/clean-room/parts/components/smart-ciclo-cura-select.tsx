'use client'

import { useState, useEffect, useMemo } from 'react'
import { useDebounce } from '@/hooks/useDebounce'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { CicloCura } from '@/lib/api'
import { Plus, Search } from 'lucide-react'

interface SmartCicloCuraSelectProps {
  cicliCura: CicloCura[]
  selectedId: number | null
  onSelect: (id: number | null) => void
  onCreateNew: () => void
  isLoading?: boolean
  error?: string
}

// Funzione per evidenziare il testo che corrisponde alla ricerca
const highlightMatch = (text: string, searchTerm: string) => {
  if (!searchTerm) return text
  
  const regex = new RegExp(`(${searchTerm})`, 'gi')
  const parts = text.split(regex)
  
  return parts.map((part, index) => 
    regex.test(part) ? (
      <mark key={index} className="bg-yellow-200 text-yellow-900 px-1 rounded">
        {part}
      </mark>
    ) : part
  )
}

export default function SmartCicloCuraSelect({ 
  cicliCura, 
  selectedId, 
  onSelect, 
  onCreateNew, 
  isLoading = false,
  error 
}: SmartCicloCuraSelectProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const debouncedSearchTerm = useDebounce(searchTerm, 300)

  // Filtra i cicli di cura in base al termine di ricerca
  const filteredCicli = useMemo(() => {
    if (!debouncedSearchTerm) return cicliCura
    
    return cicliCura.filter(ciclo =>
      ciclo.nome.toLowerCase().includes(debouncedSearchTerm.toLowerCase())
    )
  }, [cicliCura, debouncedSearchTerm])

  // Trova il ciclo selezionato
  const selectedCiclo = cicliCura.find(ciclo => ciclo.id === selectedId)

  const handleSelect = (ciclo: CicloCura | null) => {
    onSelect(ciclo?.id || null)
    setSearchTerm('')
    setIsOpen(false)
  }

  const handleInputFocus = () => {
    setIsOpen(true)
    if (selectedCiclo) {
      setSearchTerm(selectedCiclo.nome)
    }
  }

  const handleInputBlur = () => {
    // Ritarda la chiusura per permettere il click sulle opzioni
    setTimeout(() => {
      setIsOpen(false)
      if (selectedCiclo && !searchTerm) {
        setSearchTerm('')
      }
    }, 200)
  }

  return (
    <div className="grid grid-cols-4 items-center gap-4">
      <Label htmlFor="ciclo_cura_search" className="text-right">
        Ciclo di Cura
      </Label>
      <div className="col-span-3 relative">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              id="ciclo_cura_search"
              value={isOpen ? searchTerm : (selectedCiclo?.nome || '')}
              onChange={e => setSearchTerm(e.target.value)}
              onFocus={handleInputFocus}
              onBlur={handleInputBlur}
              placeholder="Cerca ciclo di cura..."
              className="pl-10"
              disabled={isLoading}
            />
            
            {/* Dropdown con risultati */}
            {isOpen && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
                {/* Opzione "Nessun ciclo" */}
                <div
                  className="px-3 py-2 hover:bg-gray-100 cursor-pointer border-b"
                  onClick={() => handleSelect(null)}
                >
                  <span className="text-gray-500 italic">Nessun ciclo di cura</span>
                </div>
                
                {/* Risultati filtrati */}
                {filteredCicli.length > 0 ? (
                  filteredCicli.map(ciclo => (
                    <div
                      key={ciclo.id}
                      className={`px-3 py-2 hover:bg-gray-100 cursor-pointer ${
                        selectedId === ciclo.id ? 'bg-blue-50' : ''
                      }`}
                      onClick={() => handleSelect(ciclo)}
                    >
                      <div className="font-medium">
                        {highlightMatch(ciclo.nome, debouncedSearchTerm)}
                      </div>
                      <div className="text-sm text-gray-500">
                        {ciclo.temperatura_stasi1}°C, {ciclo.pressione_stasi1} bar, {ciclo.durata_stasi1} min
                        {ciclo.attiva_stasi2 && ` + Stasi 2`}
                      </div>
                    </div>
                  ))
                ) : debouncedSearchTerm ? (
                  <div className="px-3 py-2 text-gray-500 italic">
                    Nessun risultato per "{debouncedSearchTerm}"
                  </div>
                ) : (
                  <div className="px-3 py-2 text-gray-500 italic">
                    Digita per cercare...
                  </div>
                )}
              </div>
            )}
          </div>
          
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onCreateNew}
            disabled={isLoading}
            className="flex items-center gap-1"
          >
            <Plus className="h-4 w-4" />
            Nuovo Ciclo
          </Button>
        </div>
        
        {error && (
          <p className="text-sm text-destructive mt-1">{error}</p>
        )}
      </div>
    </div>
  )
} 
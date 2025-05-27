'use client'

import { useState, useMemo } from 'react'
import { useDebounce } from '@/hooks/useDebounce'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { CatalogoResponse } from '@/lib/api'
import { Search } from 'lucide-react'

interface SmartCatalogoSelectProps {
  catalogo: CatalogoResponse[]
  selectedPartNumber: string
  onSelect: (partNumber: string) => void
  onItemSelect?: (item: CatalogoResponse) => void
  isLoading?: boolean
  error?: string
  disabled?: boolean
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

export default function SmartCatalogoSelect({ 
  catalogo, 
  selectedPartNumber, 
  onSelect, 
  onItemSelect,
  isLoading = false,
  error,
  disabled = false
}: SmartCatalogoSelectProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const debouncedSearchTerm = useDebounce(searchTerm, 300)

  // Filtra il catalogo in base al termine di ricerca
  const filteredCatalogo = useMemo(() => {
    if (!debouncedSearchTerm) return catalogo
    
    return catalogo.filter(item =>
      item.part_number.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
      item.descrizione.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
      (item.categoria && item.categoria.toLowerCase().includes(debouncedSearchTerm.toLowerCase())) ||
      (item.sotto_categoria && item.sotto_categoria.toLowerCase().includes(debouncedSearchTerm.toLowerCase()))
    )
  }, [catalogo, debouncedSearchTerm])

  // Trova l'item selezionato
  const selectedItem = catalogo.find(item => item.part_number === selectedPartNumber)

  const handleSelect = (item: CatalogoResponse) => {
    onSelect(item.part_number)
    if (onItemSelect) {
      onItemSelect(item)
    }
    setSearchTerm('')
    setIsOpen(false)
  }

  const handleInputFocus = () => {
    if (!disabled) {
      setIsOpen(true)
      if (selectedItem) {
        setSearchTerm(selectedItem.part_number)
      }
    }
  }

  const handleInputBlur = () => {
    // Ritarda la chiusura per permettere il click sulle opzioni
    setTimeout(() => {
      setIsOpen(false)
      if (selectedItem && !searchTerm) {
        setSearchTerm('')
      }
    }, 200)
  }

  return (
    <div className="grid grid-cols-4 items-center gap-4">
      <Label htmlFor="part_number_search" className="text-right">
        Part Number
      </Label>
      <div className="col-span-3 relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          id="part_number_search"
          value={isOpen ? searchTerm : (selectedItem?.part_number || '')}
          onChange={e => setSearchTerm(e.target.value)}
          onFocus={handleInputFocus}
          onBlur={handleInputBlur}
          placeholder="Cerca Part Number..."
          className="pl-10"
          disabled={isLoading || disabled}
        />
        
        {/* Dropdown con risultati */}
        {isOpen && !disabled && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
            {filteredCatalogo.length > 0 ? (
              filteredCatalogo.map(item => (
                <div
                  key={item.part_number}
                  className={`px-3 py-2 hover:bg-gray-100 cursor-pointer ${
                    selectedPartNumber === item.part_number ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => handleSelect(item)}
                >
                  <div className="font-medium">
                    {highlightMatch(item.part_number, debouncedSearchTerm)}
                  </div>
                  <div className="text-sm text-gray-600">
                    {highlightMatch(item.descrizione, debouncedSearchTerm)}
                  </div>
                  {(item.categoria || item.sotto_categoria) && (
                    <div className="text-xs text-gray-400">
                      {item.categoria && highlightMatch(item.categoria, debouncedSearchTerm)}
                      {item.categoria && item.sotto_categoria && ' > '}
                      {item.sotto_categoria && highlightMatch(item.sotto_categoria, debouncedSearchTerm)}
                    </div>
                  )}
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
        
        {error && (
          <p className="text-sm text-destructive mt-1">{error}</p>
        )}
      </div>
    </div>
  )
} 
'use client'

import { useState, useMemo } from 'react'
import { useDebounce } from '@/hooks/useDebounce'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Tool } from '@/lib/api'
import { Plus, Search } from 'lucide-react'

interface SmartToolsSelectProps {
  tools: Tool[]
  selectedIds: number[]
  onSelect: (ids: number[]) => void
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

export default function SmartToolsSelect({ 
  tools, 
  selectedIds, 
  onSelect, 
  onCreateNew, 
  isLoading = false,
  error 
}: SmartToolsSelectProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const debouncedSearchTerm = useDebounce(searchTerm, 300)

  // Filtra i tools in base al termine di ricerca
  const filteredTools = useMemo(() => {
    if (!debouncedSearchTerm) return tools
    
    return tools.filter(tool =>
      tool.part_number_tool.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
      (tool.descrizione && tool.descrizione.toLowerCase().includes(debouncedSearchTerm.toLowerCase()))
    )
  }, [tools, debouncedSearchTerm])

  // Trova i tools selezionati
  const selectedTools = tools.filter(tool => selectedIds.includes(tool.id))

  const handleToggleTool = (tool: Tool) => {
    const isSelected = selectedIds.includes(tool.id)
    if (isSelected) {
      onSelect(selectedIds.filter(id => id !== tool.id))
    } else {
      onSelect([...selectedIds, tool.id])
    }
  }

  const handleInputFocus = () => {
    setIsOpen(true)
  }

  const handleInputBlur = () => {
    // Ritarda la chiusura per permettere il click sulle opzioni
    setTimeout(() => {
      setIsOpen(false)
    }, 200)
  }

  return (
    <div className="grid grid-cols-4 items-start gap-4">
      <Label htmlFor="tools_search" className="text-right pt-2">
        Tools/Stampi
      </Label>
      <div className="col-span-3">
        <div className="flex gap-2 mb-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              id="tools_search"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              onFocus={handleInputFocus}
              onBlur={handleInputBlur}
              placeholder="Cerca tools..."
              className="pl-10"
              disabled={isLoading}
            />
            
            {/* Dropdown con risultati */}
            {isOpen && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
                {filteredTools.length > 0 ? (
                  filteredTools.map(tool => (
                    <div
                      key={tool.id}
                      className={`px-3 py-2 hover:bg-gray-100 cursor-pointer flex items-center gap-2 ${
                        selectedIds.includes(tool.id) ? 'bg-blue-50' : ''
                      }`}
                      onClick={() => handleToggleTool(tool)}
                    >
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(tool.id)}
                        onChange={() => {}} // Gestito dal click del div
                        className="h-4 w-4 rounded border-gray-300"
                      />
                      <div className="flex-1">
                        <div className="font-medium">
                          {highlightMatch(tool.part_number_tool, debouncedSearchTerm)}
                        </div>
                        {tool.descrizione && (
                          <div className="text-sm text-gray-500">
                            {highlightMatch(tool.descrizione, debouncedSearchTerm)}
                          </div>
                        )}
                        <div className="text-xs text-gray-400">
                          {tool.lunghezza_piano} x {tool.larghezza_piano} mm
                          {!tool.disponibile && ' (Non disponibile)'}
                        </div>
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
            Nuovo Tool
          </Button>
        </div>

        {/* Lista dei tools selezionati */}
        {selectedTools.length > 0 && (
          <div className="p-2 border rounded-md bg-gray-50">
            <div className="text-sm font-medium mb-2">Tools selezionati:</div>
            <div className="space-y-1">
              {selectedTools.map(tool => (
                <div key={tool.id} className="flex items-center justify-between text-sm">
                  <span>
                    {tool.part_number_tool}
                    {tool.descrizione && ` - ${tool.descrizione}`}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleToggleTool(tool)}
                    className="text-red-500 hover:text-red-700 ml-2"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {error && (
          <p className="text-sm text-destructive mt-1">{error}</p>
        )}
      </div>
    </div>
  )
} 
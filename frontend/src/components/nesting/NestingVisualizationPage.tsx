'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Eye, 
  AlertTriangle, 
  ArrowLeft, 
  Share2,
  Package,
  Layers
} from 'lucide-react'
import { NestingVisualization } from './NestingVisualization'
import { NestingExcludedTools } from './NestingExcludedTools'
import { ODLLayoutInfo, ODLNestingInfo } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

interface NestingVisualizationPageProps {
  nestingId: number
  onBack?: () => void
  className?: string
}

// Tipo union per gestire entrambi i tipi di ODL
type SelectedTool = ODLLayoutInfo | ODLNestingInfo

export function NestingVisualizationPage({ 
  nestingId, 
  onBack,
  className = "" 
}: NestingVisualizationPageProps) {
  const [selectedTool, setSelectedTool] = useState<SelectedTool | null>(null)
  const [activeTab, setActiveTab] = useState('layout')
  const { toast } = useToast()

  // Gestisce il click su un tool dal layout
  const handleLayoutToolClick = (odl: ODLLayoutInfo) => {
    setSelectedTool(odl)
    toast({
      title: "Tool Selezionato",
      description: `${odl.tool.part_number_tool} - ODL #${odl.id}`,
    })
  }

  // Gestisce il click su un tool escluso
  const handleExcludedToolClick = (odl: ODLNestingInfo) => {
    setSelectedTool(odl)
    toast({
      title: "Tool Escluso Selezionato",
      description: `${odl.tool_nome || 'Tool'} - ODL #${odl.id}`,
    })
  }

  // Condivide il layout
  const handleShare = () => {
    const url = window.location.href
    navigator.clipboard.writeText(url).then(() => {
      toast({
        title: "Link Copiato",
        description: "Il link alla visualizzazione è stato copiato negli appunti",
      })
    }).catch(() => {
      toast({
        title: "Errore",
        description: "Impossibile copiare il link",
        variant: "destructive",
      })
    })
  }

  // Helper per determinare se il tool selezionato è di tipo ODLLayoutInfo
  const isLayoutTool = (tool: SelectedTool): tool is ODLLayoutInfo => {
    return 'tool' in tool && typeof (tool as any).tool === 'object' && 'parte' in tool
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header della pagina */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {onBack && (
                <Button variant="outline" size="sm" onClick={onBack}>
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Indietro
                </Button>
              )}
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Eye className="h-5 w-5" />
                  Visualizzazione Nesting #{nestingId}
                </CardTitle>
                <CardDescription>
                  Layout grafico e analisi del posizionamento tool
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handleShare}>
                <Share2 className="h-4 w-4 mr-2" />
                Condividi
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Tool selezionato */}
      {selectedTool && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Tool Selezionato
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-sm text-muted-foreground">Part Number</div>
                <div className="font-medium">
                  {isLayoutTool(selectedTool) 
                    ? selectedTool.tool.part_number_tool 
                    : selectedTool.tool_nome || 'Tool non specificato'
                  }
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">ODL</div>
                <div className="font-medium">#{selectedTool.id}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Priorità</div>
                <Badge variant={selectedTool.priorita >= 8 ? 'destructive' : selectedTool.priorita >= 4 ? 'default' : 'secondary'}>
                  {selectedTool.priorita}
                </Badge>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Parte</div>
                <div className="font-medium">
                  {isLayoutTool(selectedTool) 
                    ? selectedTool.parte.part_number 
                    : selectedTool.parte_codice || 'Parte non specificata'
                  }
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs principali */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="layout" className="flex items-center gap-2">
            <Layers className="h-4 w-4" />
            Layout Grafico
          </TabsTrigger>
          <TabsTrigger value="excluded" className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Tool Esclusi
          </TabsTrigger>
        </TabsList>

        <TabsContent value="layout" className="space-y-4">
          <NestingVisualization
            nestingId={nestingId}
            onToolClick={handleLayoutToolClick}
            showControls={true}
          />
        </TabsContent>

        <TabsContent value="excluded" className="space-y-4">
          <NestingExcludedTools
            nestingId={nestingId}
            onToolClick={handleExcludedToolClick}
          />
        </TabsContent>
      </Tabs>

      {/* Istruzioni d'uso */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Istruzioni d'Uso</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium mb-2">Layout Grafico</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Clicca sui tool per selezionarli e vedere i dettagli</li>
                <li>• Usa i controlli zoom per ingrandire/rimpicciolire</li>
                <li>• Regola padding e bordi per ottimizzare il layout</li>
                <li>• Esporta l'immagine SVG per documentazione</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">Legenda Colori</h4>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-green-500 rounded"></div>
                  <span className="text-sm">Priorità Bassa (1-3)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-yellow-500 rounded"></div>
                  <span className="text-sm">Priorità Media (4-7)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-red-500 rounded"></div>
                  <span className="text-sm">Priorità Alta (8-10)</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 
'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { FileText, Eye, Settings } from 'lucide-react'

export default function TestSimpleNesting() {
  const [activeTab, setActiveTab] = useState('manual')

  return (
    <div className="container mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">Test Nesting Semplice</h1>
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="manual" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            <span>Test 1</span>
          </TabsTrigger>
          <TabsTrigger value="preview" className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            <span>Test 2</span>
          </TabsTrigger>
          <TabsTrigger value="parameters" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            <span>Test 3</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="manual" className="space-y-6">
          <div className="p-8 border rounded-lg">
            <h2 className="text-lg font-semibold">Tab 1 - Test Manuale</h2>
            <p>Questo è un test semplice per verificare che i tab funzionino.</p>
          </div>
        </TabsContent>

        <TabsContent value="preview" className="space-y-6">
          <div className="p-8 border rounded-lg">
            <h2 className="text-lg font-semibold">Tab 2 - Test Preview</h2>
            <p>Secondo tab di test per verificare la struttura.</p>
          </div>
        </TabsContent>

        <TabsContent value="parameters" className="space-y-6">
          <div className="p-8 border rounded-lg">
            <h2 className="text-lg font-semibold">Tab 3 - Test Parametri</h2>
            <p>Terzo tab di test per verificare la navigazione.</p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
} 
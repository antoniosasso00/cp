'use client'

import React from 'react'
import { Button } from '@/shared/components/ui/button'
import { Badge } from '@/shared/components/ui/badge'
import { ArrowLeft, RefreshCw, Download, Settings } from 'lucide-react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface CompactHeaderProps {
  batchName: string
  batchState: string
  efficiency?: number
  totalBatches?: number
  onRefresh: () => void
  onDownload: () => void
  isLoading?: boolean
}

const CompactHeader: React.FC<CompactHeaderProps> = ({
  batchName,
  batchState,
  efficiency,
  totalBatches,
  onRefresh,
  onDownload,
  isLoading = false
}) => {
  const router = useRouter()

  const getStateBadge = (state: string) => {
    switch (state?.toLowerCase()) {
      case 'draft':
        return <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-200">Draft</Badge>
      case 'sospeso':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 border-yellow-200">Sospeso</Badge>
      case 'confermato':
        return <Badge variant="secondary" className="bg-green-100 text-green-800 border-green-200">Confermato</Badge>
      case 'loaded':
        return <Badge variant="secondary" className="bg-blue-100 text-blue-800 border-blue-200">Caricato</Badge>
      case 'cured':
        return <Badge variant="secondary" className="bg-red-100 text-red-800 border-red-200">In Cura</Badge>
      case 'completato':
        return <Badge variant="secondary" className="bg-gray-100 text-gray-800 border-gray-200">Completato</Badge>
      default:
        return <Badge variant="outline">{state}</Badge>
    }
  }

  return (
    <div className="border-b bg-white sticky top-0 z-40">
      <div className="p-4">
        <div className="flex items-center justify-between">
          {/* Left section - Navigation & Title */}
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.back()}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Indietro
            </Button>
            
            <div className="flex items-center gap-3">
              <div>
                <h1 className="text-lg font-semibold text-gray-900">
                  {batchName}
                </h1>
                <div className="flex items-center gap-2 mt-1">
                  {getStateBadge(batchState)}
                  {totalBatches && totalBatches > 1 && (
                    <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                      🚀 Multi-Batch ({totalBatches})
                    </Badge>
                  )}
                  {efficiency !== undefined && (
                    <Badge 
                      variant="outline" 
                      className={`${
                        efficiency >= 80 ? 'bg-green-50 text-green-700 border-green-200' :
                        efficiency >= 60 ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                        'bg-red-50 text-red-700 border-red-200'
                      }`}
                    >
                      {efficiency.toFixed(1)}% efficienza
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Right section - Actions */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={isLoading}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              Aggiorna
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={onDownload}
              className="flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Export
            </Button>

            <Link href="/nesting/list">
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4 mr-2" />
                Lista Batch
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CompactHeader 
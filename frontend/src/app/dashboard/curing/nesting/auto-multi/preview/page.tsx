"use client";

import React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft } from 'lucide-react';
import { NestingCanvasFixed } from '@/components/Nesting/NestingCanvasFixed'

export default function NestingPreviewPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const batchId = searchParams.get('batch_id') || '13'; // Default per test

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            🔧 Preview Nesting Auto-Multi (FIXED)
          </h1>
          <p className="text-muted-foreground mt-2">
            Anteprima del nesting automatico con dimensioni corrette - Batch ID: {batchId}
          </p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline" className="text-lg px-4 py-2">
            📊 Batch #{batchId}
          </Badge>
          <Button 
            variant="outline" 
            onClick={() => router.back()}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Indietro
          </Button>
        </div>
      </div>

      {/* ✅ FIXED: Usa il nuovo componente corretto */}
      <NestingCanvasFixed
        nestingId={parseInt(batchId)}
        onToolClick={(odl) => {
          console.log('🔧 FIXED - Tool clicked in preview:', odl)
        }}
        showControls={true}
        height={700}
        className="w-full"
      />
    </div>
  );
} 
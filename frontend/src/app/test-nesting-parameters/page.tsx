'use client';

import React from 'react';
import { NestingWithParameters } from '@/components/nesting/NestingWithParameters';

export default function TestNestingParametersPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Test Step 5 - Parametri Nesting</h1>
        <p className="text-muted-foreground mt-2">
          Pagina di test per verificare l'implementazione dei parametri regolabili
        </p>
      </div>
      
      <NestingWithParameters />
    </div>
  );
} 
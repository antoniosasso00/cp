'use client';

import React, { useState } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export function TestSelect() {
  const [value, setValue] = useState<string | undefined>(undefined);

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-semibold">Test Select Component</h2>
      <div className="space-y-2">
        <label className="text-sm font-medium">Test Select con valore undefined:</label>
        <Select value={value || 'none'} onValueChange={(newValue) => setValue(newValue === 'none' ? undefined : newValue)}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Seleziona un'opzione" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">Nessuna selezione</SelectItem>
            <SelectItem value="option1">Opzione 1</SelectItem>
            <SelectItem value="option2">Opzione 2</SelectItem>
            <SelectItem value="option3">Opzione 3</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="text-sm text-gray-600">
        Valore corrente: {value || 'undefined'}
      </div>
    </div>
  );
} 
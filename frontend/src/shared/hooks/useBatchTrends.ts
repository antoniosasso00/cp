'use client';

import { useMemo } from 'react';
import { useBatchStatusStore } from './useBatchStatus';

export interface BatchTrendData {
  total: { today: number; yesterday: number; delta: number };
  sospeso: { today: number; yesterday: number; delta: number };
  confermato: { today: number; yesterday: number; delta: number };
  loaded: { today: number; yesterday: number; delta: number };
  cured: { today: number; yesterday: number; delta: number };
  completato: { today: number; yesterday: number; delta: number };
}

interface BatchWithTimestamp {
  id: string;
  stato: string;
  created_at: string;
  updated_at: string;
}

const getTrendType = (delta: number): 'increase' | 'decrease' | 'stable' => {
  if (delta > 0) return 'increase';
  if (delta < 0) return 'decrease';
  return 'stable';
};

export const useBatchTrends = (batches: BatchWithTimestamp[] = []) => {
  return useMemo(() => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    // Funzione per contare batch per data e stato
    const countBatchesByDateAndStatus = (targetDate: Date, status?: string) => {
      const nextDay = new Date(targetDate);
      nextDay.setDate(nextDay.getDate() + 1);
      
      return batches.filter(batch => {
        const batchDate = new Date(batch.created_at);
        const isInDateRange = batchDate >= targetDate && batchDate < nextDay;
        const matchesStatus = !status || batch.stato === status;
        return isInDateRange && matchesStatus;
      }).length;
    };

    // Calcolo statistiche per ogni stato
    const calculateTrend = (status?: string) => {
      const todayCount = countBatchesByDateAndStatus(today, status);
      const yesterdayCount = countBatchesByDateAndStatus(yesterday, status);
      const delta = todayCount - yesterdayCount;
      
      return {
        today: todayCount,
        yesterday: yesterdayCount,
        delta,
        type: getTrendType(delta)
      };
    };

    const trends: BatchTrendData = {
      total: calculateTrend(),
      sospeso: calculateTrend('sospeso'),
      confermato: calculateTrend('confermato'),
      loaded: calculateTrend('loaded'),
      cured: calculateTrend('cured'),
      completato: calculateTrend('completato')
    };

    return trends;
  }, [batches]);
};

// Hook per ottenere i trend con i dati correnti dal store (interno)
const useBatchTrendsFromStore = () => {
  const batchStates = useBatchStatusStore(state => state.batchStates);
  
  // Simula dati batch con timestamp per il calcolo trend
  // In un'app reale, questi dati dovrebbero venire dal backend
  const mockBatches = useMemo(() => {
    const now = new Date();
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    
    return Object.entries(batchStates).map(([id, stato], index) => ({
      id,
      stato,
      created_at: index % 2 === 0 ? yesterday.toISOString() : now.toISOString(),
      updated_at: now.toISOString()
    }));
  }, [batchStates]);
  
  return useBatchTrends(mockBatches);
};

// Utility per formattare il trend in un formato leggibile (interno)
const formatTrend = (trend: { delta: number; type: 'increase' | 'decrease' | 'stable' }) => {
  const sign = trend.delta > 0 ? '+' : '';
  return {
    text: `${sign}${trend.delta}`,
    color: trend.type === 'increase' ? 'text-green-600' : 
           trend.type === 'decrease' ? 'text-red-600' : 'text-gray-600',
    type: trend.type
  };
}; 
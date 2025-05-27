'use client';

import { useState, useEffect } from 'react';
import { scheduleApi, autoclaveApi, odlApi } from '@/lib/api';
import { Autoclave, ODLResponse } from '@/lib/api';
import CalendarSchedule from '@/components/CalendarSchedule';
import { Button } from '@/components/ui/button';

export default function SchedulePage() {
  const [autoclavi, setAutoclavi] = useState<Autoclave[]>([]);
  const [odlList, setOdlList] = useState<ODLResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Recupera i dati al caricamento della pagina
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Recupera le autoclavi usando l'API client configurato
        const autoclaviData = await autoclaveApi.getAll();
        
        // Recupera tutti gli ODL (non solo quelli in "Attesa Cura")
        const odlData = await odlApi.getAll();
        
        setAutoclavi(autoclaviData);
        setOdlList(odlData);
      } catch (err) {
        console.error('Errore nel caricamento dei dati:', err);
        setError('Impossibile caricare i dati necessari. Riprova più tardi.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-lg text-gray-700 dark:text-gray-300">Caricamento sistema di scheduling...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <p className="text-red-500 dark:text-red-400 text-lg mb-4">{error}</p>
          <Button 
            variant="outline" 
            onClick={() => window.location.reload()}
            className="bg-blue-500 hover:bg-blue-600 text-white"
          >
            🔄 Riprova
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen overflow-hidden">
      <CalendarSchedule autoclavi={autoclavi} odlList={odlList} />
    </div>
  );
}
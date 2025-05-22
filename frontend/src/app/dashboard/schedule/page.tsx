'use client';

import { useState, useEffect } from 'react';
import { scheduleApi } from '@/lib/api';
import { Autoclave, ODLResponse } from '@/lib/api';
import CalendarSchedule from '@/components/CalendarSchedule';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

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
        
        // Recupera le autoclavi - Aggiunto slash finale per evitare il redirect
        const autoclaviResponse = await fetch('/api/v1/autoclavi/');
        if (!autoclaviResponse.ok) {
          throw new Error('Errore nel caricamento delle autoclavi');
        }
        const autoclaviData = await autoclaviResponse.json();
        
        // Recupera gli ODL in stato "Attesa Cura" - Aggiunto slash finale per evitare il redirect
        const odlResponse = await fetch('/api/v1/odl/?status=Attesa Cura');
        if (!odlResponse.ok) {
          throw new Error('Errore nel caricamento degli ODL');
        }
        const odlData = await odlResponse.json();
        
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
      <div className="flex items-center justify-center h-screen">
        <p className="text-lg">Caricamento in corso...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <p className="text-red-500 text-lg">{error}</p>
        <Button 
          variant="outline" 
          className="mt-4"
          onClick={() => window.location.reload()}
        >
          Riprova
        </Button>
      </div>
    );
  }

  return (
    <div className="p-4 h-screen">
      <h1 className="text-2xl font-bold mb-4">Scheduling ODL per Autoclavi</h1>
      
      <Card className="h-[calc(100vh-150px)]">
        <CalendarSchedule autoclavi={autoclavi} odlList={odlList} />
      </Card>
    </div>
  );
} 
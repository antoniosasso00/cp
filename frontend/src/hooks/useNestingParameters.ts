import { useState, useCallback } from 'react';
import { NestingParameters } from '@/components/Nesting/NestingParametersPanel';

/**
 * Interfaccia per la risposta dell'API dei parametri
 */
interface NestingParametersResponse {
  success: boolean;
  message: string;
  parameters: NestingParameters;
}

/**
 * Interfaccia per la risposta della preview con parametri
 */
interface NestingPreviewResponse {
  success: boolean;
  message: string;
  odl_groups: Array<{
    ciclo_cura: string;
    odl_list: Array<any>;
    total_area: number;
    total_weight: number;
    compatible_autoclaves: Array<any>;
  }>;
  available_autoclaves: Array<any>;
  total_odl_pending: number;
}

/**
 * Hook personalizzato per gestire i parametri di nesting
 */
export const useNestingParameters = () => {
  const [parameters, setParameters] = useState<NestingParameters>({
    distanza_minima_tool_cm: 2.0,
    padding_bordo_autoclave_cm: 1.5,
    margine_sicurezza_peso_percent: 10.0,
    priorita_minima: 1,
    efficienza_minima_percent: 60.0,
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Carica i parametri di default dal backend
   */
  const loadDefaultParameters = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v1/nesting/parameters');
      
      if (!response.ok) {
        throw new Error(`Errore HTTP: ${response.status}`);
      }
      
      const data: NestingParametersResponse = await response.json();
      
      if (data.success) {
        setParameters(data.parameters);
      } else {
        throw new Error(data.message);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Errore sconosciuto';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Valida i parametri sul backend
   */
  const validateParameters = useCallback(async (params: NestingParameters): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v1/nesting/parameters/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });
      
      if (!response.ok) {
        throw new Error(`Errore HTTP: ${response.status}`);
      }
      
      const data: NestingParametersResponse = await response.json();
      
      if (!data.success) {
        throw new Error(data.message);
      }
      
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Errore sconosciuto';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Genera una preview con i parametri specificati
   */
  const generatePreviewWithParameters = useCallback(async (params: NestingParameters): Promise<NestingPreviewResponse | null> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v1/nesting/preview-with-parameters', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });
      
      if (!response.ok) {
        throw new Error(`Errore HTTP: ${response.status}`);
      }
      
      const data: NestingPreviewResponse = await response.json();
      
      if (!data.success) {
        throw new Error(data.message);
      }
      
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Errore sconosciuto';
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Genera il nesting automatico con i parametri specificati
   */
  const generateAutomaticNesting = useCallback(async (params: NestingParameters, forceRegenerate: boolean = false): Promise<any> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v1/nesting/automatic', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          force_regenerate: forceRegenerate,
          parameters: params,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Errore HTTP: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.message);
      }
      
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Errore sconosciuto';
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Aggiorna i parametri locali
   */
  const updateParameters = useCallback((newParameters: NestingParameters) => {
    setParameters(newParameters);
  }, []);

  return {
    parameters,
    isLoading,
    error,
    loadDefaultParameters,
    validateParameters,
    generatePreviewWithParameters,
    generateAutomaticNesting,
    updateParameters,
  };
}; 
'use client';

import React, { useState, useEffect, useRef } from 'react';
import { nestingApi } from '@/lib/api/nestingApi';
import { NestingParameters } from '@/lib/types/nesting';

interface ParametersFormProps {
    onParametersChange?: (params: NestingParameters) => void;
    disabled?: boolean;
}

// Funzione debounce semplice
function debounce<T extends (...args: any[]) => void>(fn: T, delay: number) {
    let timer: ReturnType<typeof setTimeout>;
    return (...args: Parameters<T>) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
}

const ParametersForm: React.FC<ParametersFormProps> = ({ 
    onParametersChange,
    disabled = false 
}) => {
    const [params, setParams] = useState<NestingParameters>({
        peso_valvole: 1.0,
        peso_area: 1.0,
        peso_priorita: 1.0,
        spazio_minimo_mm: 30.0
    });
    
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [saved, setSaved] = useState<boolean>(false);
    
    // Ref per la funzione debounce
    const debouncedOnParametersChange = useRef<((params: NestingParameters) => void) | null>(null);

    // Carica i parametri attuali dal server
    useEffect(() => {
        const fetchParameters = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await nestingApi.getParameters();
                setParams(data);
            } catch (err) {
                setError('Errore nel caricamento dei parametri');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        
        fetchParameters();
    }, []);
    
    useEffect(() => {
        if (onParametersChange) {
            debouncedOnParametersChange.current = debounce(onParametersChange, 500);
        }
    }, [onParametersChange]);
    
    // Gestisce il cambiamento di un parametro
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        const newParams = { ...params, [name]: parseFloat(value) };
        setParams(newParams);
        
        // Notifica il componente padre (debounced)
        if (debouncedOnParametersChange.current) {
            debouncedOnParametersChange.current(newParams);
        }
        // Resetta il messaggio di successo
        setSaved(false);
    };
    
    // Salva i parametri
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        try {
            setLoading(true);
            setError(null);
            setSaved(false);
            
            await nestingApi.updateParameters(params);
            setSaved(true);
        } catch (err) {
            setError('Errore nell\'aggiornamento dei parametri');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };
    
    if (loading && !params) {
        return <div className="text-center py-4">Caricamento parametri...</div>;
    }
    
    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <h3 className="text-lg font-semibold mb-3">Parametri di Ottimizzazione</h3>
            
            {error && (
                <div className="mb-4 p-2 bg-red-50 text-red-700 rounded border border-red-200">
                    {error}
                </div>
            )}
            
            {saved && (
                <div className="mb-4 p-2 bg-green-50 text-green-700 rounded border border-green-200">
                    Parametri salvati con successo!
                </div>
            )}
            
            <form onSubmit={handleSubmit}>
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">
                            Peso Valvole: {params.peso_valvole.toFixed(1)}
                        </label>
                        <input
                            type="range"
                            name="peso_valvole"
                            min="0"
                            max="10"
                            step="0.1"
                            value={params.peso_valvole}
                            onChange={handleChange}
                            className="w-full"
                            disabled={disabled}
                        />
                        <div className="flex justify-between text-xs text-gray-500">
                            <span>0.0</span>
                            <span>5.0</span>
                            <span>10.0</span>
                        </div>
                    </div>
                    
                    <div>
                        <label className="block text-sm font-medium mb-1">
                            Peso Area: {params.peso_area.toFixed(1)}
                        </label>
                        <input
                            type="range"
                            name="peso_area"
                            min="0"
                            max="10"
                            step="0.1"
                            value={params.peso_area}
                            onChange={handleChange}
                            className="w-full"
                            disabled={disabled}
                        />
                        <div className="flex justify-between text-xs text-gray-500">
                            <span>0.0</span>
                            <span>5.0</span>
                            <span>10.0</span>
                        </div>
                    </div>
                    
                    <div>
                        <label className="block text-sm font-medium mb-1">
                            Peso Priorità: {params.peso_priorita.toFixed(1)}
                        </label>
                        <input
                            type="range"
                            name="peso_priorita"
                            min="0"
                            max="10"
                            step="0.1"
                            value={params.peso_priorita}
                            onChange={handleChange}
                            className="w-full"
                            disabled={disabled}
                        />
                        <div className="flex justify-between text-xs text-gray-500">
                            <span>0.0</span>
                            <span>5.0</span>
                            <span>10.0</span>
                        </div>
                    </div>
                    
                    <div>
                        <label className="block text-sm font-medium mb-1">
                            Spazio Minimo (mm): {params.spazio_minimo_mm.toFixed(1)}
                        </label>
                        <input
                            type="range"
                            name="spazio_minimo_mm"
                            min="0"
                            max="100"
                            step="1"
                            value={params.spazio_minimo_mm}
                            onChange={handleChange}
                            className="w-full"
                            disabled={disabled}
                        />
                        <div className="flex justify-between text-xs text-gray-500">
                            <span>0</span>
                            <span>50</span>
                            <span>100</span>
                        </div>
                    </div>
                    
                    {!disabled && (
                        <div className="pt-2">
                            <button
                                type="submit"
                                className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md shadow-sm disabled:opacity-50"
                                disabled={loading}
                            >
                                {loading ? 'Salvataggio...' : 'Salva Parametri'}
                            </button>
                        </div>
                    )}
                </div>
            </form>
            
            <div className="mt-4 text-sm text-gray-500">
                <p className="font-medium mb-1">Guida ai parametri:</p>
                <ul className="space-y-1 list-disc pl-5">
                    <li><b>Peso Valvole:</b> Importanza dell'utilizzo ottimale delle valvole</li>
                    <li><b>Peso Area:</b> Importanza della densità di carico (ottimizzazione area)</li>
                    <li><b>Peso Priorità:</b> Importanza di processare gli ODL ad alta priorità</li>
                    <li><b>Spazio Minimo:</b> Distanza minima tra gli ODL nell'autoclave</li>
                </ul>
            </div>
        </div>
    );
};

export default ParametersForm; 
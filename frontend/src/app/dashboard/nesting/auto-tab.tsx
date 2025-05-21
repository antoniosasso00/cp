'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { nestingApi } from '@/lib/api/nestingApi';
import { AutoclaveLayout, NestingParameters, NestingRequest, NestingResponse } from '@/lib/types/nesting';
import ParametersForm from '@/components/nesting/ParametersForm';
import NestingVisualizer from '@/components/nesting/NestingVisualizer';
import { Loader2 } from 'lucide-react';

export default function AutoNestingTab() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [parameters, setParameters] = useState<NestingParameters | null>(null);
    const [result, setResult] = useState<NestingResponse | null>(null);
    const [selectedOdlId, setSelectedOdlId] = useState<number>(-1);
    
    // Esegue il nesting automatico
    const handleRunNesting = async () => {
        try {
            setLoading(true);
            setError(null);
            setSuccess(null);
            setResult(null);
            
            const request: NestingRequest = {
                parameters: parameters
            };
            
            const response = await nestingApi.runAutoNesting(request);
            setResult(response);
            
            if (response.success) {
                setSuccess('Nesting automatico completato con successo.');
            } else {
                setError(response.message || 'Errore durante l\'esecuzione del nesting automatico.');
            }
        } catch (err: any) {
            setError(err.message || 'Errore durante l\'esecuzione del nesting automatico.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };
    
    // Conferma il nesting
    const handleConfirmNesting = async (layout: AutoclaveLayout) => {
        if (!layout.nesting_id) {
            setError('ID nesting non disponibile. Impossibile confermare.');
            return;
        }
        
        try {
            setLoading(true);
            setError(null);
            setSuccess(null);
            
            const response = await nestingApi.confirmNesting(layout.nesting_id);
            
            if (response.success) {
                setSuccess('Nesting confermato con successo. Gli ODL sono stati aggiornati a "Cura".');
                // Rimuovi il layout confermato dai risultati
                if (result) {
                    const newLayouts = result.layouts.filter(l => l.nesting_id !== layout.nesting_id);
                    setResult({
                        ...result,
                        layouts: newLayouts
                    });
                }
            } else {
                setError('Errore durante la conferma del nesting.');
            }
        } catch (err: any) {
            setError(err.message || 'Errore durante la conferma del nesting.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };
    
    // Gestisce il cambio di parametri
    const handleParametersChange = (params: NestingParameters) => {
        setParameters(params);
    };
    
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Colonna di sinistra: Parametri */}
            <div>
                <ParametersForm 
                    onParametersChange={handleParametersChange}
                    disabled={loading}
                />
                
                <div className="mt-6">
                    <Button
                        className="w-full"
                        size="lg"
                        onClick={handleRunNesting}
                        disabled={loading}
                    >
                        {loading ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Elaborazione...
                            </>
                        ) : (
                            'Esegui Nesting Automatico'
                        )}
                    </Button>
                </div>
                
                {error && (
                    <Alert variant="destructive" className="mt-4">
                        <AlertTitle>Errore</AlertTitle>
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}
                
                {success && (
                    <Alert className="mt-4 border-green-500 text-green-700 bg-green-50">
                        <AlertTitle>Successo</AlertTitle>
                        <AlertDescription>{success}</AlertDescription>
                    </Alert>
                )}
                
                {result && !result.success && (
                    <Alert variant="warning" className="mt-4">
                        <AlertTitle>Attenzione</AlertTitle>
                        <AlertDescription>{result.message}</AlertDescription>
                    </Alert>
                )}
            </div>
            
            {/* Colonna destra: Risultati */}
            <div className="md:col-span-2">
                {result && result.success && result.layouts.length > 0 ? (
                    <div className="space-y-6">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold">Risultati Nesting</h2>
                            <div className="text-sm text-gray-500">
                                {result.layouts.length} autoclavi
                            </div>
                        </div>
                        
                        {result.layouts.map((layout, index) => (
                            <Card key={index} className="overflow-hidden">
                                <NestingVisualizer 
                                    layout={layout}
                                    onSelect={setSelectedOdlId}
                                    selectedOdlId={selectedOdlId}
                                />
                                
                                <div className="p-4 border-t border-gray-200 bg-gray-50 flex justify-end">
                                    <Button
                                        onClick={() => handleConfirmNesting(layout)}
                                        disabled={loading}
                                        className="bg-green-600 hover:bg-green-700"
                                    >
                                        {loading ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                Confermando...
                                            </>
                                        ) : (
                                            'Conferma e Carica'
                                        )}
                                    </Button>
                                </div>
                            </Card>
                        ))}
                    </div>
                ) : (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                        <h3 className="text-lg font-medium mb-2">Nessun risultato disponibile</h3>
                        <p className="text-gray-500 mb-6">
                            Utilizza i parametri a sinistra e premi "Esegui Nesting Automatico" per ottimizzare la disposizione degli ODL nelle autoclavi.
                        </p>
                        
                        <div className="max-w-md mx-auto">
                            <p className="text-sm text-gray-500 mb-1 text-left font-medium">L'algoritmo di nesting:</p>
                            <ul className="text-sm text-gray-500 list-disc pl-5 text-left space-y-1">
                                <li>Ottimizza la disposizione degli ODL nelle autoclavi disponibili</li>
                                <li>Raggruppa ODL con cicli di cura compatibili</li>
                                <li>Considera le priorità degli ODL, l'area disponibile e le valvole</li>
                                <li>Genera layout 2D per ogni autoclave utilizzata</li>
                            </ul>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
} 
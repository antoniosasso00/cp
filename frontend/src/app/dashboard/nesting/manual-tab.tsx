'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { nestingApi } from '@/lib/api/nestingApi';
import { AutoclaveLayout, NestingParameters, NestingRequest, NestingResponse } from '@/lib/types/nesting';
import ParametersForm from '@/components/nesting/ParametersForm';
import NestingVisualizer from '@/components/nesting/NestingVisualizer';
import ODLSelector from '@/components/nesting/ODLSelector';
import { Loader2 } from 'lucide-react';

export default function ManualNestingTab() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [parameters, setParameters] = useState<NestingParameters | null>(null);
    const [selectedOdlIds, setSelectedOdlIds] = useState<number[]>([]);
    const [result, setResult] = useState<NestingResponse | null>(null);
    const [selectedResultOdlId, setSelectedResultOdlId] = useState<number>(-1);
    
    // Esegue il nesting manuale
    const handleRunNesting = async () => {
        if (selectedOdlIds.length === 0) {
            setError('Seleziona almeno un ODL per eseguire il nesting manuale.');
            return;
        }
        
        try {
            setLoading(true);
            setError(null);
            setSuccess(null);
            setResult(null);
            
            const request: NestingRequest = {
                odl_ids: selectedOdlIds,
                parameters: parameters,
                manual: true
            };
            
            const response = await nestingApi.runManualNesting(request);
            setResult(response);
            
            if (response.success) {
                setSuccess('Nesting manuale completato con successo.');
            } else {
                setError(response.message || 'Errore durante l\'esecuzione del nesting manuale.');
            }
        } catch (err: any) {
            setError(err.message || 'Errore durante l\'esecuzione del nesting manuale.');
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
                // Resetta lo stato
                setResult(null);
                setSelectedOdlIds([]);
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
    
    // Gestisce il cambio di selezione degli ODL
    const handleSelectionChange = (selectedIds: number[]) => {
        setSelectedOdlIds(selectedIds);
    };
    
    // Gestisce il cambio di parametri
    const handleParametersChange = (params: NestingParameters) => {
        setParameters(params);
    };
    
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Colonna di sinistra: Selezione ODL */}
            <div>
                <ODLSelector 
                    onSelectionChange={handleSelectionChange}
                    disabled={loading}
                />
                
                <div className="mt-6">
                    <Button
                        className="w-full"
                        size="lg"
                        onClick={handleRunNesting}
                        disabled={loading || selectedOdlIds.length === 0}
                    >
                        {loading ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Elaborazione...
                            </>
                        ) : (
                            `Esegui Nesting Manuale (${selectedOdlIds.length} ODL)`
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
                
                {/* Parametri in versione ridotta */}
                <div className="mt-6">
                    <ParametersForm 
                        onParametersChange={handleParametersChange}
                        disabled={loading}
                    />
                </div>
            </div>
            
            {/* Colonna destra: Risultati */}
            <div>
                {result && result.success && result.layouts.length > 0 ? (
                    <div className="space-y-6">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold">Risultato Nesting Manuale</h2>
                            <div className="text-sm text-gray-500">
                                {result.layouts[0].odl_layout.length} ODL
                            </div>
                        </div>
                        
                        <Card className="overflow-hidden">
                            <NestingVisualizer 
                                layout={result.layouts[0]}
                                onSelect={setSelectedResultOdlId}
                                selectedOdlId={selectedResultOdlId}
                            />
                            
                            <div className="p-4 border-t border-gray-200 bg-gray-50 flex justify-end">
                                <Button
                                    onClick={() => handleConfirmNesting(result.layouts[0])}
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
                    </div>
                ) : (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center h-full flex flex-col justify-center">
                        <h3 className="text-lg font-medium mb-2">Nessun risultato disponibile</h3>
                        <p className="text-gray-500 mb-6">
                            Seleziona gli ODL dalla lista a sinistra e premi "Esegui Nesting Manuale" per creare un layout personalizzato.
                        </p>
                        
                        <div className="max-w-md mx-auto">
                            <p className="text-sm text-gray-500 mb-1 text-left font-medium">Il nesting manuale ti permette di:</p>
                            <ul className="text-sm text-gray-500 list-disc pl-5 text-left space-y-1">
                                <li>Selezionare precisamente quali ODL includere nel carico</li>
                                <li>Filtrare gli ODL per ciclo di cura e priorità</li>
                                <li>Ottimizzare la disposizione degli ODL selezionati</li>
                                <li>Visualizzare immediatamente il risultato del nesting</li>
                            </ul>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
} 
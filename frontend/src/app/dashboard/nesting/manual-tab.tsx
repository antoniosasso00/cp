'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { nestingApi } from '@/lib/api/nestingApi';
import { AutoclaveLayout, NestingParameters, NestingRequest, NestingResponse } from '@/lib/types/nesting';
import ParametersForm from '@/components/nesting/ParametersForm';
import NestingVisualizer from '@/components/nesting/NestingVisualizer';
import ODLSelector from '@/components/nesting/ODLSelector';
import { Loader2, Check } from 'lucide-react';

export default function ManualNestingTab() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [parameters, setParameters] = useState<NestingParameters | null>(null);
    const [selectedOdlIds, setSelectedOdlIds] = useState<number[]>([]);
    const [result, setResult] = useState<NestingResponse | null>(null);
    const [selectedResultOdlId, setSelectedResultOdlId] = useState<number>(-1);
    const [progress, setProgress] = useState<{
        step: string;
        percentage: number;
        message: string;
    } | null>(null);
    
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
            setProgress({
                step: 'Inizializzazione',
                percentage: 0,
                message: 'Preparazione dei parametri...'
            });
            
            const request: NestingRequest = {
                odl_ids: selectedOdlIds,
                parameters: parameters,
                manual: true
            };
            
            setProgress({
                step: 'Analisi ODL',
                percentage: 20,
                message: `Analisi di ${selectedOdlIds.length} ODL selezionati...`
            });
            
            const response = await nestingApi.runManualNesting(request);
            setResult(response);
            
            if (response.success) {
                setProgress({
                    step: 'Completato',
                    percentage: 100,
                    message: 'Nesting completato con successo'
                });
                setSuccess('Nesting manuale completato con successo.');
            } else {
                setError(response.message || 'Errore durante l\'esecuzione del nesting manuale.');
            }
        } catch (err: any) {
            let errorMessage = 'Errore durante l\'esecuzione del nesting manuale.';
            
            if (err.message.includes('network')) {
                errorMessage = 'Errore di connessione. Verifica la tua connessione internet e riprova.';
            } else if (err.message.includes('timeout')) {
                errorMessage = 'Timeout della richiesta. Il server sta impiegando troppo tempo a rispondere.';
            } else if (err.message.includes('validation')) {
                errorMessage = 'Errore di validazione dei parametri. Verifica i valori inseriti.';
            }
            
            setError(errorMessage);
            console.error('Errore nesting:', err);
        } finally {
            setLoading(false);
            setProgress(null);
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
            setProgress({
                step: 'Conferma',
                percentage: 0,
                message: 'Preparazione della conferma...'
            });
            
            const response = await nestingApi.confirmNesting(layout.nesting_id);
            
            if (response.success) {
                setProgress({
                    step: 'Completato',
                    percentage: 100,
                    message: 'Nesting confermato con successo'
                });
                setSuccess('Nesting confermato con successo. Gli ODL sono stati aggiornati a "Cura".');
                // Resetta lo stato
                setResult(null);
                setSelectedOdlIds([]);
            } else {
                setError('Errore durante la conferma del nesting.');
            }
        } catch (err: any) {
            let errorMessage = 'Errore durante la conferma del nesting.';
            
            if (err.message.includes('network')) {
                errorMessage = 'Errore di connessione durante la conferma. Verifica la tua connessione internet.';
            } else if (err.message.includes('timeout')) {
                errorMessage = 'Timeout durante la conferma. Il server sta impiegando troppo tempo a rispondere.';
            }
            
            setError(errorMessage);
            console.error('Errore conferma:', err);
        } finally {
            setLoading(false);
            setProgress(null);
        }
    };
    
    // Gestisce il cambio di selezione degli ODL
    const handleSelectionChange = (selectedIds: number[]) => {
        setSelectedOdlIds(selectedIds);
        // Resetta gli errori quando cambia la selezione
        setError(null);
    };
    
    // Gestisce il cambio di parametri
    const handleParametersChange = (params: NestingParameters) => {
        setParameters(params);
        // Resetta gli errori quando cambiano i parametri
        setError(null);
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
                                {progress?.step || 'Elaborazione...'}
                            </>
                        ) : (
                            `Esegui Nesting Manuale (${selectedOdlIds.length} ODL)`
                        )}
                    </Button>
                </div>
                
                {/* Barra di progresso */}
                {progress && (
                    <div className="mt-4">
                        <div className="flex justify-between text-sm text-gray-600 mb-1">
                            <span>{progress.step}</span>
                            <span>{progress.percentage}%</span>
                        </div>
                        <div className="w-full h-2 bg-gray-200 rounded-full">
                            <div
                                className="h-full bg-blue-500 rounded-full transition-all duration-300"
                                style={{ width: `${progress.percentage}%` }}
                            />
                        </div>
                        <p className="text-sm text-gray-500 mt-1">{progress.message}</p>
                    </div>
                )}
                
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
            
            {/* Colonna di destra: Risultati */}
            <div>
                {result && result.layouts.length > 0 ? (
                    <div className="space-y-6">
                        {result.layouts.map((layout, index) => (
                            <Card key={layout.nesting_id || index}>
                                <CardHeader>
                                    <CardTitle>Layout Autoclave {index + 1}</CardTitle>
                                    <CardDescription>
                                        Efficienza: {(layout.efficienza_area * 100).toFixed(1)}%
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <NestingVisualizer 
                                        layout={layout}
                                        onSelect={setSelectedResultOdlId}
                                        selectedOdlId={selectedResultOdlId}
                                    />
                                </CardContent>
                                <CardFooter className="border-t bg-gray-50">
                                    <Button 
                                        onClick={() => handleConfirmNesting(layout)}
                                        disabled={loading}
                                        className="ml-auto bg-green-600 hover:bg-green-700"
                                    >
                                        {loading ? (
                                            <>
                                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                                Confermando...
                                            </>
                                        ) : (
                                            <>
                                                <Check className="h-4 w-4 mr-2" />
                                                Conferma Layout
                                            </>
                                        )}
                                    </Button>
                                </CardFooter>
                            </Card>
                        ))}
                    </div>
                ) : (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                        <h3 className="text-lg font-medium mb-2">Nessun risultato disponibile</h3>
                        <p className="text-gray-500 mb-6">
                            Seleziona gli ODL a sinistra e premi "Esegui Nesting Manuale" per ottimizzare la disposizione.
                        </p>
                        
                        <div className="max-w-md mx-auto">
                            <p className="text-sm text-gray-500 mb-1 text-left font-medium">Il nesting manuale:</p>
                            <ul className="text-sm text-gray-500 list-disc pl-5 text-left space-y-1">
                                <li>Permette di selezionare specifici ODL da processare</li>
                                <li>Ottimizza la disposizione degli ODL selezionati</li>
                                <li>Considera le priorità e le dimensioni degli ODL</li>
                                <li>Genera un layout 2D per l'autoclave</li>
                            </ul>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
} 
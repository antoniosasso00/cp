'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { nestingApi } from '@/lib/api/nestingApi';
import { AutoclaveLayout, NestingParameters, NestingRequest, NestingResponse } from '@/lib/types/nesting';
import ParametersForm from '@/components/nesting/ParametersForm';
import NestingVisualizer from '@/components/nesting/NestingVisualizer';
import { Loader2, Check } from 'lucide-react';

export default function AutoNestingTab() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [parameters, setParameters] = useState<NestingParameters | null>(null);
    const [result, setResult] = useState<NestingResponse | null>(null);
    const [selectedOdlId, setSelectedOdlId] = useState<number>(-1);
    const [progress, setProgress] = useState<{
        step: string;
        percentage: number;
        message: string;
    } | null>(null);
    
    // Esegue il nesting automatico
    const handleRunNesting = async () => {
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
                parameters: parameters
            };
            
            setProgress({
                step: 'Analisi ODL',
                percentage: 20,
                message: 'Analisi degli ODL disponibili...'
            });
            
            const response = await nestingApi.runAutoNesting(request);
            setResult(response);
            
            if (response.success) {
                setProgress({
                    step: 'Completato',
                    percentage: 100,
                    message: 'Nesting completato con successo'
                });
                setSuccess('Nesting automatico completato con successo.');
            } else {
                setError(response.message || 'Errore durante l\'esecuzione del nesting automatico.');
            }
        } catch (err: any) {
            let errorMessage = 'Errore durante l\'esecuzione del nesting automatico.';
            
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
                                {progress?.step || 'Elaborazione...'}
                            </>
                        ) : (
                            'Esegui Nesting Automatico'
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
                
                {result && !result.success && (
                    <Alert variant="warning" className="mt-4">
                        <AlertTitle>Attenzione</AlertTitle>
                        <AlertDescription>{result.message}</AlertDescription>
                    </Alert>
                )}
            </div>
            
            {/* Colonna di destra: Risultati */}
            <div className="md:col-span-2">
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
                                        onSelect={setSelectedOdlId}
                                        selectedOdlId={selectedOdlId}
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
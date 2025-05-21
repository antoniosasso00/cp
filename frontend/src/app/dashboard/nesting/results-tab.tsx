'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { nestingApi } from '@/lib/api/nestingApi';
import { NestingResultSummary } from '@/lib/types/nesting';
import { Loader2, ArrowDownUp, BarChart2, Check, Clock, Info } from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

export default function ResultsTab() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [results, setResults] = useState<NestingResultSummary[]>([]);
    
    // Carica i risultati di nesting
    useEffect(() => {
        const fetchResults = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await nestingApi.getResults();
                setResults(data);
            } catch (err: any) {
                setError(err.message || 'Errore nel caricamento dei risultati di nesting');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        
        fetchResults();
    }, []);
    
    // Formatta la data in formato italiano
    const formatDate = (date: string) => {
        try {
            return format(new Date(date), 'dd MMM yyyy, HH:mm', { locale: it });
        } catch (e) {
            return 'Data non valida';
        }
    };
    
    if (loading) {
        return (
            <div className="flex justify-center items-center py-12">
                <Loader2 className="h-6 w-6 animate-spin mr-2" />
                <span>Caricamento risultati...</span>
            </div>
        );
    }
    
    if (error) {
        return (
            <Alert variant="destructive" className="my-4">
                <AlertTitle>Errore</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
            </Alert>
        );
    }
    
    if (results.length === 0) {
        return (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center my-4">
                <h3 className="text-lg font-medium mb-2">Nessun risultato di nesting salvato</h3>
                <p className="text-gray-500">
                    Esegui un nesting automatico o manuale per vedere i risultati qui.
                </p>
            </div>
        );
    }
    
    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle>Storia Nesting</CardTitle>
                    <CardDescription>
                        Risultati di nesting recenti, ordinati dal più recente
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Codice</TableHead>
                                <TableHead>Autoclave</TableHead>
                                <TableHead>Stato</TableHead>
                                <TableHead>Data</TableHead>
                                <TableHead>Efficienza</TableHead>
                                <TableHead>Valvole</TableHead>
                                <TableHead>Tipo</TableHead>
                                <TableHead>Azioni</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {results.map((result) => (
                                <TableRow key={result.id}>
                                    <TableCell className="font-medium">
                                        {result.codice}
                                    </TableCell>
                                    <TableCell>
                                        {result.autoclave_nome}
                                    </TableCell>
                                    <TableCell>
                                        {result.confermato ? (
                                            <Badge className="bg-green-600">
                                                <Check className="h-3 w-3 mr-1" />
                                                Confermato
                                            </Badge>
                                        ) : (
                                            <Badge variant="outline" className="border-amber-500 text-amber-500">
                                                <Clock className="h-3 w-3 mr-1" />
                                                In attesa
                                            </Badge>
                                        )}
                                    </TableCell>
                                    <TableCell>
                                        <div className="text-sm">
                                            {formatDate(result.created_at)}
                                        </div>
                                        {result.confermato && result.data_conferma && (
                                            <div className="text-xs text-gray-500">
                                                Confermato: {formatDate(result.data_conferma)}
                                            </div>
                                        )}
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex items-center">
                                            <BarChart2 className={`h-4 w-4 mr-1 ${
                                                result.efficienza_area > 0.7 ? 'text-green-500' :
                                                result.efficienza_area > 0.5 ? 'text-amber-500' :
                                                'text-gray-500'
                                            }`} />
                                            {(result.efficienza_area * 100).toFixed(1)}%
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        {result.valvole_utilizzate}/{result.valvole_totali}
                                    </TableCell>
                                    <TableCell>
                                        {result.generato_manualmente ? (
                                            <Badge variant="outline" className="border-blue-500 text-blue-500">
                                                Manuale
                                            </Badge>
                                        ) : (
                                            <Badge variant="outline" className="border-purple-500 text-purple-500">
                                                Auto
                                            </Badge>
                                        )}
                                    </TableCell>
                                    <TableCell>
                                        <Button 
                                            variant="outline" 
                                            size="sm"
                                            asChild
                                        >
                                            <a href={`/dashboard/nesting/details/${result.id}`}>
                                                <Info className="h-4 w-4 mr-1" />
                                                Dettagli
                                            </a>
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-lg">Utilizzo Area</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold">
                            {(results.reduce((sum, r) => sum + r.efficienza_area, 0) / results.length * 100).toFixed(1)}%
                        </div>
                        <p className="text-sm text-gray-500 mt-1">Efficienza media dell'area</p>
                    </CardContent>
                </Card>
                
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-lg">Utilizzo Valvole</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold">
                            {(results.reduce((sum, r) => sum + (r.valvole_utilizzate / r.valvole_totali), 0) / results.length * 100).toFixed(1)}%
                        </div>
                        <p className="text-sm text-gray-500 mt-1">Efficienza media valvole</p>
                    </CardContent>
                </Card>
                
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-lg">Nesting Totali</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold">
                            {results.length}
                        </div>
                        <p className="text-sm text-gray-500 mt-1">
                            {results.filter(r => r.confermato).length} confermati
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
} 
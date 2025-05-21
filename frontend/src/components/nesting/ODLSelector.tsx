'use client';

import React, { useState, useEffect } from 'react';
import { nestingApi } from '@/lib/api/nestingApi';
import { ODLAttesaCura } from '@/lib/types/nesting';

interface ODLSelectorProps {
    onSelectionChange: (selectedIds: number[]) => void;
    disabled?: boolean;
}

const ODLSelector: React.FC<ODLSelectorProps> = ({ onSelectionChange, disabled = false }) => {
    const [odls, setODLs] = useState<ODLAttesaCura[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedIds, setSelectedIds] = useState<number[]>([]);
    const [searchTerm, setSearchTerm] = useState<string>('');
    const [filters, setFilters] = useState({
        ciclo_cura_id: 'all',
        priorita: 'all'
    });
    
    // Recupera la lista di ODL in attesa di cura
    useEffect(() => {
        const fetchODLs = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await nestingApi.getODLInAttesaCura();
                setODLs(data);
            } catch (err) {
                setError('Errore nel caricamento degli ODL in attesa di cura');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        
        fetchODLs();
    }, []);
    
    // Gestisce la selezione/deselezione di un ODL
    const handleToggleSelect = (id: number) => {
        if (disabled) return;
        
        let newSelectedIds;
        if (selectedIds.includes(id)) {
            newSelectedIds = selectedIds.filter(selectedId => selectedId !== id);
        } else {
            newSelectedIds = [...selectedIds, id];
        }
        
        setSelectedIds(newSelectedIds);
        onSelectionChange(newSelectedIds);
    };
    
    // Seleziona/deseleziona tutti gli ODL filtrati
    const handleToggleAll = () => {
        if (disabled) return;
        
        const filteredODLs = getFilteredODLs();
        const filteredIds = filteredODLs.map(odl => odl.id);
        
        // Se tutti gli ODL filtrati sono già selezionati, deseleziona tutti
        const allSelected = filteredIds.every(id => selectedIds.includes(id));
        
        if (allSelected) {
            // Deseleziona solo quelli filtrati
            const newSelectedIds = selectedIds.filter(id => !filteredIds.includes(id));
            setSelectedIds(newSelectedIds);
            onSelectionChange(newSelectedIds);
        } else {
            // Seleziona tutti quelli filtrati (mantenendo eventuali altri già selezionati)
            const uniqueIds = Array.from(new Set([...selectedIds, ...filteredIds]));
            setSelectedIds(uniqueIds);
            onSelectionChange(uniqueIds);
        }
    };
    
    // Filtra gli ODL in base a ricerca e filtri
    const getFilteredODLs = () => {
        return odls.filter(odl => {
            // Filtra per termine di ricerca
            const searchMatch = 
                searchTerm === '' || 
                odl.parte_nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
                odl.tool_codice.toLowerCase().includes(searchTerm.toLowerCase()) ||
                odl.id.toString().includes(searchTerm);
            
            // Filtra per ciclo di cura
            const cicloMatch = 
                filters.ciclo_cura_id === 'all' || 
                odl.ciclo_cura_id.toString() === filters.ciclo_cura_id;
            
            // Filtra per priorità
            const prioritaMatch = 
                filters.priorita === 'all' || 
                odl.priorita.toString() === filters.priorita;
            
            return searchMatch && cicloMatch && prioritaMatch;
        });
    };
    
    // Ottieni i cicli di cura unici per il filtro
    const getUniqueCicli = () => {
        const cicliMap = odls.reduce((acc, odl) => {
            acc[odl.ciclo_cura_id] = true;
            return acc;
        }, {} as Record<number, boolean>);
        
        return Object.keys(cicliMap).map(Number).sort((a, b) => a - b);
    };
    
    // Ottieni le priorità uniche per il filtro
    const getUniquePriorita = () => {
        const prioritaMap = odls.reduce((acc, odl) => {
            acc[odl.priorita] = true;
            return acc;
        }, {} as Record<number, boolean>);
        
        return Object.keys(prioritaMap).map(Number).sort((a, b) => b - a);  // Ordina dal più alto al più basso
    };
    
    // Mappa dei nomi dei cicli di cura per ID
    const getCicloName = (id: number) => {
        const odl = odls.find(o => o.ciclo_cura_id === id);
        return odl ? odl.ciclo_cura_nome : `Ciclo ${id}`;
    };
    
    const filteredODLs = getFilteredODLs();
    const uniqueCicli = getUniqueCicli();
    const uniquePriorita = getUniquePriorita();
    
    if (loading) {
        return <div className="text-center py-4">Caricamento ODL in attesa di cura...</div>;
    }
    
    if (error) {
        return (
            <div className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
                {error}
            </div>
        );
    }
    
    if (odls.length === 0) {
        return (
            <div className="p-4 bg-yellow-50 text-yellow-700 rounded-lg border border-yellow-200">
                Non ci sono ODL in stato "Attesa Cura". Completa la fase di laminazione per alcuni ODL.
            </div>
        );
    }
    
    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <h3 className="text-lg font-semibold mb-3">Seleziona ODL per Nesting Manuale</h3>
            
            <div className="mb-4 grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                    <label className="block text-sm font-medium mb-1">Ricerca</label>
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="ID, parte o tool..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        disabled={disabled}
                    />
                </div>
                
                <div>
                    <label className="block text-sm font-medium mb-1">Ciclo di Cura</label>
                    <select
                        value={filters.ciclo_cura_id}
                        onChange={(e) => setFilters({ ...filters, ciclo_cura_id: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        disabled={disabled}
                    >
                        <option value="all">Tutti i cicli</option>
                        {uniqueCicli.map(id => (
                            <option key={id} value={id.toString()}>
                                {getCicloName(id)}
                            </option>
                        ))}
                    </select>
                </div>
                
                <div>
                    <label className="block text-sm font-medium mb-1">Priorità</label>
                    <select
                        value={filters.priorita}
                        onChange={(e) => setFilters({ ...filters, priorita: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        disabled={disabled}
                    >
                        <option value="all">Tutte le priorità</option>
                        {uniquePriorita.map(priorita => (
                            <option key={priorita} value={priorita.toString()}>
                                {priorita} - {priorita >= 4 ? 'Alta' : priorita >= 2 ? 'Media' : 'Bassa'}
                            </option>
                        ))}
                    </select>
                </div>
            </div>
            
            <div className="mb-4 flex justify-between items-center">
                <div className="text-sm">
                    {filteredODLs.length} ODL trovati
                    {selectedIds.length > 0 && ` (${selectedIds.length} selezionati)`}
                </div>
                
                <button
                    type="button"
                    onClick={handleToggleAll}
                    className="text-sm px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded border border-gray-300 disabled:opacity-50"
                    disabled={disabled || filteredODLs.length === 0}
                >
                    {filteredODLs.every(odl => selectedIds.includes(odl.id)) 
                        ? 'Deseleziona tutti' 
                        : 'Seleziona tutti'}
                </button>
            </div>
            
            <div className="space-y-2 max-h-80 overflow-y-auto p-1">
                {filteredODLs.length === 0 ? (
                    <div className="text-center text-gray-500 py-4">
                        Nessun ODL trovato con i filtri selezionati
                    </div>
                ) : (
                    filteredODLs.map(odl => (
                        <div
                            key={odl.id}
                            className={`p-3 rounded-md border ${
                                selectedIds.includes(odl.id) 
                                    ? 'border-blue-500 bg-blue-50' 
                                    : 'border-gray-200 hover:border-gray-300 bg-white'
                            } cursor-pointer transition-colors ${disabled ? 'opacity-60' : ''}`}
                            onClick={() => handleToggleSelect(odl.id)}
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center">
                                        <input
                                            type="checkbox"
                                            checked={selectedIds.includes(odl.id)}
                                            onChange={() => {}} // Gestito dal click sul div padre
                                            className="mr-3 h-4 w-4 text-blue-600 rounded"
                                            disabled={disabled}
                                        />
                                        <div>
                                            <div className="font-medium">{odl.parte_nome}</div>
                                            <div className="text-sm text-gray-500">
                                                ID: {odl.id} | Tool: {odl.tool_codice}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div className="ml-4 flex flex-col items-end">
                                    <div className="flex items-center">
                                        <span className="text-sm mr-2">Priorità:</span>
                                        <span className={`font-medium ${
                                            odl.priorita >= 4 ? 'text-red-600' : 
                                            odl.priorita >= 2 ? 'text-yellow-600' : 'text-gray-600'
                                        }`}>
                                            {odl.priorita}
                                        </span>
                                    </div>
                                    <div className="text-sm text-gray-500">
                                        {odl.larghezza}×{odl.lunghezza} mm
                                    </div>
                                </div>
                            </div>
                            
                            <div className="mt-2 flex justify-between text-sm">
                                <div>
                                    <span className="text-gray-500">Ciclo: </span>
                                    <span>{odl.ciclo_cura_nome}</span>
                                </div>
                                <div>
                                    <span className="text-gray-500">Valvole: </span>
                                    <span>{odl.valvole_richieste}</span>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default ODLSelector; 
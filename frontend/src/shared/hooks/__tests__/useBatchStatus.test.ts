import { renderHook, act } from '@testing-library/react';
import { 
  useBatchStatus, 
  useBatchStatusStore,
  isValidTransition,
  getAvailableTransitions,
  isFinalState,
  getStatusColor,
  getStatusLabel,
  BATCH_STATUS_CONFIG,
  STATE_TRANSITIONS,
  BatchStatus
} from '../useBatchStatus';

// Mock React per evitare errori nei test
jest.mock('react', () => ({
  ...jest.requireActual('react'),
  useEffect: jest.fn((fn) => fn())
}));

describe('useBatchStatus State Machine', () => {
  beforeEach(() => {
    // Reset dello store prima di ogni test
    const { reset } = useBatchStatusStore.getState();
    reset();
  });

  describe('State Machine Configuration', () => {
    test('BATCH_STATUS_CONFIG contiene tutti gli stati necessari', () => {
      const expectedStates: BatchStatus[] = [
        'draft', 'sospeso', 'confermato', 'loaded', 'cured', 'terminato', 'annullato'
      ];
      
      expectedStates.forEach(status => {
        expect(BATCH_STATUS_CONFIG[status]).toBeDefined();
        expect(BATCH_STATUS_CONFIG[status].label).toBeTruthy();
        expect(BATCH_STATUS_CONFIG[status].description).toBeTruthy();
        expect(BATCH_STATUS_CONFIG[status].color.hex).toMatch(/^#[0-9a-f]{6}$/i);
        expect(BATCH_STATUS_CONFIG[status].icon).toBeDefined();
      });
    });

    test('STATE_TRANSITIONS definisce transizioni corrette', () => {
      // Verifica che ogni stato abbia una definizione di transizioni
      Object.keys(BATCH_STATUS_CONFIG).forEach(status => {
        expect(STATE_TRANSITIONS[status as BatchStatus]).toBeDefined();
      });

      // Verifica flusso principale: draft → sospeso → confermato → loaded → cured → terminato
      expect(STATE_TRANSITIONS.draft).toContain('sospeso');
      expect(STATE_TRANSITIONS.sospeso).toContain('confermato');
      expect(STATE_TRANSITIONS.confermato).toContain('loaded');
      expect(STATE_TRANSITIONS.loaded).toContain('cured');
      expect(STATE_TRANSITIONS.cured).toContain('terminato');
      
      // Stati finali non hanno transizioni
      expect(STATE_TRANSITIONS.terminato).toEqual([]);
      expect(STATE_TRANSITIONS.annullato).toEqual([]);
    });
  });

  describe('useBatchStatusStore', () => {
    test('store inizializzato con valori corretti', () => {
      const state = useBatchStatusStore.getState();
      
      expect(state.currentStatus).toBe('sospeso');
      expect(state.isTransitioning).toBe(false);
      expect(state.error).toBeNull();
      expect(state.lastTransition).toBeNull();
      expect(state.batchStates).toEqual({});
    });

    test('setCurrentStatus aggiorna lo stato corrente', () => {
      const { setCurrentStatus } = useBatchStatusStore.getState();
      
      act(() => {
        setCurrentStatus('confermato');
      });
      
      expect(useBatchStatusStore.getState().currentStatus).toBe('confermato');
    });

    test('setBatchStatus e getBatchStatus gestiscono batch multipli', () => {
      const { setBatchStatus, getBatchStatus } = useBatchStatusStore.getState();
      
      act(() => {
        setBatchStatus('batch-1', 'confermato');
        setBatchStatus('batch-2', 'loaded');
      });
      
      expect(getBatchStatus('batch-1')).toBe('confermato');
      expect(getBatchStatus('batch-2')).toBe('loaded');
      expect(getBatchStatus('batch-3')).toBeUndefined();
    });
  });

  describe('canTransition validation', () => {
    test('transizioni valide sono permesse', () => {
      const { canTransition } = useBatchStatusStore.getState();
      
      // Transizioni valide secondo la state machine
      expect(canTransition('draft', 'sospeso', 'ADMIN')).toBe(true);
      expect(canTransition('sospeso', 'confermato', 'MANAGER')).toBe(true);
      expect(canTransition('confermato', 'loaded', 'OPERATOR')).toBe(true);
      expect(canTransition('loaded', 'cured', 'OPERATOR')).toBe(true);
      expect(canTransition('cured', 'terminato', 'OPERATOR')).toBe(true);
    });

    test('transizioni non valide sono bloccate', () => {
      const { canTransition } = useBatchStatusStore.getState();
      
      // Transizioni non permesse dalla state machine
      expect(canTransition('draft', 'confermato', 'ADMIN')).toBe(false);
      expect(canTransition('sospeso', 'loaded', 'ADMIN')).toBe(false);
      expect(canTransition('terminato', 'cured', 'ADMIN')).toBe(false);
      expect(canTransition('annullato', 'sospeso', 'ADMIN')).toBe(false);
    });

    test('permessi utente sono verificati', () => {
      const { canTransition } = useBatchStatusStore.getState();
      
      // VIEWER non può fare transizioni
      expect(canTransition('sospeso', 'confermato', 'VIEWER')).toBe(false);
      
      // OPERATOR non può confermare (solo ADMIN/MANAGER)
      expect(canTransition('sospeso', 'confermato', 'OPERATOR')).toBe(false);
      
      // OPERATOR può caricare e gestire cura
      expect(canTransition('confermato', 'loaded', 'OPERATOR')).toBe(true);
      expect(canTransition('loaded', 'cured', 'OPERATOR')).toBe(true);
    });
  });

  describe('transition function', () => {
    test('transizione valida completata con successo', async () => {
      const { transition } = useBatchStatusStore.getState();
      
      const result = await act(async () => {
        return transition('batch-1', 'sospeso', 'confermato', 'ADMIN');
      });
      
      expect(result).toBe(true);
      
      const state = useBatchStatusStore.getState();
      expect(state.getBatchStatus('batch-1')).toBe('confermato');
      expect(state.currentStatus).toBe('confermato');
      expect(state.lastTransition).toEqual({
        from: 'sospeso',
        to: 'confermato',
        label: 'In Sospeso → Confermato',
        requiresConfirmation: true,
        permissions: ['ADMIN', 'MANAGER', 'OPERATOR']
      });
    });

    test('transizione non valida restituisce errore', async () => {
      const { transition } = useBatchStatusStore.getState();
      
      const result = await act(async () => {
        return transition('batch-1', 'draft', 'terminato', 'ADMIN');
      });
      
      expect(result).toBe(false);
      
      const state = useBatchStatusStore.getState();
      expect(state.error).toContain('Transizione non permessa');
      expect(state.getBatchStatus('batch-1')).toBeUndefined();
    });

    test('transizione senza permessi restituisce errore', async () => {
      const { transition } = useBatchStatusStore.getState();
      
      const result = await act(async () => {
        return transition('batch-1', 'sospeso', 'confermato', 'VIEWER');
      });
      
      expect(result).toBe(false);
      
      const state = useBatchStatusStore.getState();
      expect(state.error).toContain('Transizione non permessa');
    });
  });

  describe('getValidTransitions', () => {
    test('restituisce transizioni valide per ruolo', () => {
      const { getValidTransitions } = useBatchStatusStore.getState();
      
      // ADMIN può fare tutte le transizioni disponibili
      const adminTransitions = getValidTransitions('sospeso', 'ADMIN');
      expect(adminTransitions).toContain('confermato');
      expect(adminTransitions).toContain('annullato');
      
      // VIEWER non può fare transizioni
      const viewerTransitions = getValidTransitions('sospeso', 'VIEWER');
      expect(viewerTransitions).toEqual([]);
    });

    test('restituisce array vuoto per stati finali', () => {
      const { getValidTransitions } = useBatchStatusStore.getState();
      
      expect(getValidTransitions('terminato', 'ADMIN')).toEqual([]);
      expect(getValidTransitions('annullato', 'ADMIN')).toEqual([]);
    });
  });

  describe('useBatchStatus hook', () => {
    test('hook inizializzato correttamente senza batchId', () => {
      const { result } = renderHook(() => useBatchStatus());
      
      expect(result.current.state).toBe('sospeso');
      expect(result.current.statusInfo.label).toBe('In Sospeso');
      expect(result.current.label()).toBe('In Sospeso');
      expect(result.current.color().hex).toBe('#f59e0b');
    });

    test('hook inizializzato correttamente con batchId', () => {
      const { result } = renderHook(() => useBatchStatus('batch-1', 'confermato'));
      
      expect(result.current.state).toBe('confermato');
      expect(result.current.statusInfo.label).toBe('Confermato');
    });

    test('canTransition funziona correttamente', () => {
      const { result } = renderHook(() => useBatchStatus('batch-1', 'sospeso'));
      
      expect(result.current.canTransition('confermato', 'ADMIN')).toBe(true);
      expect(result.current.canTransition('loaded', 'ADMIN')).toBe(false);
      expect(result.current.canTransition('confermato', 'VIEWER')).toBe(false);
    });

    test('transition senza batchId mostra warning', async () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      const { result } = renderHook(() => useBatchStatus());
      
      await act(async () => {
        await result.current.transition('confermato', 'ADMIN');
      });
      
      expect(consoleSpy).toHaveBeenCalledWith('useBatchStatus: batchId non fornito per la transizione');
      consoleSpy.mockRestore();
    });
  });

  describe('Utility Functions', () => {
    test('isValidTransition verifica transizioni correttamente', () => {
      expect(isValidTransition('draft', 'sospeso')).toBe(true);
      expect(isValidTransition('sospeso', 'confermato')).toBe(true);
      expect(isValidTransition('draft', 'terminato')).toBe(false);
      expect(isValidTransition('terminato', 'sospeso')).toBe(false);
    });

    test('getAvailableTransitions restituisce transizioni disponibili', () => {
      expect(getAvailableTransitions('draft')).toEqual(['sospeso', 'annullato']);
      expect(getAvailableTransitions('terminato')).toEqual([]);
      expect(getAvailableTransitions('sospeso')).toEqual(['confermato', 'annullato']);
    });

    test('isFinalState identifica stati finali', () => {
      expect(isFinalState('terminato')).toBe(true);
      expect(isFinalState('annullato')).toBe(true);
      expect(isFinalState('sospeso')).toBe(false);
      expect(isFinalState('confermato')).toBe(false);
    });

    test('getStatusColor restituisce colore hex', () => {
      expect(getStatusColor('draft')).toBe('#fbbf24');
      expect(getStatusColor('sospeso')).toBe('#f59e0b');
      expect(getStatusColor('confermato')).toBe('#10b981');
      expect(getStatusColor('invalid_status' as BatchStatus)).toBe('#6b7280');
    });

    test('getStatusLabel restituisce etichetta corretta', () => {
      expect(getStatusLabel('draft')).toBe('Bozza');
      expect(getStatusLabel('sospeso')).toBe('In Sospeso');
      expect(getStatusLabel('confermato')).toBe('Confermato');
      expect(getStatusLabel('invalid_status' as BatchStatus)).toBe('invalid_status');
    });
  });

  describe('Edge Cases e Error Handling', () => {
    test('clearError pulisce gli errori', () => {
      const { clearError } = useBatchStatusStore.getState();
      
      // Imposta un errore manualmente
      act(() => {
        useBatchStatusStore.setState({ error: 'Test error' });
      });
      
      expect(useBatchStatusStore.getState().error).toBe('Test error');
      
      act(() => {
        clearError();
      });
      
      expect(useBatchStatusStore.getState().error).toBeNull();
    });

    test('reset ripristina stato iniziale', () => {
      const { reset, setBatchStatus, setCurrentStatus } = useBatchStatusStore.getState();
      
      // Modifica lo stato
      act(() => {
        setCurrentStatus('confermato');
        setBatchStatus('batch-1', 'loaded');
        useBatchStatusStore.setState({ error: 'Test error' });
      });
      
      // Verifica che lo stato sia cambiato
      expect(useBatchStatusStore.getState().currentStatus).toBe('confermato');
      expect(useBatchStatusStore.getState().batchStates['batch-1']).toBe('loaded');
      expect(useBatchStatusStore.getState().error).toBe('Test error');
      
      // Reset
      act(() => {
        reset();
      });
      
      // Verifica stato iniziale
      const state = useBatchStatusStore.getState();
      expect(state.currentStatus).toBe('sospeso');
      expect(state.batchStates).toEqual({});
      expect(state.error).toBeNull();
      expect(state.lastTransition).toBeNull();
    });

    test('getStatusInfo gestisce stati non validi con fallback', () => {
      const { getStatusInfo } = useBatchStatusStore.getState();
      
      // Stato valido
      const validInfo = getStatusInfo('sospeso');
      expect(validInfo.label).toBe('In Sospeso');
      
      // Lo store dovrebbe sempre avere tutti gli stati definiti
      // ma testiamo il comportamento se qualcosa dovesse mancare
      expect(() => getStatusInfo('invalid' as BatchStatus)).not.toThrow();
    });
  });

  describe('Comprehensive State Transition Tests', () => {
    const testAllValidTransitions = [
      { from: 'draft', to: 'sospeso', role: 'ADMIN' },
      { from: 'draft', to: 'annullato', role: 'ADMIN' },
      { from: 'sospeso', to: 'confermato', role: 'MANAGER' },
      { from: 'sospeso', to: 'annullato', role: 'MANAGER' },
      { from: 'confermato', to: 'loaded', role: 'OPERATOR' },
      { from: 'confermato', to: 'annullato', role: 'ADMIN' },
      { from: 'loaded', to: 'cured', role: 'OPERATOR' },
      { from: 'loaded', to: 'annullato', role: 'ADMIN' },
      { from: 'cured', to: 'terminato', role: 'OPERATOR' }
    ];

    test.each(testAllValidTransitions)(
      'transizione valida $from → $to con ruolo $role',
      async ({ from, to, role }) => {
        const { transition } = useBatchStatusStore.getState();
        
        const result = await act(async () => {
          return transition(`batch-${from}-${to}`, from as BatchStatus, to as BatchStatus, role);
        });
        
        expect(result).toBe(true);
        expect(useBatchStatusStore.getState().getBatchStatus(`batch-${from}-${to}`)).toBe(to);
      }
    );

    const testInvalidTransitions = [
      { from: 'draft', to: 'confermato', role: 'ADMIN', reason: 'skip state' },
      { from: 'sospeso', to: 'loaded', role: 'ADMIN', reason: 'skip state' },
      { from: 'terminato', to: 'cured', role: 'ADMIN', reason: 'reverse transition' },
      { from: 'annullato', to: 'sospeso', role: 'ADMIN', reason: 'reverse transition' },
      { from: 'sospeso', to: 'confermato', role: 'VIEWER', reason: 'insufficient permissions' }
    ];

    test.each(testInvalidTransitions)(
      'transizione non valida $from → $to ($reason)',
      async ({ from, to, role }) => {
        const { transition } = useBatchStatusStore.getState();
        
        const result = await act(async () => {
          return transition(`batch-invalid-${from}-${to}`, from as BatchStatus, to as BatchStatus, role);
        });
        
        expect(result).toBe(false);
        expect(useBatchStatusStore.getState().error).toBeTruthy();
      }
    );
  });
});

describe('Performance and Memory Tests', () => {
  test('gestione di molti batch contemporaneamente', () => {
    const { setBatchStatus, getBatchStatus } = useBatchStatusStore.getState();
    const numBatches = 1000;
    
    // Imposta molti batch
    act(() => {
      for (let i = 0; i < numBatches; i++) {
        setBatchStatus(`batch-${i}`, 'sospeso');
      }
    });
    
    // Verifica che tutti siano stati impostati
    for (let i = 0; i < numBatches; i++) {
      expect(getBatchStatus(`batch-${i}`)).toBe('sospeso');
    }
    
    // Verifica che il numero di stati sia corretto
    expect(Object.keys(useBatchStatusStore.getState().batchStates)).toHaveLength(numBatches);
  });
}); 
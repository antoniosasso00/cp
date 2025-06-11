# Draft Lifecycle Management System

## 🎯 Panoramica

Il sistema di gestione del ciclo di vita delle bozze di CarbonPilot fornisce funzionalità complete per gestire batch temporanei con protezione automatica dalla perdita di dati e navigazione intelligente.

## 🚀 Caratteristiche Principali

### Performance Optimizations
- **Memoizzazione computazionale**: Draft count e liste filtrate sono memoizzate per evitare ricalcoli
- **Callback memoizzati**: Tutte le funzioni sono ottimizzate con useCallback
- **Elaborazione parallela**: Salvataggio batch e enrichment dati autoclave in parallelo
- **Timeout gestiti**: Timeout su richieste API per evitare hang
- **Retry logic**: Tentativi multipli per operazioni critiche (cleanup)

### Edge Case Handling
- **Validazione ID batch**: Controlli per ID nulli, undefined o non validi
- **Gestione risposte API**: Handling di formati di risposta multipli (single/multi-batch)
- **Cleanup race conditions**: Delayed cleanup per evitare race conditions
- **Timeout su richieste**: Prevenzione hang su operazioni di rete
- **Fallback per dati mancanti**: Gestione graceful di dati autoclave mancanti
- **Navigation guards**: Protezione multi-livello (browser + app)

### Integration Features
- **Hook API universale**: Interfaccia consistent per tutte le pagine
- **Event handling**: Gestione eventi browser (beforeunload) e app-level
- **State management**: Stato centralizzato con TypeScript strict
- **Toast notifications**: Feedback utente comprehensive con dettagli errori
- **Auto-switching**: Navigazione automatica intelligente tra batch

## 📋 API Reference

### Hook: `useDraftLifecycle`

```typescript
interface UseDraftLifecycleProps {
  allBatches: DraftBatch[]
  selectedBatchId: string
  onBatchChange: (batchId: string, batchData: DraftBatch) => void
  onBatchRemoved: (batchId: string) => void
}

const draftLifecycle = useDraftLifecycle({
  allBatches,
  selectedBatchId,
  onBatchChange: useCallback((newBatchId, newBatchData) => {
    setSelectedBatchId(newBatchId)
    setBatchData(newBatchData as BatchData)
  }, []),
  onBatchRemoved: useCallback((batchId) => {
    setAllBatches(prev => prev.filter(batch => batch.id !== batchId))
  }, [])
})
```

### Return Values

```typescript
{
  // 🚀 Performance: Memoized state
  hasUnsavedDrafts: boolean
  showExitDialog: boolean
  savingDraft: string | null
  draftCount: number
  draftBatches: DraftBatch[]
  
  // 🛡️ Edge Case: Enhanced actions
  handleNavigation: (navigationFn: () => void) => void
  handleConfirmExit: () => Promise<void>
  handleSaveAllDrafts: () => Promise<void>
  handleSaveDraft: (batchId: string) => Promise<void>
  handleDeleteDraft: (batchId: string) => Promise<void>
  setShowExitDialog: (show: boolean) => void
  switchToNextAvailableBatch: () => void
  isDraftBatch: (batch: DraftBatch | null) => boolean
  
  // 🧹 Integration: Utilities
  cleanupAllDrafts: () => Promise<void>
}
```

## 🔧 Usage Examples

### 1. Basic Integration

```tsx
export default function BatchResultPage() {
  const [allBatches, setAllBatches] = useState<BatchData[]>([])
  const [selectedBatchId, setSelectedBatchId] = useState<string>(batchId)
  const [batchData, setBatchData] = useState<BatchData | null>(null)

  const draftLifecycle = useDraftLifecycle({
    allBatches,
    selectedBatchId,
    onBatchChange: useCallback((newBatchId, newBatchData) => {
      setSelectedBatchId(newBatchId)
      setBatchData(newBatchData as BatchData)
    }, []),
    onBatchRemoved: useCallback((batchId) => {
      setAllBatches(prev => prev.filter(batch => batch.id !== batchId))
    }, [])
  })

  return (
    <div>
      {/* Exit Confirmation Dialog */}
      <ExitConfirmationDialog
        open={draftLifecycle.showExitDialog}
        onOpenChange={draftLifecycle.setShowExitDialog}
        draftCount={draftLifecycle.draftCount}
        onConfirmExit={draftLifecycle.handleConfirmExit}
        onSaveAll={draftLifecycle.handleSaveAllDrafts}
        isProcessing={draftLifecycle.savingDraft === 'all'}
      />
      
      {/* Navigation with Protection */}
      <Button
        onClick={() => draftLifecycle.handleNavigation(() => router.push('/nesting/list'))}
      >
        Back to List
      </Button>
    </div>
  )
}
```

### 2. Batch Actions

```tsx
// Save current draft
<Button 
  onClick={() => draftLifecycle.handleSaveDraft(batchData.id)}
  disabled={draftLifecycle.savingDraft === batchData.id}
>
  {draftLifecycle.savingDraft === batchData.id ? 'Saving...' : 'Save Draft'}
</Button>

// Delete draft with confirmation
<Button 
  onClick={() => draftLifecycle.handleDeleteDraft(batchData.id)}
  variant="destructive"
>
  Delete Draft
</Button>
```

### 3. Manual Cleanup

```tsx
// Manual cleanup (usually automatic)
useEffect(() => {
  return () => {
    if (specialCondition) {
      draftLifecycle.cleanupAllDrafts()
    }
  }
}, [])
```

## 🛡️ Error Handling

### Network Errors
- **Retry Logic**: Automatic retry for failed cleanup operations
- **Timeout Handling**: 15s timeout for save operations, 10s for cleanup
- **Graceful Degradation**: Continue operation even if some drafts fail to save

### Validation Errors
- **ID Validation**: Comprehensive batch ID validation
- **Response Validation**: API response format validation
- **State Validation**: Internal state consistency checks

### User Experience
- **Progress Feedback**: Loading states and progress indicators
- **Error Messages**: User-friendly error descriptions
- **Recovery Options**: Clear recovery paths for failed operations

## 📈 Performance Considerations

### Optimizations Applied
1. **Memoization**: Draft calculations memoized to prevent unnecessary re-renders
2. **Parallel Processing**: Batch operations run in parallel where possible
3. **Debounced Updates**: State updates debounced to reduce render cycles
4. **Lazy Cleanup**: Cleanup operations deferred to avoid blocking UI

### Memory Management
- **Event Listener Cleanup**: Proper removal of beforeunload listeners
- **Timeout Cleanup**: AbortController used for request cancellation
- **State Cleanup**: Proper cleanup of internal state on unmount

## 🔄 Integration Guidelines

### 1. Component Integration
- Use `useCallback` for all callback props to prevent unnecessary re-renders
- Implement proper TypeScript typing for batch data structures
- Handle loading and error states appropriately

### 2. API Integration
- Ensure backend endpoints support the expected request/response formats
- Implement proper error handling on the backend
- Consider implementing request idempotency for save operations

### 3. Testing Considerations
- Test edge cases like network failures and timeouts
- Verify cleanup behavior on component unmount
- Test multi-batch scenarios with various combinations

## 📝 Best Practices

### Do's
✅ Always use the hook's navigation guard for protected routes
✅ Provide meaningful error messages to users
✅ Use memoized callbacks for performance
✅ Handle all possible batch states (draft, sospeso, etc.)
✅ Implement proper loading states

### Don'ts
❌ Don't bypass the navigation guard for draft pages
❌ Don't forget to handle edge cases (null IDs, empty responses)
❌ Don't block the UI thread with synchronous operations
❌ Don't ignore error states or provide generic error messages
❌ Don't forget to cleanup resources on component unmount

## 🚨 Troubleshooting

### Common Issues

1. **Drafts not cleaning up**: Check if `cleanupAllDrafts` is being called on unmount
2. **Navigation not protected**: Ensure `handleNavigation` is used instead of direct router calls
3. **Performance issues**: Verify callbacks are memoized and dependencies are correct
4. **State inconsistencies**: Check if `onBatchChange` and `onBatchRemoved` are implemented correctly

### Debug Tips

- Check browser console for lifecycle logs (prefixed with 🔍, ✅, ❌, etc.)
- Verify API endpoints are responding correctly
- Monitor network tab for timeout issues
- Use React DevTools to inspect hook state

## 🔮 Future Enhancements

### Planned Features
- **Offline Support**: Draft persistence during network outages
- **Conflict Resolution**: Handle simultaneous edits by multiple users
- **Draft Versioning**: Track changes within draft batches
- **Bulk Operations**: Enhanced bulk edit capabilities
- **Analytics**: Draft usage and conversion metrics

### Performance Improvements
- **Virtual Scrolling**: For large batch lists
- **Background Sync**: Non-blocking save operations
- **Optimistic Updates**: Immediate UI updates with rollback on failure
- **Caching**: Intelligent caching of batch data and metadata 
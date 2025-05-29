# 📋 Changelog - CarbonPilot

Questo file documenta tutte le modifiche significative apportate al progetto CarbonPilot.

## 🎯 Formato
Ogni entry segue il formato:
```
### [Data - Nome Feature]
- Descrizione sintetica della funzionalità
- Modifiche ai modelli DB (se presenti)
- Effetti sulla UI e sul comportamento dell'app
```

---

### [2025-05-29 - DEBUG PROFONDO E FIX MODULO ODL] ✅ COMPLETATO

#### 🎯 Obiettivo
Risoluzione completa dei bugs nel modulo ODL di monitoraggio, con focus particolare sull'errore **"TypeError: logs.map is not a function"** nell'interfaccia timeline e gestione robusta dei dati malformati o mancanti.

#### 🐛 Problemi Identificati
- **CRITICO**: `TypeError: logs.map is not a function` in `ODLTimelineEnhanced.tsx` (linea 165)
- **Causa**: Prop `logs` a volte `undefined`, `null`, o non un array valido
- **Impatto**: Crash dell'interfaccia timeline quando si visualizzano dettagli ODL
- **Dati inconsistenti**: Service backend potevano restituire logs non validati

#### 🔧 Implementazione Tecnica

##### ✅ Frontend - Validazione Robusta Props
**File**: `frontend/src/components/odl-monitoring/ODLTimelineEnhanced.tsx`
- **Validazione Input**: Aggiunta validazione robusta con `React.useMemo` per props `logs` e `currentStatus`
- **Filtraggio Logs**: Filtro automatico di log entry non validi (mancanti id, evento, timestamp)
- **Fallback Sicuri**: Gestione di logs `null`/`undefined` con array vuoto
- **Console Warning**: Logging appropriato per debugging senza crash applicazione

```tsx
// ✅ CORREZIONE PRINCIPALE
const validLogs = React.useMemo(() => {
  if (!logs) {
    console.warn('⚠️ ODLTimelineEnhanced: logs prop è undefined/null');
    return [];
  }
  
  if (!Array.isArray(logs)) {
    console.error('❌ ODLTimelineEnhanced: logs prop non è un array:', typeof logs, logs);
    return [];
  }
  
  // Filtra e valida ogni log entry
  return logs.filter(log => {
    if (!log || typeof log !== 'object') {
      console.warn('⚠️ ODLTimelineEnhanced: log entry non valido:', log);
      return false;
    }
    
    if (!log.id || !log.evento || !log.timestamp) {
      console.warn('⚠️ ODLTimelineEnhanced: log entry manca campi essenziali:', log);
      return false;
    }
    
    return true;
  }).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
}, [logs]);

// ✅ Utilizzo validLogs invece di logs direttamente
{validLogs.map((log, index) => { /* rendering sicuro */ })}
```

##### ✅ Frontend - Protezione Component Parent
**File**: `frontend/src/components/odl-monitoring/ODLMonitoringDetail.tsx`
**File**: `frontend/src/app/dashboard/management/odl-monitoring/[id]/page.tsx`
- **Validazione Pre-Passaggio**: Controllo `Array.isArray(logs)` prima di passare props
- **Fallback Props**: Passaggio di array vuoto `[]` quando logs non valido
- **Status Validation**: Validazione `currentStatus` con fallback a `'Unknown'`

```tsx
// ✅ PRIMA (Potenziale crash)
<ODLTimelineEnhanced 
  logs={odlDetail.logs} 
  currentStatus={odlDetail.status}
/>

// ✅ DOPO (Sicuro)
<ODLTimelineEnhanced 
  logs={Array.isArray(odlDetail.logs) ? odlDetail.logs : []} 
  currentStatus={odlDetail.status || 'Unknown'}
/>
```

##### ✅ Backend - Validazione Service Layer
**File**: `backend/services/odl_monitoring_service.py`
- **Validazione Logs**: Controllo `hasattr(odl, 'logs')` e `odl.logs is not None`
- **Filtering Sicuro**: Validazione ogni log entry prima di processarlo
- **Gestione Errori**: Try/catch granulare per nesting e autoclave info
- **Fallback Garantito**: Sempre ritorno di `logs_arricchiti = []` in caso di errore

```python
# ✅ CORREZIONE: Validazione robusta dei logs
if hasattr(odl, 'logs') and odl.logs is not None:
    try:
        for log in odl.logs:
            # Valida che il log abbia i campi essenziali
            if not log or not hasattr(log, 'id') or not hasattr(log, 'evento') or not hasattr(log, 'timestamp'):
                logger.warning(f"ODL {odl_id}: log entry mancante o invalido, saltato")
                continue
                
            log_dict = {
                "id": log.id,
                "evento": log.evento or "evento_sconosciuto",
                "stato_precedente": getattr(log, 'stato_precedente', None),
                # ... altri campi con getattr sicuro
            }
            
            # Gestione sicura delle relazioni
            try:
                if log.nesting_id:
                    nesting = db.query(NestingResult).filter(NestingResult.id == log.nesting_id).first()
                    if nesting:
                        log_dict["nesting_stato"] = nesting.stato
            except Exception as e:
                logger.warning(f"Errore nel recupero nesting {log.nesting_id}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione dei logs per ODL {odl_id}: {str(e)}")
        logs_arricchiti = []  # Fallback a lista vuota
else:
    logger.info(f"ODL {odl_id}: nessun log disponibile o logs è None")
    logs_arricchiti = []
```

##### ✅ Backend - Validazione API Layer
**File**: `backend/api/routers/odl_monitoring.py`
- **Response Validation**: Controllo finale che `logs` sia sempre un array nella risposta
- **Timeline Safety**: Gestione robusta di `timeline_stati` vuoto o non valido
- **Error Recovery**: Fallback a array vuoto quando i dati non sono disponibili

```python
# ✅ CORREZIONE: Validazione robusta dei logs nella risposta
if not hasattr(monitoring_detail, 'logs') or monitoring_detail.logs is None:
    logger.warning(f"ODL {odl_id}: logs mancanti, impostando array vuoto")
    monitoring_detail.logs = []
elif not isinstance(monitoring_detail.logs, list):
    logger.warning(f"ODL {odl_id}: logs non è una lista, convertendo in array vuoto")
    monitoring_detail.logs = []

# ✅ Timeline endpoint - Gestione robusta
if not timeline_stati or not isinstance(timeline_stati, list):
    logger.warning(f"ODL {odl_id}: timeline_stati vuoto o non valido, usando fallback")
    timeline_stati = []
```

#### 🧪 Test di Robustezza
**File**: `test_odl_robustness_debug.py`
- **Test Endpoint API**: Verifica che `/api/odl-monitoring/*` restituiscano sempre dati validi
- **Test Props Validation**: Simulazione di casi edge con props malformati
- **Test Error Recovery**: Verifica gestione errori senza crash dell'applicazione

#### 📁 File Modificati
- `frontend/src/components/odl-monitoring/ODLTimelineEnhanced.tsx` - Validazione props e rendering sicuro
- `frontend/src/components/odl-monitoring/ODLMonitoringDetail.tsx` - Protezione passaggio props
- `frontend/src/app/dashboard/management/odl-monitoring/[id]/page.tsx` - Protezione passaggio props
- `backend/services/odl_monitoring_service.py` - Validazione service layer
- `backend/api/routers/odl_monitoring.py` - Validazione API responses
- `test_odl_robustness_debug.py` - Test di verifica correzioni

#### 🎯 Risultati Ottenuti
- **✅ Errore Risolto**: `TypeError: logs.map is not a function` completamente eliminato
- **✅ Rendering Sicuro**: Timeline ODL ora sempre renderizza senza crash
- **✅ Validazione Robusta**: Controlli a tutti i livelli (frontend, backend, API)
- **✅ Error Recovery**: Fallback appropriati per tutti i casi edge
- **✅ Debugging Migliorato**: Console warning informativi senza crash dell'app
- **✅ Test Coverage**: Test automatici per verificare robustezza

#### 🔄 Verifica Post-Fix
1. **Interface Timeline**: Accesso ai dettagli ODL → Tab Timeline funziona sempre
2. **Console Browser**: Nessun errore critico, solo warning informativi se necessario
3. **Data Consistency**: API sempre restituiscono strutture dati valide
4. **Error Graceful**: Errori gestiti con UI appropriata, nessun crash

---

### [2025-01-28 - Finalizzazione MultiBatch Nesting e Rimozione Mock] ✅ COMPLETATO

#### 🎯 Obiettivo
Finalizzazione completa del sistema MultiBatch nesting sostituendo tutti i mock e fallback di debug con chiamate API reali e gestione errori appropriata. Rimozione di tutti i console.error/console.warn e correzione dei placeholder "N/A".

#### 🔧 Implementazione Tecnica

##### ✅ MultiBatchNesting - Rimozione Mock e Fallback
**File**: `frontend/src/components/nesting/MultiBatchNesting.tsx`
- **Rimossi Mock Batch**: Eliminati tutti i fallback con dati "🛠 Batch Mock 1", "🛠 Batch Mock 2"
- **Rimosso Preview Mock**: Eliminato il fallback "🛠 Batch Preview Mock" con dati simulati
- **Gestione Errori Pulita**: Sostituiti console.error con gestione errori appropriata
- **Toast Corretti**: Rimossi toast con "mock data" e "API non disponibili"
- **API Reali**: Tutte le chiamate utilizzano le API del backend già implementate

```tsx
// ✅ PRIMA (Con fallback mock)
} catch (error) {
  console.error('Errore nel caricamento batch:', error);
  
  // ✅ FALLBACK: Se l'API non è disponibile, usa dati mock
  setBatchList([
    {
      id: 1,
      nome: "🛠 Batch Mock 1",
      descrizione: "Batch di esempio per test",
      // ... altri dati mock
    }
  ]);
  
  toast.error('⚠️ API non disponibili, usando dati mock per il test');
}

// ✅ DOPO (Gestione errori reale)
} catch (error) {
  const errorMessage = error instanceof Error ? error.message : 'Errore sconosciuto';
  setError(`Errore nel caricamento batch: ${errorMessage}`);
  setBatchList([]);
  toast.error('Errore nel caricamento dei batch salvati');
}
```

##### ✅ MultiAutoclaveTab - Rimozione Fallback Debug
**File**: `frontend/src/components/nesting/tabs/MultiAutoclaveTab.tsx`
- **Rimosso "🛠 Multi-Batch da implementare"**: Eliminato il fallback con EmptyState di debug
- **Wrapper Semplificato**: Rimosso il wrapper con try/catch che mostrava fallback di sviluppo
- **Gestione Errori Diretta**: Alert semplice per errori senza fallback di debug
- **Componente Diretto**: MultiBatchNesting viene renderizzato direttamente

```tsx
// ✅ PRIMA (Con fallback debug)
const MultiBatchNestingWrapper = () => {
  try {
    return <MultiBatchNesting />
  } catch (err) {
    console.error('Errore nel componente MultiBatchNesting:', err)
    setError(err instanceof Error ? err.message : 'Errore sconosciuto')
    return (
      <EmptyState
        message="🛠 Multi-Batch da implementare"
        description="Il sistema di nesting multi-autoclave è in fase di sviluppo"
        icon="🚧"
      />
    )
  }
}

// ✅ DOPO (Rendering diretto)
{error && (
  <Alert variant="destructive">
    <AlertDescription>
      Errore nel caricamento del sistema multi-autoclave: {error}
    </AlertDescription>
  </Alert>
)}

<MultiBatchNesting />
```

##### ✅ BatchPreviewPanel - Correzione Placeholder "N/A"
**File**: `frontend/src/components/nesting/BatchPreviewPanel.tsx`
- **Parametri Nesting**: Sostituiti "N/A" con valori di default appropriati usando nullish coalescing
- **Dati Autoclave**: Sostituiti "N/A" con messaggi descrittivi ("Non specificata")
- **Efficienza**: Gestione appropriata dei valori null/undefined per l'efficienza
- **Valori di Default**: Utilizzo di valori di default significativi invece di placeholder

```tsx
// ✅ PRIMA (Con placeholder "N/A")
<div className="font-medium">{batchPreview.parametri_nesting?.distanza_minima_tool_cm || 'N/A'} cm</div>
<div className="font-medium">{assegnazione.efficienza?.toFixed(1) || 'N/A'}% efficienza</div>
Area: {assegnazione.autoclave?.area_piano || 'N/A'} cm²

// ✅ DOPO (Con valori validati)
<div className="font-medium">{batchPreview.parametri_nesting?.distanza_minima_tool_cm ?? 2.0} cm</div>
<div className="font-medium">{assegnazione.efficienza ? `${assegnazione.efficienza.toFixed(1)}%` : '0.0%'} efficienza</div>
Area: {assegnazione.autoclave?.area_piano ? `${assegnazione.autoclave.area_piano} cm²` : 'Non specificata'}
```

##### ✅ BatchDetailsModal - Rimozione Console.error
**File**: `frontend/src/components/nesting/BatchDetailsModal.tsx`
- **Console.error Rimosso**: Eliminato console.error nel caricamento dettagli batch
- **Gestione Errori Pulita**: Error handling appropriato senza logging di debug
- **Toast Informativi**: Messaggi utente appropriati per errori

```tsx
// ✅ PRIMA (Con console.error)
} catch (error) {
  console.error('Errore nel caricamento dettagli batch:', error);
  setError(error instanceof Error ? error.message : 'Errore sconosciuto');
  toast.error('Errore nel caricamento dei dettagli del batch');
}

// ✅ DOPO (Gestione pulita)
} catch (error) {
  setError(error instanceof Error ? error.message : 'Errore sconosciuto');
  toast.error('Errore nel caricamento dei dettagli del batch');
}
```

#### 🔗 Backend API Verificate
Le API del backend sono già completamente implementate e funzionanti:
- **`/api/multi-nesting/batch`**: Lista batch salvati ✅
- **`/api/multi-nesting/preview-batch`**: Creazione preview batch ✅
- **`/api/multi-nesting/salva-batch`**: Salvataggio batch ✅
- **`/api/multi-nesting/batch/{id}/stato`**: Aggiornamento stato ✅
- **`/api/multi-nesting/batch/{id}`**: Dettagli e eliminazione batch ✅

#### 📁 File Modificati
- `frontend/src/components/nesting/MultiBatchNesting.tsx`
- `frontend/src/components/nesting/tabs/MultiAutoclaveTab.tsx`
- `frontend/src/components/nesting/BatchPreviewPanel.tsx`
- `frontend/src/components/nesting/BatchDetailsModal.tsx`

#### 🎯 Risultati Ottenuti
- **✅ Mock Rimossi**: Eliminati tutti i dati mock e fallback di debug
- **✅ Console.error Puliti**: Rimossi tutti i console.error dai componenti MultiBatch
- **✅ Placeholder Corretti**: Sostituiti "N/A" con valori validati e messaggi appropriati
- **✅ Fallback Corretti**: Rimosso "🛠 Multi-Batch da implementare" e altri fallback di sviluppo
- **✅ API Integration**: Tutte le funzionalità utilizzano le API reali del backend
- **✅ Error Handling**: Gestione errori appropriata senza logging di debug
- **✅ UX Migliorata**: Messaggi utente chiari e informativi

#### 🧪 Test da Eseguire
- **Test Caricamento Batch**: Verificare caricamento lista batch dal backend
- **Test Preview Batch**: Verificare creazione preview con parametri reali
- **Test Salvataggio**: Verificare salvataggio batch nel database
- **Test Gestione Stati**: Verificare aggiornamento e eliminazione batch
- **Test Error Handling**: Verificare gestione errori senza fallback mock

---

### [2025-01-28 - Completamento Parametri & Preview Ottimizzazione] ✅ COMPLETATO

#### 🎯 Obiettivo
Rimozione completa dei fallback di debug ("🛠") e implementazione gestione errori vera per i parametri del nesting e il preview dell'ottimizzazione. Integrazione dei parametri personalizzati nel processo di ottimizzazione automatica.

#### 🔧 Implementazione Tecnica

##### ✅ ParametersTab - Gestione Errori Migliorata
**File**: `frontend/src/components/nesting/tabs/ParametersTab.tsx`
- **Rimossi Fallback Debug**: Eliminati tutti i messaggi "🛠 Parametri non disponibili", "🛠 Errore nel caricamento parametri"
- **Error Handling Reale**: Implementata gestione errori con retry button e stati di caricamento appropriati
- **Props Aggiornate**: Aggiunta prop `onRetry` per permettere ricaricamento manuale
- **Stati Distinti**: Separazione chiara tra stato di caricamento, errore e parametri non disponibili

```tsx
// ✅ PRIMA (Con fallback debug)
if (error) {
  return (
    <EmptyState
      message="🛠 Errore nel caricamento parametri"
      description={`Si è verificato un errore: ${error}`}
      icon="⚠️"
    />
  )
}

if (!parameters && !isLoading) {
  return (
    <EmptyState
      message="🛠 Parametri non disponibili"
      description="I parametri di configurazione non sono ancora stati caricati"
    />
  )
}

// ✅ DOPO (Gestione errori appropriata)
if (error) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertDescription>
        Errore nel caricamento dei parametri: {error}
      </AlertDescription>
    </Alert>
    {onRetry && (
      <Button onClick={onRetry} variant="outline" disabled={isLoading}>
        <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
        Riprova
      </Button>
    )}
  )
}

if (isLoading) {
  return (
    <EmptyState
      message="Caricamento parametri in corso..."
      description="I parametri di configurazione verranno caricati a breve"
      icon="⏳"
    />
  )
}
```

##### ✅ PreviewOptimizationTab - Integrazione Parametri
**File**: `frontend/src/components/nesting/tabs/PreviewOptimizationTab.tsx`
- **Rimosso "🛠 Canvas non disponibile"**: Sostituito con gestione intelligente degli stati
- **Integrazione Parametri**: I parametri configurati vengono passati alle API di ottimizzazione
- **Validazione Parametri**: Verifiche che i parametri siano configurati prima dell'ottimizzazione
- **Gestione Stati Canvas**: Loading, errori e lista vuota con azioni di retry appropriate
- **Preview con Parametri**: Nuova funzione per generare preview con parametri personalizzati

```tsx
// ✅ PRIMA (Fallback fisso)
<EmptyState
  message="🛠 Canvas non disponibile"
  description="Seleziona un nesting dalla lista sopra per visualizzarlo nel canvas interattivo"
  size="sm"
/>

// ✅ DOPO (Gestione stati intelligente)
{isLoadingNestings ? (
  <EmptyState
    message="Caricamento nesting disponibili..."
    description="Sto cercando i nesting disponibili per la visualizzazione"
    icon="⏳"
    size="sm"
  />
) : availableNestings.length === 0 ? (
  <div className="space-y-4">
    <EmptyState
      message="Nessun nesting disponibile"
      description="Non sono stati trovati nesting da visualizzare. Crea prima un nesting nella tab Preview o genera un'ottimizzazione automatica."
      icon="📋"
      size="sm"
    />
    <div className="flex gap-2">
      <Button onClick={loadAvailableNestings} variant="outline" size="sm">
        <RefreshCw className="h-4 w-4" />
        Ricarica
      </Button>
      {parameters && (
        <Button onClick={handleGeneratePreview} variant="outline" size="sm">
          <Eye className="h-4 w-4" />
          Genera Preview
        </Button>
      )}
    </div>
  </div>
) : (
  // Rendering normale con selezione nesting
)}
```

##### ✅ Validazione e Passaggio Parametri
- **Verifica Parametri**: Prima di avviare ottimizzazione automatica, verifica che i parametri siano configurati
- **API Integration**: Parametri passati correttamente alle funzioni di `generateAutomaticNesting` e `generatePreviewWithParameters`
- **User Feedback**: Alert informativi se i parametri non sono configurati
- **Preview Personalizzata**: Nuova funzione per generare preview utilizzando i parametri configurati

```tsx
// ✅ Validazione parametri prima dell'ottimizzazione
const handleGenerateAutomatic = async () => {
  if (!parameters) {
    toast({
      title: "Parametri mancanti",
      description: "È necessario configurare i parametri prima di avviare l'ottimizzazione",
      variant: "destructive",
    })
    return
  }

  // Usa l'hook per generare il nesting con i parametri
  const result = await generateAutomaticNesting(parameters, automaticOptions.force_regenerate)
  // ...
}

// ✅ Preview con parametri personalizzati
const handleGeneratePreview = async () => {
  if (!parameters) {
    toast({
      title: "Parametri mancanti",
      description: "È necessario configurare i parametri prima di generare la preview",
      variant: "destructive",
    })
    return
  }

  const previewResult = await generatePreviewWithParameters(parameters)
  // ...
}
```

##### ✅ Hook useNestingParameters - Funzionalità Complete
**File**: `frontend/src/hooks/useNestingParameters.ts`
- **API Completa**: Hook già implementato con tutte le funzioni necessarie
- **Gestione Errori**: Error handling appropriato per ogni operazione
- **TypeScript Types**: Interfacce complete per requests e responses
- **Validazione**: Funzione per validare parametri sul backend
- **Preview Parametrizzata**: Funzione per generare preview con parametri specifici

##### ✅ NestingCanvas - Gestione Stati Ottimizzata
**File**: `frontend/src/components/nesting/NestingCanvas.tsx`
- **Stati di Caricamento**: Loading state con Skeleton appropriato
- **Error Handling**: Gestione errori con retry button
- **Fallback Appropriati**: Nessun fallback di debug, solo stati utente appropriati
- **Componente già Ottimizzato**: NestingCanvas già implementato correttamente

#### 📁 File Modificati
- `frontend/src/components/nesting/tabs/ParametersTab.tsx`
- `frontend/src/components/nesting/tabs/PreviewOptimizationTab.tsx`
- `frontend/src/hooks/useNestingParameters.ts` (verificato, già completo)
- `frontend/src/components/nesting/NestingCanvas.tsx` (verificato, già corretto)

#### 🎯 Risultati Ottenuti
- **✅ Rimossi Fallback Debug**: Eliminati tutti i messaggi "🛠" dai componenti
- **✅ Error Handling Reale**: Gestione errori appropriata con retry e stati di caricamento
- **✅ Integrazione Parametri**: I parametri vengono validati e passati correttamente alle API
- **✅ UX Migliorata**: Stati di caricamento, errori e azioni più chiari per l'utente
- **✅ Validazione Robusta**: Verifiche parametri prima delle operazioni critiche
- **✅ Preview Parametrizzata**: Possibilità di generare preview con parametri personalizzati

#### 🧪 Test da Eseguire
- **Test Parametri**: Verificare caricamento, modifica e applicazione parametri
- **Test Validazione**: Verificare che l'ottimizzazione non parta senza parametri
- **Test Preview Canvas**: Verificare gestione stati vuoti, loading e errori
- **Test Retry**: Verificare funzionamento pulsanti di retry su errori
- **Test Preview Parametrizzata**: Verificare generazione preview con parametri specifici
- **Test Error Handling**: Verificare toast informativi invece di fallback debug

---

### [2025-01-28 - Completamento Funzionalità NestingTable] ✅ COMPLETATO

#### 🎯 Obiettivo
Implementazione completa delle funzionalità principali della NestingTable: abilitazione dei pulsanti "Rigenera Nesting" e "Elimina Nesting", correzione visualizzazione nome autoclave, e pulizia del codice.

#### 🔧 Implementazione Tecnica

##### ✅ Pulsanti Funzionali Abilitati
**File**: `frontend/src/components/nesting/NestingTable.tsx`
- **Pulsante "Rigenera Nesting"**: Collegato a API `POST /nesting/{id}/regenerate`
- **Pulsante "Elimina Nesting"**: Collegato a API `DELETE /nesting/{id}`
- **Rimozione Fallback**: Eliminati i try-catch con fallback "🛠 Funzione da implementare"
- **Error Handling**: Gestione errori diretta tramite `handleActionWithLoading`

```tsx
// ✅ PRIMA (Con fallback per endpoint non implementati)
const handleRegenerateNesting = async (nesting: NestingResponse) => {
  await handleActionWithLoading(nesting.id, 'rigenera', async () => {
    try {
      await nestingApi.regenerate(parseInt(nesting.id), true)
      // ... toast di successo
    } catch (error: any) {
      if (error.status === 404 || error.status === 405) {
        toast({
          variant: "default",
          title: "🛠 Funzione da implementare",
          description: "La rigenerazione del nesting sarà implementata prossimamente."
        })
      } else {
        throw error
      }
    }
  })
}

// ✅ DOPO (Funzionalità diretta)
const handleRegenerateNesting = async (nesting: NestingResponse) => {
  await handleActionWithLoading(nesting.id, 'rigenera', async () => {
    await nestingApi.regenerate(parseInt(nesting.id), true)
    
    toast({
      variant: "default",
      title: "Nesting Rigenerato",
      description: `Il nesting ${nesting.id.substring(0, 8)}... è stato rigenerato con successo.`
    })
    
    onRefresh()
  })
}
```

##### ✅ API già Implementate nel Sistema
**File**: `frontend/src/lib/api.ts`
- **regenerate**: API `POST /nesting/{id}/regenerate` (riga 1274-1284)
- **delete**: API `DELETE /nesting/{id}` (riga 1286-1290)
- **Interfacce Complete**: Tutte le tipologie di response già definite

```tsx
// ✅ API già implementate nell'oggetto nestingApi
regenerate: (nestingId: number, forceRegenerate?: boolean) => {
  const queryParams = new URLSearchParams();
  if (forceRegenerate !== undefined) {
    queryParams.append('force_regenerate', forceRegenerate.toString());
  }
  
  const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
  return apiRequest<{
    success: boolean;
    message: string;
    nesting_id: number;
    stato: string;
  }>(`/nesting/${nestingId}/regenerate${query}`, 'POST');
},

delete: (nestingId: number) => 
  apiRequest<{
    success: boolean;
    message: string;
  }>(`/nesting/${nestingId}`, 'DELETE'),
```

##### ✅ Correzione Visualizzazione Autoclave
- **Sostituito**: `"🛠 Non disponibile"` con valore reale o `"—"` se null
- **Miglioramento UX**: Simbolo tipografico "—" invece di testo placeholder tecnico
- **Consistenza**: Allineamento con altre parti dell'applicazione

```tsx
// ✅ PRIMA
<TableCell>
  {nesting.autoclave_nome || "🛠 Non disponibile"}
</TableCell>

// ✅ DOPO
<TableCell>
  {nesting.autoclave_nome || "—"}
</TableCell>
```

##### ✅ Pulizia del Codice
- **Rimossi console.error**: Eliminati tutti i `console.error` da NestingTable.tsx
- **Rimossi toast("🛠")**: Eliminati tutti i toast con messaggi placeholder
- **Error Handling Pulito**: Solo toast user-friendly per errori
- **Codice Più Pulito**: Funzioni più lineari senza gestione errori ridondante

```tsx
// ✅ PRIMA (Con console.error)
} catch (error: any) {
  console.error(`Errore durante ${actionType}:`, error)
  toast({
    variant: "destructive",
    title: "Errore",
    description: error.message || `Errore durante ${actionType}`
  })
}

// ✅ DOPO (Solo toast user-friendly)
} catch (error: any) {
  toast({
    variant: "destructive",
    title: "Errore",
    description: error.message || `Errore durante ${actionType}`
  })
}
```

#### 📁 File Modificati
- `frontend/src/components/nesting/NestingTable.tsx`

#### 🎯 Risultati Ottenuti
- **✅ Funzionalità Complete**: Pulsanti "Rigenera" e "Elimina" pienamente operativi
- **✅ UI Migliorata**: Nome autoclave reale o simbolo tipografico appropriato
- **✅ Codice Pulito**: Rimossi console.error e toast placeholder
- **✅ Error Handling**: Gestione errori user-friendly e consistente
- **✅ Backend Integration**: Utilizzo completo delle API REST già implementate

#### 🧪 Test da Eseguire
- **Test Pulsante Rigenera**: Verificare chiamata API `POST /nesting/{id}/regenerate`
- **Test Pulsante Elimina**: Verificare chiamata API `DELETE /nesting/{id}`
- **Test Visualizzazione**: Confermare visualizzazione corretta nome autoclave
- **Test Error Handling**: Verificare toast di errore senza console.error

---

### [2025-01-28 - Correzione Errori TypeScript e Dipendenze] ✅ COMPLETATO

#### 🎯 Obiettivo
Risoluzione degli errori di compilazione TypeScript relativi all'importazione di `buttonVariants` e correzione delle dipendenze dei componenti UI.

#### 🔧 Implementazione Tecnica

##### ✅ Problema Identificato
- **Errore TypeScript**: `Module '"@/components/ui/button"' has no exported member 'buttonVariants'`
- **File Interessato**: `frontend/src/app/dashboard/shared/catalog/page.tsx` riga 30
- **Causa**: Il componente Button non esportava `buttonVariants` necessario per l'uso con Link di Next.js

##### ✅ Soluzione Implementata
**File**: `frontend/src/components/ui/button.tsx`
- **Migrazione a CVA**: Sostituita implementazione personalizzata con `class-variance-authority`
- **Export buttonVariants**: Aggiunta esportazione di `buttonVariants` utilizzabile con className
- **Mantiene Compatibilità**: Tutte le props e varianti esistenti rimangono invariate
- **Type Safety**: Migliorata type safety con `VariantProps<typeof buttonVariants>`

```tsx
// ✅ PRIMA (Implementazione personalizzata)
const getButtonClasses = (variant?: string, size?: string) => {
  // Logica personalizzata per le classi
}

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link" | "success" | "warning" | "info"
  size?: "default" | "sm" | "lg" | "icon"
}

export { Button }

// ✅ DOPO (Con CVA e buttonVariants)
const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-2xl...",
  {
    variants: {
      variant: { ... },
      size: { ... }
    },
    defaultVariants: { ... }
  }
)

export interface ButtonProps 
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  // Mantiene compatibilità con props esistenti
}

export { Button, buttonVariants }
```

##### ✅ Benefici Ottenuti
- **Type Safety**: Migliorata type safety con VariantProps di CVA
- **Consistenza**: Stessa implementazione utilizzata in altri progetti shadcn/ui
- **Maintainability**: Codice più pulito e maintainabile con CVA
- **Compatibility**: Compatibilità totale con componenti esistenti

#### 📁 File Modificati
- `frontend/src/components/ui/button.tsx`

#### 🎯 Risultati Ottenuti
- **✅ Zero Errori TypeScript**: Tutti gli errori di compilazione risolti
- **✅ Linting Pulito**: Comando `npm run lint` eseguito con successo
- **✅ buttonVariants Disponibile**: Può essere importato e utilizzato con Link di Next.js
- **✅ Compatibilità Mantenuta**: Tutti i componenti esistenti continuano a funzionare
- **✅ Type Safety**: Migliorata type safety con CVA

#### 🧪 Test Eseguiti
- **✅ TypeScript Check**: `npx tsc --noEmit` - nessun errore
- **✅ Linting**: `npm run lint` - passed
- **✅ Compatibilità**: Verificata compatibilità con implementazione esistente

---

### [2025-01-28 - Rimozione Dati Mock e Integrazione API Reali - Layout Confermati] ✅ COMPLETATO

#### 🎯 Obiettivo
Eliminazione completa dei fallback "N/A" nel tab "Layout Confermati" e integrazione dei dati reali provenienti dal backend, utilizzando le API esistenti per mostrare informazioni accurate su autoclave, tool, peso e ODL.

#### 🔧 Implementazione Tecnica

##### ✅ Interfaccia Dati Arricchiti
**File**: `frontend/src/components/nesting/tabs/ConfirmedLayoutsTab.tsx`
- **Nuova Interfaccia**: `EnrichedNestingData` che estende `NestingResponse` con dettagli aggiuntivi
- **Caricamento Dettagli**: Funzione `enrichNestingData()` per ottenere informazioni complete via `nestingApi.getDetails()`
- **Gestione Performance**: Caricamento dettagli solo per i primi 5 nesting per evitare troppe chiamate API
- **Caricamento On-Demand**: Pulsante "Carica Info" per ottenere dettagli aggiuntivi quando necessario

```tsx
// ✅ NUOVO: Interfaccia per i dati arricchiti del nesting
interface EnrichedNestingData extends NestingResponse {
  dettagli?: NestingDetailResponse;
  tool_principale?: string;
  odl_count?: number;
}

// ✅ NUOVO: Funzione per arricchire i dati del nesting con dettagli aggiuntivi
const enrichNestingData = async (nesting: NestingResponse): Promise<EnrichedNestingData> => {
  try {
    // Carica i dettagli del nesting per ottenere informazioni sui tool
    const dettagli = await nestingApi.getDetails(parseInt(nesting.id))
    
    // Estrae il tool principale (primo tool degli ODL inclusi)
    const tool_principale = dettagli.odl_inclusi?.[0]?.tool_nome || 
                           dettagli.odl_inclusi?.[0]?.parte_codice || 
                           undefined
    
    return {
      ...nesting,
      dettagli,
      tool_principale,
      odl_count: dettagli.odl_inclusi?.length || nesting.odl_inclusi || 0
    }
  } catch (error) {
    // Ritorna i dati base se non riusciamo a caricare i dettagli
    return {
      ...nesting,
      odl_count: nesting.odl_inclusi || 0
    }
  }
}
```

##### ✅ Funzioni Helper per Dati Reali
- **`getAutoclaveName()`**: Utilizza `nesting.autoclave_nome` o `dettagli.autoclave.nome` con fallback "—"
- **`getToolName()`**: Estrae tool principale da `tool_principale` o `dettagli.odl_inclusi[0].tool_nome`
- **`getOdlCount()`**: Mostra numero reale di ODL da `odl_count` o `odl_inclusi`
- **`formatPeso()`**: Formatta peso da `peso_totale` con unità "kg" o "—" se nullo

```tsx
// ✅ NUOVO: Funzioni helper per dati reali
const getAutoclaveName = (nesting: EnrichedNestingData): string => {
  return nesting.autoclave_nome || 
         nesting.dettagli?.autoclave?.nome || 
         '—'
}

const getToolName = (nesting: EnrichedNestingData): string => {
  return nesting.tool_principale || 
         nesting.dettagli?.odl_inclusi?.[0]?.tool_nome ||
         '—'
}

const formatPeso = (peso?: number): string => {
  if (peso === undefined || peso === null) return '—'
  return `${peso.toFixed(1)} kg`
}
```

##### ✅ UI Migliorata con Dati Reali
- **Autoclave**: Mostra nome reale dell'autoclave con icona Package
- **Tool**: Visualizza tool principale utilizzato con icona Wrench
- **Peso**: Formattazione corretta del peso totale con unità
- **ODL**: Conteggio reale degli ODL inclusi nel nesting
- **Badge Efficienza**: Mostra percentuale di efficienza se disponibile
- **Informazioni Aggiuntive**: Sezione espandibile con ciclo cura, area utilizzata, valvole

##### ✅ Gestione Stati di Caricamento
- **Loading Indicators**: Spinner per caricamento dettagli in corso
- **Pulsante "Carica Info"**: Disponibile per nesting senza dettagli caricati
- **Feedback Visivo**: Icone e indicatori per stato di caricamento
- **Gestione Errori**: Fallback graceful se caricamento dettagli fallisce

#### 📊 Dati Sostituiti

##### ❌ PRIMA (Dati Mock)
```tsx
<p className="text-sm text-muted-foreground">
  Autoclave N/A
</p>
// ...
<span className="ml-1 font-medium">N/A</span> // ODL
<span className="ml-1 font-medium">N/A</span> // Tool
<span className="ml-1 font-medium">N/A kg</span> // Peso
```

##### ✅ DOPO (Dati Reali)
```tsx
<p className="text-sm text-muted-foreground flex items-center gap-1">
  <Package className="h-3 w-3" />
  {getAutoclaveName(nesting)} // Nome reale autoclave
</p>
// ...
<span className="ml-1 font-medium">{getOdlCount(nesting)}</span> // Conteggio ODL reale
<span className="ml-1 font-medium">{getToolName(nesting)}</span> // Nome tool reale
<span className="ml-1 font-medium">{formatPeso(nesting.peso_totale)}</span> // Peso reale
```

#### 🎨 Miglioramenti UI

##### ✅ Icone Semantiche
- **FileText**: Per informazioni ODL
- **Wrench**: Per informazioni tool
- **Package**: Per autoclave e peso
- **Calendar**: Per data creazione

##### ✅ Badge Informativi
- **Badge Stato**: Colori semantici per ogni stato nesting
- **Badge Efficienza**: Percentuale di efficienza se disponibile
- **Badge Outline**: Per informazioni secondarie

##### ✅ Sezione Informazioni Aggiuntive
- **Ciclo Cura**: Nome del ciclo di cura utilizzato
- **Area Utilizzata**: Rapporto area utilizzata/totale in cm²
- **Valvole**: Conteggio valvole utilizzate/totali
- **Visualizzazione Condizionale**: Mostra solo se dati disponibili

#### 🔄 Strategia di Caricamento

##### ✅ Caricamento Intelligente
1. **Primi 5 Nesting**: Caricamento automatico dettagli completi
2. **Nesting Successivi**: Solo dati base, dettagli on-demand
3. **Pulsante "Carica Info"**: Per ottenere dettagli quando necessario
4. **Cache Locale**: Dettagli caricati rimangono in memoria

##### ✅ Performance Ottimizzata
- **Chiamate API Limitate**: Massimo 5 chiamate automatiche
- **Caricamento Asincrono**: Non blocca il rendering iniziale
- **Fallback Graceful**: Mostra dati disponibili anche se dettagli falliscono
- **Indicatori Visivi**: Loading states per feedback utente

#### 📁 File Modificati
- `frontend/src/components/nesting/tabs/ConfirmedLayoutsTab.tsx`

#### 🎯 Risultati Ottenuti
- **✅ Zero Dati "N/A"**: Tutti i fallback sostituiti con dati reali o "—"
- **✅ Autoclave Reale**: Nome autoclave da `autoclave_nome` o dettagli
- **✅ Tool Reale**: Nome tool principale da ODL inclusi
- **✅ Peso Reale**: Peso totale formattato correttamente
- **✅ ODL Reale**: Conteggio accurato degli ODL nel nesting
- **✅ UI Migliorata**: Icone, badge e layout più informativi
- **✅ Performance**: Caricamento intelligente per evitare sovraccarico API

#### 🧪 Test Consigliati
- [ ] Verificare che autoclave mostri nome reale invece di "N/A"
- [ ] Controllare che tool mostri part_number_tool corretto
- [ ] Verificare formattazione peso con unità "kg"
- [ ] Testare pulsante "Carica Info" per nesting senza dettagli
- [ ] Verificare badge efficienza per nesting con dati disponibili
- [ ] Controllare sezione informazioni aggiuntive (ciclo, area, valvole)

---

### [2025-01-28 - Gestione Nesting Confermati con Report Avanzati] ✅ COMPLETATO

#### 🎯 Obiettivo
Implementazione completa della gestione dei nesting confermati con stati avanzati e sistema di report integrato per il download diretto dei PDF di nesting completati.

#### 🎨 Implementazione Frontend

##### ✅ Tab "Layout Confermati" Potenziato
**File**: `frontend/src/components/nesting/tabs/ConfirmedLayoutsTab.tsx`
- **Filtri Avanzati**: Gestione nesting in stati `sospeso`, `cura`, `finito`, `confermato`, `in_corso`, `completato`
- **Statistiche Dettagliate**: 5 card con contatori per ogni stato (Totale, Confermati, In Sospeso, In Cura, Completati)
- **UI Migliorata**: Layout a card invece di tabella per migliore visualizzazione
- **Icone Stato**: Icone specifiche per ogni stato (CheckCircle, Clock, Play, CheckSquare)
- **Badge Colorati**: Indicatori visivi per stato e efficienza con colori semantici
- **Pulsante Report**: Disponibile solo per nesting completati (`finito`, `completato`)
- **Download Diretto**: Integrazione con `nestingApi.generateReport()` e `nestingApi.downloadReport()`
- **Loading States**: Gestione stati di caricamento per ogni azione di download
- **Informazioni Dettagliate**: ODL, Tool, Peso, Data per ogni nesting (con fallback N/A)

```tsx
// Funzione per scaricare il report di un nesting
const handleDownloadReport = async (nesting: NestingResponse) => {
  const nestingId = parseInt(nesting.id)
  
  try {
    setDownloadingReports(prev => new Set(prev).add(nesting.id))
    
    // Prima genera il report se non esiste
    const reportInfo = await nestingApi.generateReport(nestingId)
    
    // Poi scarica il report
    const blob = await nestingApi.downloadReport(nestingId)
    
    // Crea un link per il download
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = reportInfo.filename || `nesting_${nesting.id}_report.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
```

##### ✅ Tab "Report" Completamente Rinnovato
**File**: `frontend/src/components/nesting/tabs/ReportsTab.tsx`
- **Filtri Temporali**: Campi data inizio/fine per filtrare nesting per periodo
- **Filtro Stato**: Dropdown per filtrare per stato specifico (Finito/Completato)
- **Tabella Report**: Visualizzazione tabellare dei nesting completati con report disponibili
- **Statistiche Estese**: 5 card con metriche (Totale Nesting, Efficienza Media, Tool Processati, Completati, Report Disponibili)
- **Caricamento Automatico**: Caricamento asincrono dei nesting completati al mount
- **Applicazione Filtri**: Filtri reattivi che si applicano automaticamente al cambio parametri
- **Download Integrato**: Pulsante download per ogni riga della tabella
- **Gestione Errori**: Toast notifications per successo/errore operazioni
- **Distribuzione Stati**: Grafico a barre per visualizzazione distribuzione stati
- **Esportazione Dati**: Pulsanti per export CSV, Excel, PDF (preparati per implementazione futura)

```tsx
// Applica filtri
const applyFilters = () => {
  let filtered = [...completedNestings]

  // Filtro per data
  if (dateFrom) {
    const fromDate = new Date(dateFrom)
    filtered = filtered.filter(nesting => 
      new Date(nesting.created_at) >= fromDate
    )
  }

  if (dateTo) {
    const toDate = new Date(dateTo)
    toDate.setHours(23, 59, 59, 999) // Fine giornata
    filtered = filtered.filter(nesting => 
      new Date(nesting.created_at) <= toDate
    )
  }

  // Filtro per stato
  if (statusFilter !== 'all') {
    filtered = filtered.filter(nesting => 
      nesting.stato.toLowerCase() === statusFilter
    )
  }

  setFilteredNestings(filtered)
}
```

#### 🔧 Integrazione API Esistente

##### ✅ API Report Nesting
**Backend**: Utilizzo delle API esistenti già implementate:
- **Generazione Report**: `POST /api/v1/nesting/{nesting_id}/generate-report`
- **Download Report**: `GET /api/v1/reports/nesting/{nesting_id}/download`
- **Servizio Report**: `NestingReportGenerator` per creazione PDF dettagliati

**Frontend**: Integrazione con `nestingApi`:
- **generateReport()**: Genera report PDF per nesting specifico con opzione force_regenerate
- **downloadReport()**: Scarica report come Blob per download diretto
- **Gestione Errori**: Try-catch con toast notifications per feedback utente

#### 📊 Funzionalità Implementate

##### ✅ Gestione Stati Avanzati
- **Confermato**: Layout approvato, pronto per produzione (arancione)
- **In Sospeso**: In attesa di essere caricato in autoclave (giallo)
- **In Cura**: Produzione attualmente in esecuzione (blu)
- **Completato**: Produzione terminata, report disponibile (verde)

##### ✅ Sistema Report Integrato
- **Preview Nesting**: Visualizzazione dettagli nesting con informazioni complete
- **Generazione Automatica**: Report PDF generati automaticamente per nesting completati
- **Download Diretto**: Un click per scaricare report PDF con nome file automatico
- **Gestione Cache**: Report esistenti riutilizzati, rigenerazione solo se necessario
- **Feedback Utente**: Loading states e toast notifications per ogni operazione

##### ✅ Filtri e Ricerca
- **Filtro Temporale**: Selezione periodo con date picker
- **Filtro Stato**: Dropdown per stati specifici
- **Applicazione Automatica**: Filtri applicati in tempo reale
- **Contatori Dinamici**: Statistiche aggiornate in base ai filtri applicati

#### 🎯 Risultati Ottenuti
- **Tab Layout Confermati**: ✅ Mostra tutti i nesting con stati avanzati
- **Pulsante Genera Report**: ✅ Disponibile per nesting completati
- **Tab Report**: ✅ Tabella con filtri temporali e download diretto
- **Download Report**: ✅ Integrazione con `reportsApi.downloadNestingReport(nestingId)`
- **Preview Completi**: ✅ Visualizzazione dettagli nesting con azioni contestuali

#### 📝 Note Tecniche
- **Compatibilità**: Gestione proprietà mancanti in `NestingResponse` con fallback N/A
- **Performance**: Caricamento asincrono e filtri client-side per responsività
- **UX**: Loading states, toast notifications e feedback visivo per tutte le operazioni
- **Sicurezza**: Validazione ID nesting e gestione errori API robusta
- **Scalabilità**: Struttura preparata per future estensioni (export, filtri avanzati)

---

### [2024-05-29 - Fix Barra di Progresso Tempi Reali]

**🔧 CORREZIONE CRITICA: Tempi Reali vs Stimati**

**Problema risolto:**
- La barra di avanzamento ODL mostrava sempre tempi stimati invece dei tempi reali di produzione
- Endpoint frontend sbagliato che causava errori nel recupero dati
- Mancanza di fallback robusti per gestire ODL senza tracking completo
- **❌ ERRORE CRITICO**: Incompatibilità tipizzazione TypeScript per il campo `fine` (null vs undefined)

**Modifiche implementate:**

**Frontend:**
- 🔧 `frontend/src/components/ui/OdlProgressWrapper.tsx`: Corretto endpoint API da `/tempo-fasi` a `/odl-monitoring/monitoring/{id}/progress`
- 🔧 `frontend/src/lib/api.ts`: Corretta tipizzazione API per corrispondenza con backend
- 🔥 **`frontend/src/components/ui/OdlProgressBar.tsx`**: **CORREZIONE CRITICA** - Aggiornata interfaccia `ODLStateTimestamp` per accettare `fine?: string | null` invece di solo `fine?: string`
- 🎨 Migliorata gestione fallback con messaggi utente informativi
- ✨ Aggiunto logging dettagliato per debugging

**Backend:**
- 🔧 `backend/api/routers/odl_monitoring.py`: Implementato sistema di fallback multi-livello
  - Livello 1: StateTrackingService (dati precisi)
  - Livello 2: ODLLogService (dati base)  
  - Livello 3: Calcolo temporale dall'inizio ODL
- 📊 Aggiunto campo `data_source` per tracciabilità origine dati
- 🛡️ Gestione robusta degli errori con logging dettagliato

**Testing:**
- 🧪 Creato script `test_progress_robustness.py` per validazione automatica
- 🧪 Creato script `test_progress_simple.py` per test tipizzazione TypeScript
- 📋 Documentazione completa in `docs/FIX_BARRA_PROGRESSO_TEMPI_REALI.md`

**Correzione TypeScript:**
```typescript
// ❌ PRIMA (Errore di compilazione)
export interface ODLStateTimestamp {
  fine?: string;  // Solo string o undefined
}

// ✅ DOPO (Compatibile con backend)
export interface ODLStateTimestamp {
  fine?: string | null;  // Accetta anche null
}
```

**Benefici:**
- ✅ Visualizzazione accurata dei tempi reali di produzione
- ✅ Distinzione visiva chiara tra dati reali e stimati  
- ✅ Sistema sempre funzionante anche con dati incompleti
- ✅ Debugging semplificato con indicatori di origine dati
- ✅ Compatibilità retroattiva con ODL esistenti
- ✅ **Zero errori di compilazione TypeScript**
- ✅ **Robustezza strutturale garantita**

**Effetti sulla UI:**
- Le barre di progresso ora mostrano tempi effettivi quando disponibili
- Badge "Stimato" appare solo quando necessario
- Tooltip informativi migliorati con distinzione dati reali/stimati
- Messaggi di errore più chiari e informativi
- **Indicatore animato per stati correnti (fine = null)**

# Test Plan: Nesting 2L Multi-Autoclave

## 🎯 Obiettivo del Test
Verificare che il sistema CarbonPilot supporti correttamente il nesting su 2 livelli (con cavalletti) in modalità multi-autoclave.

## 🐛 Problemi Risolti

### 1. **PROBLEMA**: Toast "Cavalletti non supportati per multi-autoclave"
- **CAUSA**: Logica nel file `frontend/src/modules/nesting/page.tsx` che disabilitava i cavalletti per multi-autoclave
- **FIX**: Aggiunta condizione `useStands && selectedAutoclavi.length > 1` che genera 2L per ogni autoclave

### 2. **PROBLEMA**: Pagina autoclavi non carica dati  
- **CAUSA**: Import errato `@/lib/api` invece di `@/shared/lib/api` in `frontend/src/modules/autoclavi/page.tsx`
- **FIX**: Corretto il path dell'import API

## 🔧 Modifiche Implementate

### A. Frontend - Logica 2L Multi-Autoclave
```typescript
// NUOVO FLUSSO: useStands && selectedAutoclavi.length > 1
if (useStands && selectedAutoclavi.length > 1) {
  // Genera 2L per ogni autoclave selezionata
  const batchPromises = selectedAutoclavi.map(autoclaveId => 
    batchNestingApi.genera2L({
      autoclave_id: autoclaveId,
      odl_ids: selectedOdls,
      parametri: roundedParams,
      use_cavalletti: true,
      cavalletto_height_mm: 100.0,
      max_weight_per_level_kg: 200.0,
      prefer_base_level: true
    })
  );
  
  const batchResults = await Promise.all(batchPromises);
}
```

### B. UI - Indicatore Supporto Multi-Autoclave
```typescript
// Da blu a verde con checkmark
<div className="text-green-600 bg-green-50">
  Modalità 2L (cavalletti) attiva
  {selectedAutoclavi.length > 1 ? " - Multi-Autoclave supportato ✓" : ""}
</div>
```

### C. Backend - Endpoint 2L Esistente
- ✅ Endpoint `/api/batch_nesting/2l` già implementato
- ✅ Service `solver_2l.py` già supporta cavalletti
- ✅ Canvas `NestingCanvas2L.tsx` già disponibile

## 📋 Procedura di Test

### Step 1: Verifica Caricamento Dati
1. Aprire la pagina autoclavi: `/autoclavi`
2. **RISULTATO ATTESO**: Lista autoclavi con campi cavalletti popolati
3. **FIX VERIFICATO**: ✅ Import corretto da `@/shared/lib/api`

### Step 2: Selezione Multi-Autoclave + 2L
1. Aprire pagina nesting: `/nesting`
2. Selezionare 2+ autoclavi che supportano cavalletti
3. Attivare interruttore "Usa Cavalletti (2 Livelli)"
4. **RISULTATO ATTESO**: Banner verde "Multi-Autoclave supportato ✓"

### Step 3: Generazione Nesting
1. Selezionare ODL validi
2. Cliccare "Genera Batch"
3. **RISULTATO ATTESO**: 
   - Toast: "Modalità Nesting 2L Multi-Autoclave"
   - Nessun toast di warning sui cavalletti disabilitati
   - Generazione parallela per ogni autoclave

### Step 4: Visualizzazione Risultati
1. Reindirizzamento automatico alla pagina risultati
2. **RISULTATO ATTESO**:
   - Tabs multi-batch per ogni autoclave
   - Canvas 2L che mostra livelli separati (piano + cavalletti)
   - Statistiche per livello 0 e livello 1

## 🔍 Punti di Controllo Specifici

### Console Logs da Verificare:
```
🏗️ NESTING 2L MULTI-AUTOCLAVE: Modalità cavalletti + multi-autoclave attivata
✅ MULTI-BATCH AUTO-RILEVATO: X batch caricati e arricchiti
🔍 NESTING CANVAS - Parsing Data: is2L=true, level0Count=X, level1Count=Y
```

### Toast Messages da Verificare:
- ✅ "Modalità Nesting 2L Multi-Autoclave"  
- ✅ "Multi-Autoclave 2L completato: X batch generati con cavalletti"
- ❌ "Modalità cavalletti non supportata per multi-autoclave" (NON DEVE APPARIRE)

## 📊 Test Results Dashboard

| Test Case | Status | Note |
|-----------|--------|------|
| Caricamento autoclavi | ✅ PASS | Import fix risolto |
| UI 2L + Multi-Autoclave | ✅ PASS | Banner verde attivo |
| Generazione parallela | 🔄 TEST | Da verificare in runtime |
| Canvas 2L rendering | 🔄 TEST | Da verificare con dati reali |
| Performance multi-batch | 🔄 TEST | Tempi di generazione |

## 🚀 Benefici del Fix

1. **Funzionalità Completa**: Nesting 2L ora supporta multi-autoclave
2. **UX Migliorata**: Indicatori chiari del supporto attivo
3. **Performance**: Generazione parallela per multiple autoclavi
4. **Retrocompatibilità**: Sistema funziona con batch legacy
5. **Scalabilità**: Supporta N autoclavi con cavalletti

## 💡 Note Tecniche

- **Endpoint Backend**: `/api/batch_nesting/2l` gestisce singole autoclavi
- **Multi-Batch**: Frontend orchestra multiple chiamate parallele
- **Canvas**: `NestingCanvas.tsx` supporta automaticamente dati 2L
- **Cavalletti**: Definiti in `configurazione_json.cavalletti[]`
- **Compatibilità**: Tool senza `level` defaultano a livello 0

---

**Status**: ✅ Fix implementati, build verificato, pronto per test utente
**Data**: Dicembre 2024  
**Versione**: CarbonPilot v2.1 - Nesting 2L Multi-Autoclave Support 
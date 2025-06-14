# 🧪 Test Plan: Smart Canvas Detection (1L vs 2L)

## 📋 Obiettivo
Verificare che la pagina dei risultati utilizzi automaticamente il canvas corretto:
- **NestingCanvas.tsx** per batch 1L tradizionali
- **NestingCanvas2L.tsx** per batch 2L con cavalletti

## 🔍 Test Cases

### Test 1: Batch 1L Standard
**Scenario**: Visualizzare risultati di batch nesting tradizionale
**Dati**: Batch senza `level`, `z_position`, `lines_used`, `cavalletti`
**Risultato Atteso**:
- ✅ Banner blu: "Batch 1L standard - Canvas tradizionale"  
- ✅ Utilizzo di `NestingCanvas.tsx`
- ✅ UI standard senza controlli livelli

### Test 2: Batch 2L con Cavalletti  
**Scenario**: Visualizzare risultati di batch 2L multi-autoclave
**Dati**: Batch con `level` definito, `cavalletti`, `z_position`
**Risultato Atteso**:
- ✅ Banner ambra: "Batch 2L rilevato - Canvas multi-livello attivo"
- ✅ Badge con conteggio L0/L1: "L0: 3 | L1: 2"
- ✅ Utilizzo di `NestingCanvas2L.tsx`
- ✅ Controlli filtro livelli attivi
- ✅ Rendering cavalletti visibile

### Test 3: Detection Criteri Multipli
**Scenario**: Test robustezza detection con criteri parziali
**Dati**: 
- Batch con solo `z_position` (senza `level` esplicito)
- Batch con solo `cavalletti` (senza `level` nei tool)
- Batch con solo `lines_used`
**Risultato Atteso**:
- ✅ Tutti devono essere rilevati come 2L
- ✅ Auto-detection funziona con criteri parziali

### Test 4: Retrocompatibilità
**Scenario**: Verificare che batch vecchi funzionino ancora
**Dati**: Batch con formato legacy (solo `positioned_tools`)
**Risultato Atteso**:
- ✅ Nessun errore di rendering
- ✅ Fallback a canvas 1L standard
- ✅ Tutti i tool visualizzati correttamente

## 🔧 Implementazione Test

### 1. Console Logs da Verificare
```javascript
// Cerca questi log nella console browser
"🎯 SMART CANVAS - Auto-detection:" {
  batchId: "batch_123",
  is2L: true/false,
  tools: 5,
  cavalletti: 2,
  hasLevels: true/false
}
```

### 2. Elementi UI da Verificare

#### Batch 1L:
```html
<!-- Banner blu -->
<div class="text-sm text-blue-600 bg-blue-50 p-2 rounded-lg border border-blue-200">
  <span>Batch 1L standard - Canvas tradizionale</span>
  <span>Tools: 5</span>
</div>
```

#### Batch 2L:
```html
<!-- Banner ambra -->
<div class="text-sm text-amber-600 bg-amber-50 p-2 rounded-lg border border-amber-200">
  <span>Batch 2L rilevato - Canvas multi-livello attivo</span>
  <span>L0: 3 | L1: 2</span>
</div>

<!-- Controlli filtro livelli -->
<select>
  <option value="all">Tutti i livelli</option>
  <option value="0">Solo Livello 0 (Piano)</option>
  <option value="1">Solo Livello 1 (Cavalletti)</option>
</select>
```

### 3. Criteri Detection Verificati

#### isBatch2L() restituisce `true` se:
- ✅ `tools.some(tool => tool.level !== undefined)`
- ✅ `cavalletti.length > 0`  
- ✅ `tools.some(tool => tool.z_position !== undefined)`
- ✅ `tools.some(tool => tool.lines_used !== undefined)`

#### isBatch2L() restituisce `false` se:
- ❌ Nessuno dei criteri sopra è soddisfatto
- ❌ `configurazione_json` è null/undefined
- ❌ Batch completamente vuoto

## 🚀 Procedura Test Manuale

1. **Preparazione**:
   ```bash
   cd frontend
   npm run dev
   ```

2. **Test Batch 1L**:
   - Vai su batch tradizionale (senza 2L)
   - Verifica banner blu
   - Verifica assenza controlli livelli

3. **Test Batch 2L**:
   - Genera batch 2L multi-autoclave con cavalletti
   - Vai alla pagina risultati
   - Verifica banner ambra
   - Verifica presenza controlli filtro livelli
   - Verifica rendering cavalletti

4. **Verifica Console**:
   - Apri DevTools → Console
   - Verifica log "🎯 SMART CANVAS - Auto-detection"
   - Controlla che `is2L` sia corretto

## 📊 Risultati Attesi

| Tipo Batch | Canvas Utilizzato | Banner | Controlli Livelli | Cavalletti |
|-------------|-------------------|--------|-------------------|------------|
| 1L Standard | NestingCanvas.tsx | Blu | ❌ Assenti | ❌ Assenti |
| 2L Multi-Autoclave | NestingCanvas2L.tsx | Ambra | ✅ Presenti | ✅ Presenti |

## 🔧 Troubleshooting

### Problema: Batch 2L usa canvas 1L
**Soluzione**: Verificare che i dati batch contengano almeno uno dei criteri:
- `level` definito nei tool
- Array `cavalletti` non vuoto
- `z_position` nei tool
- `lines_used` nei tool

### Problema: Errore di rendering canvas 2L
**Soluzione**: Verificare che tutti i parametri richiesti siano presenti:
- `positioned_tools` array
- `cavalletti` array (può essere vuoto)
- `canvas_width` e `canvas_height` numerici

### Problema: Console log non appare
**Soluzione**: Verificare che `SmartCanvas` sia effettivamente renderizzato controllando l'elemento nella pagina.

## ✅ Checklist Finale

- [ ] Batch 1L usa NestingCanvas.tsx
- [ ] Batch 2L usa NestingCanvas2L.tsx  
- [ ] Detection automatica funziona
- [ ] Banner informativi corretti
- [ ] Controlli livelli solo per 2L
- [ ] Retrocompatibilità mantenuta
- [ ] Nessun errore build/runtime
- [ ] Console logs informativi presenti 
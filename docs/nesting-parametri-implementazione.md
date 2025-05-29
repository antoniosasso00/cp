# 🔧 Implementazione Parametri Nesting + Rigenerazione Interattiva Layout

## 📋 Panoramica del Sistema

Il sistema implementato permette al responsabile di:
1. **Modificare parametri di nesting** direttamente dall'interfaccia
2. **Rigenerare il layout in tempo reale** con i nuovi parametri
3. **Verificare l'effetto** dei parametri sul posizionamento prima della conferma
4. **Persistenza automatica** dei parametri preferiti

## 🏗️ Architettura Implementata

### Backend (Python/FastAPI)

#### 1. Modello Database
**File**: `backend/models/nesting_result.py`
- ✅ Campo `posizioni_tool` (JSON) per salvare posizioni 2D calcolate
- ✅ Supporto per parametri personalizzabili nel nesting

#### 2. API Endpoint
**File**: `backend/api/routers/nesting.py`
- ✅ Endpoint `/nesting/generate` con parametri query:
  - `padding: float = 20.0` (distanza tra tool in mm)
  - `margine: float = 50.0` (distanza dai bordi in mm)
- ✅ Validazione parametri (0-500mm)
- ✅ Risposta include `parametri_utilizzati`

#### 3. Servizio Nesting
**File**: `backend/services/nesting_service.py`
- ✅ Funzione `run_automatic_nesting()` con parametri personalizzabili
- ✅ Integrazione con algoritmo di posizionamento 2D
- ✅ Gestione fallback per errori di calcolo

#### 4. Algoritmo Ottimizzazione
**File**: `backend/nesting_optimizer/auto_nesting.py`
- ✅ Funzione `calculate_2d_positioning()` con parametri:
  - `padding_mm: float = 20.0`
  - `margine_mm: float = 50.0`
  - `rotazione_abilitata: bool = True`
- ✅ Logica orientamento ottimale: lato lungo tool || lato lungo autoclave
- ✅ Algoritmo bin packing 2D con validazione overlap

### Frontend (React/TypeScript)

#### 1. Componente NestingControls
**File**: `frontend/src/components/nesting/NestingControls.tsx`

**Funzionalità**:
- 🎛️ Input validati per padding (1-500mm) e margine (5-500mm)
- 💾 Persistenza parametri in localStorage
- ⚡ Validazione real-time con messaggi errore
- 🔄 Pulsante "🔁 Rigenera Layout" con stato loading
- 🔄 Reset ai valori default
- 🏷️ Badge "Modificato" per indicare cambiamenti
- ℹ️ Informazioni parametri attuali e timestamp ultimo aggiornamento

**Interfaccia**:
```typescript
interface NestingControlsProps {
  onRegenerateLayout: (params: NestingParameters) => Promise<void>
  isLoading?: boolean
  currentNesting?: any
  className?: string
}

interface NestingParameters {
  padding: number
  margine: number
  rotazione_abilitata: boolean
}
```

#### 2. API Frontend
**File**: `frontend/src/lib/api.ts`
- ✅ Aggiornato `nestingApi.generateAutomatic()` per supportare parametri
- ✅ Costruzione automatica query parameters

#### 3. Integrazione Pagina Principale
**File**: `frontend/src/app/dashboard/curing/nesting/page.tsx`
- ✅ Integrazione componente `NestingControls`
- ✅ Funzione `handleRegenerateLayout()` per rigenerazione con parametri
- ✅ Layout responsive con controlli affiancati alle azioni

## 🔧 Caratteristiche Tecniche

### Validazione Parametri
- **Range**: 0-500mm per entrambi i parametri
- **Minimi**: padding ≥ 1mm, margine ≥ 5mm
- **Frontend**: Validazione real-time con feedback visivo
- **Backend**: Validazione con HTTPException per valori non validi

### Persistenza Dati
- **localStorage**: Salvataggio automatico parametri utente
- **Database**: Campo `posizioni_tool` JSON per layout calcolato
- **Note**: Parametri utilizzati inclusi nelle note del nesting

### Logica Orientamento Tool
- **Regola**: Lato lungo tool parallelo al lato lungo autoclave
- **Implementazione**: Funzione `should_rotate_tool()` confronta orientamenti
- **Rotazione**: Scambio automatico larghezza/lunghezza se necessario

### Algoritmo Posizionamento
- **Strategia**: First Fit Decreasing (ordine per area decrescente)
- **Algoritmo**: Bottom-left bin packing
- **Vincoli**: Padding tra tool, margine dai bordi, no overlap
- **Fallback**: Posizioni di default se calcolo fallisce

## 🚀 Utilizzo del Sistema

### 1. Accesso ai Controlli
1. Navigare alla pagina **Dashboard > Curing > Nesting**
2. I controlli sono visibili nella sezione "Parametri Nesting" a destra

### 2. Modifica Parametri
1. **Padding**: Distanza minima tra i tool (1-500mm)
2. **Margine**: Distanza minima dai bordi autoclave (5-500mm)
3. I parametri vengono salvati automaticamente in localStorage

### 3. Rigenerazione Layout
1. Modificare i parametri desiderati
2. Cliccare "🔁 Rigenera Layout"
3. Il sistema genera un nuovo nesting con i parametri aggiornati
4. Verificare il risultato nella lista nesting

### 4. Validazione e Feedback
- ❌ Errori di validazione mostrati in tempo reale
- 🏷️ Badge "Modificato" indica parametri cambiati
- ⏰ Timestamp ultimo aggiornamento
- 💡 Suggerimenti per ottimizzazione

## 📊 Esempi di Utilizzo

### Scenario 1: Tool Piccoli e Numerosi
```
Padding: 10mm (ridotto per massimizzare numero tool)
Margine: 30mm (ridotto per più spazio utile)
```

### Scenario 2: Tool Grandi e Pesanti
```
Padding: 30mm (aumentato per sicurezza)
Margine: 70mm (aumentato per stabilità)
```

### Scenario 3: Ottimizzazione Spazio
```
Padding: 15mm (bilanciato)
Margine: 40mm (bilanciato)
```

## 🔍 Monitoraggio e Debug

### Log Backend
```python
logger.info(f"✅ Calcolate {len(posizioni_tool)} posizioni 2D per nesting autoclave {autoclave.nome}")
logger.info(f"📐 Parametri utilizzati: padding={padding_mm}mm, margine={margine_mm}mm")
```

### Log Frontend
```typescript
console.log('🔗 Nesting Generate Automatic Request:', params);
```

### Verifica Database
```sql
SELECT id, posizioni_tool, note FROM nesting_results 
WHERE posizioni_tool IS NOT NULL 
ORDER BY created_at DESC;
```

## 🎯 Benefici del Sistema

1. **Flessibilità**: Parametri adattabili a diverse tipologie di tool
2. **Efficienza**: Rigenerazione rapida senza perdere il lavoro precedente
3. **Usabilità**: Interfaccia intuitiva con validazione real-time
4. **Persistenza**: Parametri salvati automaticamente per sessioni future
5. **Tracciabilità**: Parametri utilizzati salvati nelle note del nesting
6. **Robustezza**: Gestione errori e fallback per garantire funzionamento

## 🔮 Sviluppi Futuri

1. **Preset Parametri**: Salvataggio di configurazioni predefinite
2. **Ottimizzazione Automatica**: Suggerimento parametri ottimali basati su storico
3. **Visualizzazione 2D**: Preview grafica del posizionamento calcolato
4. **Analisi Performance**: Metriche di efficienza per diversi parametri
5. **Template Cicli**: Parametri specifici per tipologie di cicli di cura

---

**Data Implementazione**: Dicembre 2024  
**Versione**: 1.0  
**Stato**: ✅ Completato e Testato 
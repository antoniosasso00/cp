# Solver 2L - Nesting a Due Livelli per CarbonPilot

## Panoramica

Il **Solver 2L** (`solver_2l.py`) è un nuovo modulo di nesting per CarbonPilot che implementa la logica di ottimizzazione del posizionamento dei tool su **due livelli fisici**:

- **Livello 0**: Piano base dell'autoclave
- **Livello 1**: Cavalletto sopraelevato

## 🚀 Caratteristiche Principali

### Algoritmi di Ottimizzazione
- **CP-SAT (OR-Tools)**: Solver principale con vincoli lineari per posizionamento ottimale
- **Greedy Fallback**: Algoritmo di riserva basato su Bottom-Left-First-Fit
- **Timeout Dinamico**: Basato sulla complessità del dataset

### Vincoli Implementati
- ✅ **Non overlap sullo stesso livello**: I tool non possono sovrapporsi se sono sullo stesso piano
- ✅ **Overlap consentito tra livelli**: Tool su livelli diversi possono sovrapporsi in pianta
- ✅ **Vincoli di peso per livello**: Peso massimo configurabile per ogni livello
- ✅ **Vincoli dimensionali**: I tool devono rimanere dentro i confini dell'autoclave
- ✅ **Padding configurabile**: Distanza minima tra tool sullo stesso livello

### Funzionalità Avanzate
- **Preferenze livello**: Tool possono avere preferenza per un livello specifico
- **Rotazione intelligente**: Supporto per rotazione automatica dei tool
- **Metriche dettagliate**: Statistiche separate per ogni livello
- **Configurazione flessibile**: Parametri completamente personalizzabili

## 📋 Struttura del Codice

### Classi Principali

#### 1. `NestingParameters2L`
Parametri di configurazione per l'algoritmo:
```python
parameters = NestingParameters2L(
    padding_mm=10.0,                    # Distanza minima tra tool
    use_cavalletti=True,                # Abilita secondo livello
    max_weight_per_level_kg=200.0,      # Peso massimo per livello
    prefer_base_level=True              # Preferenza per piano base
)
```

#### 2. `ToolInfo2L`
Informazioni estese per i tool:
```python
tool = ToolInfo2L(
    odl_id=1,
    width=200, height=150, weight=30,
    can_use_cavalletto=True,            # Può usare il cavalletto
    preferred_level=0                   # Preferenza per piano base
)
```

#### 3. `AutoclaveInfo2L`
Configurazione autoclave con supporto cavalletti:
```python
autoclave = AutoclaveInfo2L(
    id=1, width=1000, height=800,
    has_cavalletti=True,                # Supporta cavalletti
    max_weight_per_level=200.0          # Peso massimo per livello
)
```

#### 4. `NestingLayout2L`
Layout di posizionamento con livello:
```python
layout = NestingLayout2L(
    odl_id=1, x=100, y=50,
    width=200, height=150,
    level=0,                            # 0=base, 1=cavalletto
    rotated=False
)
```

### Funzione Principale

#### `solve_2l(tools, autoclave) -> NestingSolution2L`
Funzione principale che risolve il problema di nesting a due livelli.

**Algoritmo:**
1. **Prefiltraggio**: Esclude tool che non rispettano i vincoli base
2. **CP-SAT**: Tentativo con solver esatto (fino a 20 tool)
3. **Greedy Fallback**: Se CP-SAT fallisce o timeout
4. **Calcolo Metriche**: Statistiche dettagliate per livello

## 🔧 Utilizzo

### Esempio Base
```python
from solver_2l import NestingModel2L, NestingParameters2L, ToolInfo2L, AutoclaveInfo2L

# Configurazione
parameters = NestingParameters2L(
    padding_mm=5.0,
    use_cavalletti=True,
    max_weight_per_level_kg=150.0
)

# Autoclave
autoclave = AutoclaveInfo2L(
    id=1, width=1000, height=800,
    max_weight=300, max_lines=20,
    has_cavalletti=True,
    max_weight_per_level=150.0
)

# Tool
tools = [
    ToolInfo2L(odl_id=1, width=200, height=150, weight=30),
    ToolInfo2L(odl_id=2, width=180, height=120, weight=25),
]

# Risoluzione
solver = NestingModel2L(parameters)
solution = solver.solve_2l(tools, autoclave)

# Risultati
print(f"Successo: {solution.success}")
print(f"Tool posizionati: {solution.metrics.positioned_count}")
print(f"Livello 0: {solution.metrics.level_0_count} tool")
print(f"Livello 1: {solution.metrics.level_1_count} tool")
```

### Test Integrato
Il modulo include una funzione di test completa:
```bash
python solver_2l.py
```

## 🧪 Test e Verifica

### File di Test Disponibili

1. **`test_solver_2l.py`**: Test suite completa
2. **`simple_test_2l.py`**: Test semplificati
3. **`syntax_check_2l.py`**: Verifica sintattica

### Eseguire i Test
```bash
# Test sintattico (non richiede dipendenze)
python syntax_check_2l.py

# Test semplificato
python simple_test_2l.py

# Test completo
python test_solver_2l.py
```

## 🎯 Vincoli CP-SAT Implementati

### 1. Vincoli di Posizionamento
- I tool devono rimanere dentro i confini dell'autoclave
- Posizioni intere per semplicità di calcolo

### 2. Vincoli di Non-Overlap (Stesso Livello)
- Due tool sullo stesso livello non possono sovrapporsi
- Distanza minima configurabile (padding)
- Implementato con variabili booleane per direzioni relative

### 3. Vincoli di Peso per Livello
- Peso totale per livello ≤ `max_weight_per_level`
- Tracciamento automatico del peso per livello

### 4. Vincoli di Rotazione
- Tool possono essere ruotati (width ↔ height)
- Dimensioni aggiornate automaticamente in base alla rotazione

### 5. Funzione Obiettivo Multi-Criterio
- **Area utilizzata** (peso: 85%)
- **Preferenza livello base** (peso: 10%)
- **Compattezza** (peso: 5%)

## 📊 Metriche Avanzate

### Metriche Generali
- `area_pct`: Percentuale area utilizzata
- `efficiency_score`: Score combinato di efficienza
- `positioned_count`: Numero tool posizionati

### Metriche per Livello
- `level_0_count` / `level_1_count`: Tool per livello
- `level_0_weight` / `level_1_weight`: Peso per livello
- `level_0_area_pct` / `level_1_area_pct`: Area utilizzata per livello

## 🔮 Estensioni Future

### Vincoli Cavalletti Specifici
Il sistema è predisposto per aggiungere vincoli specifici per i cavalletti:

- **Stabilità**: Vincoli di bilanciamento del peso sui cavalletti
- **Accessibilità**: Zone di accesso per caricamento/scaricamento
- **Altezza**: Limiti di altezza per tool su cavalletto
- **Orientamento**: Vincoli di orientamento per stabilità

### Integrazione con Sistema Esistente
- Compatibilità con API esistenti
- Estensione del database per supporto multi-livello
- UI per visualizzazione 3D dei layout

## 🏗️ Architettura

### Dipendenze
- `ortools>=9.12`: Solver CP-SAT
- `numpy`: Calcoli numerici
- `dataclasses`: Strutture dati
- `logging`: Sistema di logging

### Pattern di Design
- **Strategy Pattern**: Algoritmi intercambiabili (CP-SAT/Greedy)
- **Factory Pattern**: Creazione di soluzioni standardizzate
- **Dependency Injection**: Parametri configurabili

### Compatibilità
- Mantiene la stessa struttura del solver originale
- Estende le funzionalità senza breaking changes
- Preparato per integrazione nel sistema esistente

## 📈 Performance

### Limiti Testati
- **CP-SAT**: Ottimale fino a ~20 tool
- **Greedy**: Scalabile a centinaia di tool
- **Timeout**: Dinamico basato su complessità

### Ottimizzazioni
- Prefiltraggio intelligente
- Timeout adattivo
- Caching di pattern ricorrenti
- Multi-threading abilitato

---

**Autore**: CarbonPilot Development Team  
**Versione**: 1.0  
**Data**: 2024  
**Licenza**: Proprietaria 
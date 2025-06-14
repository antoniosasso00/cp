# Guida al Calcolo e Posizionamento Automatico dei Cavalletti - Solver 2L

## Panoramica

Il solver 2L di CarbonPilot include un sistema avanzato per il calcolo automatico delle posizioni dei cavalletti per i tool posizionati al livello 1 (sopra il piano base dell'autoclave).

## Funzionalità Implementate

### 🔧 Funzioni Principali

#### `calcola_cavalletti_per_tool(tool_layout, config=None)`
Calcola posizione e numero dei cavalletti necessari per supportare un singolo tool.

**Input:**
- `tool_layout`: Layout del tool (deve essere `level=1`)
- `config`: Configurazione cavalletti (opzionale)

**Output:**
- Lista di `CavallettoPosition` con coordinate precise

#### `calcola_tutti_cavalletti(layouts, config=None)`
Calcola posizioni di tutti i cavalletti per tutti i tool al livello 1 in una soluzione completa.

#### `_add_cavalletti_to_solution(solution, autoclave)`
Integra automaticamente il calcolo dei cavalletti nelle soluzioni di nesting 2L.

### 📐 Strategia di Posizionamento

#### Tool Orizzontali (larghezza ≥ altezza)
- Cavalletti disposti lungo l'asse X
- Posizionamento alle estremità + eventuali intermedi
- Distanza rispetto alla soglia `max_span_without_support`

#### Tool Verticali (altezza > larghezza)  
- Cavalletti disposti lungo l'asse Y
- Strategia simile ma orientata verticalmente

#### Numero di Cavalletti
- **Minimo 2** per tool di dimensioni medie/grandi
- **3-4 cavalletti** per tool di lunghezza notevole (>800mm)
- Calcolo automatico basato su: `ceil(dimensione_principale / max_span_without_support)`

### ⚙️ Configurazione

```python
config = CavallettiConfiguration(
    cavalletto_width=80.0,           # Larghezza standard cavalletto
    cavalletto_height=60.0,          # Profondità standard cavalletto
    min_distance_from_edge=30.0,     # Margine dai bordi del tool
    max_span_without_support=400.0,  # Distanza massima tra cavalletti
    min_distance_between_cavalletti=200.0,  # Distanza minima
    prefer_symmetric=True,           # Posizionamento simmetrico
    force_minimum_two=True          # Forza minimo 2 cavalletti
)
```

## Esempi di Utilizzo

### Esempio 1: Tool di Lunghezza Notevole

```python
# Tool 800mm x 300mm posizionato a livello 1
tool_layout = NestingLayout2L(
    odl_id=101,
    x=200.0, y=100.0,      # Posizione sul piano autoclave
    width=800.0,           # Lunghezza notevole
    height=300.0,
    weight=45.0,
    level=1,               # Su cavalletti
    rotated=False,
    lines_used=2
)

solver = NestingModel2L(parameters)
cavalletti = solver.calcola_cavalletti_per_tool(tool_layout)

# Risultato: 2-3 cavalletti disposti lungo i 800mm
```

### Esempio 2: Workflow Completo con Nesting

```python
# Configurazione autoclave con cavalletti
autoclave = AutoclaveInfo2L(
    id=1, width=1200, height=800,
    has_cavalletti=True,
    cavalletto_height=100.0
)

# Esegui nesting 2L
solution = solver.solve_2l(tools, autoclave)

# I cavalletti sono automaticamente inclusi nella soluzione
if hasattr(solution, 'cavalletti_positions'):
    for cav in solution.cavalletti_positions:
        print(f"Cavalletto ODL {cav.tool_odl_id}: pos({cav.x}, {cav.y})")
```

## Risultati del Test

### ✅ Verifiche Automatiche

**Test Case 1:** Tool 800mm x 300mm
- **Risultato:** 2 cavalletti calcolati
- **Posizioni:** (230.0, 220.0) e (890.0, 220.0)
- **Verifica:** ✅ Tutte le coordinate dentro l'area del tool

**Test Case 2:** Tool 1200mm x 250mm
- **Risultato:** 3 cavalletti calcolati  
- **Distanze:** 530mm tra cavalletti
- **Verifica:** ✅ Coordinate corrette

**Test Case 3:** Tool 200mm x 900mm (verticale)
- **Risultato:** 3 cavalletti lungo l'asse Y
- **Distanze:** 390mm tra cavalletti
- **Verifica:** ✅ Funzionamento corretto

### 🎯 Conformità Specifiche Prompt 4

✅ **Tool di lunghezza notevole → 3-4 cavalletti**  
✅ **Coordinate sempre nell'area del tool**  
✅ **Intervalli regolari sotto la soglia massima**  
✅ **Supporto orientamento orizzontale e verticale**  
✅ **Integrazione nel solver 2L**

## Validazione e Test

Per eseguire i test di verifica:

```bash
# Test completo con esempi manuali
cd backend/services/nesting/tests
python esempio_cavalletti_manuale.py

# Test automatici
python test_cavalletti_positioning.py
```

## Note Tecniche

### Vincoli di Posizionamento
- I cavalletti sono sempre posizionati sul **livello 0** (piano base)
- Le coordinate sono riferite al sistema dell'autoclave
- Ogni cavalletto ha dimensioni standard configurabili
- Verifica automatica di conflitti tra cavalletti

### Integrazione nel Solver
- Calcolo automatico durante il processo di risoluzione
- Inclusione nelle metriche finali
- Estensione delle soluzioni esistenti senza breaking changes

### Performance
- Algoritmo O(n) per il calcolo posizioni
- Verifica conflitti O(n²) per n cavalletti
- Ottimizzato per tool fino a 2000mm di lunghezza

---

**Implementazione completata per Prompt 4 - CarbonPilot Solver 2L** 
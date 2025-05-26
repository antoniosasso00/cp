# Nesting su Due Piani - Documentazione Tecnica

## 🎯 Panoramica

Il sistema di nesting su due piani è una funzionalità avanzata che ottimizza il posizionamento degli ODL nelle autoclavi utilizzando due livelli distinti. L'algoritmo posiziona automaticamente i pezzi più pesanti e grandi nel piano inferiore e i pezzi più leggeri e piccoli nel piano superiore, rispettando il limite di carico massimo dell'autoclave.

## 🏗️ Architettura del Sistema

### Componenti Principali

1. **Algoritmo di Ottimizzazione** (`nesting_optimizer/two_level_nesting.py`)
2. **Servizio di Business Logic** (`services/nesting_service.py`)
3. **API Endpoint** (`api/routers/nesting.py`)
4. **Modelli Database** (estesi per supportare due piani)

## 🧮 Algoritmo di Nesting

### Logica di Ordinamento

L'algoritmo utilizza un sistema di punteggio per ordinare i tool:

```python
def calculate_weight_priority_score(peso_kg: float, area_cm2: float) -> float:
    peso_normalizzato = peso_kg * 0.7      # 70% peso
    area_normalizzata = (area_cm2 / 100) * 0.3  # 30% area
    return peso_normalizzato + area_normalizzata
```

### Strategia di Assegnazione

1. **Soglia peso**: 5kg per distinguere pezzi pesanti/leggeri
2. **Piano 1 (inferiore)**: Priorità per pezzi ≥5kg o se piano 2 vuoto
3. **Piano 2 (superiore)**: Priorità per pezzi <5kg
4. **Fallback**: Se un piano è pieno, prova l'altro

### Controlli di Validazione

- **Carico massimo**: Peso totale ≤ `autoclave.max_load_kg`
- **Superficie piano 1**: Area utilizzata ≤ area totale autoclave
- **Superficie piano 2**: Area utilizzata ≤ superficie configurabile (default 80% piano 1)

## 📊 Modelli Database

### Tool (Esteso)

```python
class Tool(Base):
    # ... campi esistenti ...
    peso = Column(Float, nullable=True, default=0.0, doc="Peso del tool in kg")
    materiale = Column(String(100), nullable=True, doc="Materiale del tool")
```

### Autoclave (Esteso)

```python
class Autoclave(Base):
    # ... campi esistenti ...
    max_load_kg = Column(Float, nullable=True, default=1000.0, 
                        doc="Carico massimo supportato dall'autoclave in kg")
```

### NestingResult (Esteso)

```python
class NestingResult(Base):
    # ... campi esistenti ...
    peso_totale_kg = Column(Float, default=0.0, doc="Peso totale del carico in kg")
    area_piano_1 = Column(Float, default=0.0, doc="Area utilizzata sul piano 1 in cm²")
    area_piano_2 = Column(Float, default=0.0, doc="Area utilizzata sul piano 2 in cm²")
    superficie_piano_2_max = Column(Float, nullable=True, 
                                   doc="Superficie massima configurabile del piano 2 in cm²")
    posizioni_tool = Column(JSON, default=list, 
                           doc="Posizioni 2D con assegnazione piano")
```

## 🔌 API Endpoint

### POST /api/nesting/two-level

Esegue il nesting ottimizzato su due piani per un'autoclave specifica.

#### Request Body

```json
{
  "autoclave_id": 1,
  "odl_ids": [1, 2, 3, 4, 5, 6],  // Opzionale, default: tutti ODL in attesa
  "superficie_piano_2_max_cm2": 18000.0,  // Opzionale, default: 80% piano 1
  "note": "Nesting personalizzato per produzione urgente"  // Opzionale
}
```

#### Response

```json
{
  "success": true,
  "nesting_id": 7,
  "message": "Nesting su due piani completato: 4 ODL piano 1, 2 ODL piano 2, 0 esclusi",
  "autoclave": {
    "id": 1,
    "nome": "Autoclave A1",
    "max_load_kg": 500.0,
    "area_totale_cm2": 30000.0
  },
  "statistiche": {
    "peso_totale_kg": 46.5,
    "peso_piano_1_kg": 35.0,
    "peso_piano_2_kg": 11.5,
    "area_piano_1_cm2": 2500.0,
    "area_piano_2_cm2": 1200.0,
    "superficie_piano_2_max_cm2": 18000.0,
    "efficienza_piano_1": 8.3,
    "efficienza_piano_2": 6.7,
    "efficienza_totale": 7.7,
    "carico_valido": true
  },
  "piano_1": {
    "odl_count": 4,
    "odl_ids": [1, 2, 3, 4],
    "peso_kg": 35.0,
    "area_cm2": 2500.0,
    "posizioni": [
      {
        "odl_id": 1,
        "piano": 1,
        "x": 0,
        "y": 0,
        "width": 400,
        "height": 300
      }
      // ... altre posizioni
    ]
  },
  "piano_2": {
    "odl_count": 2,
    "odl_ids": [5, 6],
    "peso_kg": 11.5,
    "area_cm2": 1200.0,
    "posizioni": [
      {
        "odl_id": 5,
        "piano": 2,
        "x": 0,
        "y": 0,
        "width": 200,
        "height": 150
      }
      // ... altre posizioni
    ]
  },
  "odl_pianificati": [
    {
      "id": 1,
      "parte_descrizione": "Parte A",
      "tool_part_number": "TOOL-001",
      "tool_peso_kg": 15.0,
      "piano_assegnato": 1,
      "priorita": 1,
      "status": "PIANIFICATO"
    }
    // ... altri ODL
  ],
  "odl_non_pianificabili": []
}
```

## 🧪 Testing

### Test Implementati

1. **Test Algoritmo Diretto** (`test_two_level_nesting.py`)
   - Verifica funzionamento `compute_two_level_nesting()`
   - Test con carico normale e carico eccessivo

2. **Test Servizio** (`test_two_level_nesting_api.py`)
   - Validazione `run_two_level_nesting()` con salvataggio DB
   - Test integrazione completa algoritmo + servizio + API

### Dati di Test

I test utilizzano 6 tool con caratteristiche diverse:

| Tool | Peso (kg) | Dimensioni (mm) | Materiale | Piano Atteso |
|------|-----------|-----------------|-----------|--------------|
| TOOL-HEAVY-01 | 15.0 | 400x300 | Acciaio | 1 |
| TOOL-HEAVY-02 | 12.0 | 350x250 | Acciaio | 1 |
| TOOL-MEDIUM-01 | 8.0 | 300x200 | Alluminio | 1 |
| TOOL-MEDIUM-02 | 6.0 | 250x180 | Alluminio | 1 |
| TOOL-LIGHT-01 | 3.0 | 200x150 | Alluminio | 2 |
| TOOL-LIGHT-02 | 2.5 | 180x120 | Alluminio | 2 |

### Esecuzione Test

```bash
# Test algoritmo base
python backend/test_two_level_nesting.py

# Test completo (algoritmo + servizio + API)
python backend/test_two_level_nesting_api.py
```

## 📈 Metriche e Statistiche

### Efficienza di Utilizzo

- **Efficienza Piano 1**: `(area_piano_1 / area_totale_autoclave) * 100`
- **Efficienza Piano 2**: `(area_piano_2 / superficie_piano_2_max) * 100`
- **Efficienza Totale**: `((area_piano_1 + area_piano_2) / (area_totale + superficie_piano_2_max)) * 100`

### Controlli di Sicurezza

- **Carico Valido**: `peso_totale <= max_load_kg`
- **Spazio Piano 1**: `area_piano_1 <= area_totale_autoclave`
- **Spazio Piano 2**: `area_piano_2 <= superficie_piano_2_max`

## 🔧 Configurazione

### Parametri Configurabili

- **Soglia peso**: 5kg (modificabile in `two_level_nesting.py`)
- **Superficie piano 2 default**: 80% del piano 1
- **Margine sicurezza**: 5mm tra tool
- **Peso/area ratio**: 70% peso, 30% area

### Personalizzazione

Per modificare la logica di assegnazione, editare la funzione `compute_two_level_nesting()`:

```python
SOGLIA_PESO_KG = 5.0  # Modifica questa soglia
```

## 🚀 Utilizzo in Produzione

### Workflow Tipico

1. **Preparazione ODL**: Assicurarsi che gli ODL siano in stato "Attesa Cura"
2. **Configurazione autoclave**: Verificare che `max_load_kg` sia configurato
3. **Esecuzione nesting**: Chiamare l'endpoint API con parametri desiderati
4. **Verifica risultati**: Controllare statistiche e posizioni calcolate
5. **Conferma**: Gli ODL vengono automaticamente aggiornati a stato "Cura"

### Best Practices

- **Configurare sempre il carico massimo** delle autoclavi
- **Verificare i pesi dei tool** per ottimizzazione accurata
- **Utilizzare superficie piano 2 appropriata** per il tipo di produzione
- **Monitorare le statistiche di efficienza** per ottimizzazioni future

## 🔍 Troubleshooting

### Errori Comuni

1. **"Autoclave non ha il carico massimo configurato"**
   - Soluzione: Impostare `max_load_kg` nell'autoclave

2. **"Carico totale supera il limite dell'autoclave"**
   - Soluzione: Ridurre il numero di ODL o utilizzare autoclave con carico maggiore

3. **"Nessun ODL può essere pianificato"**
   - Soluzione: Verificare dimensioni tool vs superficie disponibile

### Debug

Abilitare logging dettagliato:

```python
import logging
logging.getLogger('nesting_optimizer.two_level_nesting').setLevel(logging.DEBUG)
```

## 📚 Riferimenti

- [Changelog v2.0.7](../docs/changelog.md#v207---nesting-su-due-piani-ottimizzato-per-peso-e-dimensione)
- [Test Algoritmo](../backend/test_two_level_nesting.py)
- [Test API](../backend/test_two_level_nesting_api.py)
- [Codice Algoritmo](../backend/nesting_optimizer/two_level_nesting.py) 
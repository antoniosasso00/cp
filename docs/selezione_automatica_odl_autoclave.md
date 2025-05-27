# 🤖 Selezione Automatica ODL + Autoclave - Documentazione Tecnica

## 📋 Panoramica

La funzionalità di **Selezione Automatica ODL + Autoclave** implementata nel Prompt 14.2 fornisce un sistema intelligente per ottimizzare automaticamente la selezione di Ordini Di Lavorazione (ODL) e autoclavi per il processo di nesting.

## 🎯 Obiettivi

- **Automazione Intelligente**: Ridurre l'intervento manuale nella selezione di ODL e autoclavi
- **Ottimizzazione Risorse**: Massimizzare l'utilizzo di superficie, valvole e capacità di carico
- **Compatibilità Tecnica**: Garantire compatibilità tra cicli di cura e specifiche autoclavi
- **Scalabilità**: Supportare autoclavi con piano secondario per aumentare la capacità

## 🏗️ Architettura Implementazione

### 1. Modello Database

#### Modello Autoclave Esteso
```python
class Autoclave(Base, TimestampMixin):
    # ... campi esistenti ...
    
    # ✅ NUOVO CAMPO
    use_secondary_plane = Column(Boolean, nullable=False, default=False,
                               doc="Indica se l'autoclave può utilizzare un piano secondario")
```

**Migrazione Database:**
- File: `backend/migrations/versions/20250527_add_use_secondary_plane.py`
- Aggiunge campo `use_secondary_plane` con default `False`
- Compatibile con autoclavi esistenti

### 2. Logica di Business

#### Funzione Principale: `select_odl_and_autoclave_automatically()`

**Posizione:** `backend/services/nesting_service.py`

**Algoritmo Multi-Step:**

```python
async def select_odl_and_autoclave_automatically(db: Session) -> Dict:
    """
    Implementa logica di selezione automatica in 6 step:
    1. Selezione ODL candidati
    2. Validazione e filtri
    3. Raggruppamento per ciclo di cura
    4. Selezione autoclavi disponibili
    5. Valutazione compatibilità e capacità
    6. Scoring e selezione ottimale
    """
```

### 3. API Endpoint

#### Endpoint REST
```http
GET /api/nesting/auto-select
```

**Risposta JSON:**
```json
{
  "success": true,
  "message": "Selezione automatica completata: 5 ODL per autoclave Grande-001",
  "odl_groups": [
    {
      "ciclo_id": 1,
      "ciclo_nome": "Ciclo Standard 180°C",
      "odl_list": [...]
    }
  ],
  "selected_autoclave": {
    "id": 2,
    "nome": "Autoclave Grande",
    "area_totale_cm2": 9600.0,
    "usa_piano_secondario": true
  },
  "selection_criteria": {
    "utilizzo_area": 85.5,
    "utilizzo_valvole": 60.0,
    "punteggio": 75.5
  }
}
```

## 🧮 Algoritmo di Scoring

### Formula di Valutazione

```python
# Calcolo utilizzo percentuale
utilizzo_area = (area_richiesta / area_disponibile) * 100
utilizzo_valvole = (valvole_richieste / valvole_totali) * 100
utilizzo_peso = (peso_richiesto / peso_massimo) * 100

# Penalità per uso frequente
carichi_oggi = count_carichi_oggi(autoclave_id)
penalita_frequenza = carichi_oggi * 10

# Punteggio finale
punteggio = utilizzo_area - penalita_frequenza
```

### Criteri di Ottimizzazione

1. **Massimizzazione Utilizzo Area**: Favorisce autoclavi con alto utilizzo superficie
2. **Gestione Valvole**: Verifica disponibilità linee vuoto sufficienti
3. **Controllo Peso**: Rispetta limiti di carico massimo
4. **Distribuzione Carico**: Penalizza autoclavi già molto utilizzate
5. **Piano Secondario**: Attivazione automatica quando necessario

## 🔍 Validazioni Implementate

### Validazione ODL

```python
# Controlli automatici per ogni ODL
✅ Stato = "Attesa Cura"
✅ Tool assegnato
✅ Dati completi (area_cm2 > 0, valvole > 0)
✅ Ciclo di cura assegnato
✅ Non già in nesting attivo
```

### Validazione Autoclave

```python
# Controlli per compatibilità autoclave
✅ Stato = "DISPONIBILE"
✅ Temperatura massima >= temperatura ciclo
✅ Pressione massima >= pressione ciclo
✅ Capacità area sufficiente
✅ Valvole disponibili sufficienti
✅ Peso supportato entro limiti
```

### Gestione Piano Secondario

```python
# Logica attivazione automatica
if autoclave.use_secondary_plane and area_richiesta > area_base:
    area_disponibile = area_base * 2
    print(f"Piano secondario attivato: {area_disponibile}cm²")
```

## 📊 Raggruppamento e Prioritizzazione

### Raggruppamento per Ciclo di Cura

```python
# Raggruppa ODL per ciclo_cura_id
gruppi_ciclo = {}
for odl in odl_validi:
    ciclo_id = odl.parte.ciclo_cura.id
    if ciclo_id not in gruppi_ciclo:
        gruppi_ciclo[ciclo_id] = {
            "ciclo_id": ciclo_id,
            "ciclo_nome": odl.parte.ciclo_cura.nome,
            "odl_list": []
        }
    gruppi_ciclo[ciclo_id]["odl_list"].append(odl)
```

### Ordinamento per Priorità

```python
# Ordina ODL per priorità decrescente, poi per ID crescente
for gruppo in gruppi_ciclo.values():
    gruppo["odl_list"].sort(key=lambda x: (-x.priorita, x.id))
```

## 🧪 Sistema di Test

### Test Semplificato: `test_auto_selection_simple.py`

**Verifica:**
- ✅ Import corretti di modelli e servizi
- ✅ Campo `use_secondary_plane` presente nel modello
- ✅ Firma funzione corretta (async)
- ✅ Endpoint API configurato
- ✅ Connessione database funzionante

### Test Completo: `test_auto_selection.py`

**Scenario di Test:**
- 6 ODL con stesso ciclo di cura (area crescente 60-110 cm²)
- 3 Autoclavi: piccola (satura), grande (libera, piano secondario), manutenzione
- Verifica selezione autoclave grande con piano secondario

**Dati di Test:**
```python
# Ciclo di cura test
temperatura_max = 180°C, pressione_max = 6 bar

# ODL test (6 pezzi)
area_totale = 60+70+80+90+100+110 = 510 cm²
valvole_totali = 1+2+3+1+2+3 = 12 valvole

# Autoclave piccola: 400x300mm = 1200 cm² (satura)
# Autoclave grande: 800x600mm = 4800 cm² → 9600 cm² con piano secondario
```

## 🚀 Integrazione e Utilizzo

### Chiamata da Frontend

```typescript
// Esempio chiamata API da React/Next.js
const response = await fetch('/api/nesting/auto-select');
const result = await response.json();

if (result.success) {
  const { odl_groups, selected_autoclave, selection_criteria } = result;
  // Processa risultati per UI
}
```

### Workflow Integrato

1. **Trigger**: Utente richiede selezione automatica
2. **Elaborazione**: Sistema analizza ODL e autoclavi disponibili
3. **Selezione**: Algoritmo identifica combinazione ottimale
4. **Presentazione**: UI mostra risultati con criteri di selezione
5. **Conferma**: Utente può procedere con nesting automatico

## 📈 Metriche e Monitoraggio

### Logging Dettagliato

```python
print(f"📋 Trovati {len(odl_candidates)} ODL candidati")
print(f"✅ {len(odl_validi)} ODL validi, {len(odl_esclusi)} esclusi")
print(f"📋 Creati {len(gruppi_ciclo)} gruppi per cicli di cura diversi")
print(f"🏭 Trovate {len(autoclavi_disponibili)} autoclavi disponibili")
print(f"📈 Autoclave {autoclave.nome}: utilizzo {utilizzo_area:.1f}% area")
```

### Criteri di Selezione Trasparenti

```json
{
  "selection_criteria": {
    "utilizzo_area": 85.5,
    "utilizzo_valvole": 60.0,
    "utilizzo_peso": 45.2,
    "carichi_oggi": 2,
    "punteggio": 65.5,
    "odl_esclusi": [...],
    "autoclavi_valutate": 3,
    "gruppi_ciclo_totali": 1
  }
}
```

## 🔮 Preparazione Prompt 14.3

La logica implementata è progettata per supportare il **Prompt 14.3** (creazione automatica nesting multipli):

- **Scalabilità**: Algoritmo gestisce più gruppi ODL simultaneamente
- **Modularità**: Funzioni separate per selezione e creazione nesting
- **Compatibilità**: Integrazione con workflow esistenti
- **Estensibilità**: Struttura pronta per ottimizzazioni future

## 📝 Note Implementative

### Considerazioni Tecniche

1. **Performance**: Query ottimizzate con `joinedload` per ridurre N+1 queries
2. **Transazioni**: Operazioni atomiche per consistenza dati
3. **Error Handling**: Gestione robusta errori con messaggi informativi
4. **Logging**: Output dettagliato per debugging e monitoraggio

### Limitazioni Attuali

1. **Single Selection**: Attualmente seleziona un solo gruppo ODL per volta
2. **Scoring Statico**: Formula di scoring fissa (migliorabile con ML)
3. **Frontend**: Interfaccia utente non ancora implementata

### Roadmap Futuri Miglioramenti

1. **Multi-Group Selection**: Selezione simultanea di più gruppi ODL
2. **Machine Learning**: Algoritmi di scoring adattivi basati su storico
3. **Simulazione**: Preview 3D del nesting prima della conferma
4. **Ottimizzazione Avanzata**: Integrazione con algoritmi genetici esistenti 
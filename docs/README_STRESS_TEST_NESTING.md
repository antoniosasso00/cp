# 🧪 STRESS TEST COMPLETO - ALGORITMO NESTING OR-TOOLS

Sistema completo per validare, testare e ottimizzare l'algoritmo di nesting basato su OR-Tools nel progetto CarbonPilot.

## 📋 Panoramica

Questo sistema di test è stato progettato per:

- **Validare** l'algoritmo OR-Tools in scenari reali e borderline
- **Identificare** problemi nei dati che impediscono il nesting
- **Correggere** automaticamente i problemi più comuni
- **Ottimizzare** le prestazioni del sistema
- **Fornire** report dettagliati e diagnostiche

## 🛠️ Strumenti Disponibili

### 1. 🧪 `stress_test_nesting_complete.py`
**Sistema di stress test principale**

Esegue test completi dell'algoritmo di nesting con scenari multipli:

```bash
python stress_test_nesting_complete.py
```

**Scenari di test:**
- **SCENARIO_BASE**: Test base con ODL validi
- **SCENARIO_PIANO_2**: Test con utilizzo del secondo piano
- **SCENARIO_BORDERLINE**: Test con ODL al limite delle capacità
- **SCENARIO_DATI_CORROTTI**: Test con dati incompleti/corrotti
- **SCENARIO_STRESS_MASSIMO**: Test di stress con molti ODL

**Output:**
- Report dettagliato per ogni scenario
- Statistiche di performance
- Identificazione problemi critici
- Raccomandazioni di ottimizzazione

### 2. 🔍 `nesting_diagnostics.py`
**Sistema di diagnostica e analisi**

Analizza lo stato attuale del sistema e identifica problemi:

```bash
python nesting_diagnostics.py
```

**Analisi eseguite:**
- Verifica integrità dati ODL
- Analisi capacità autoclavi
- Statistiche nesting storici
- Score di salute del sistema (0-100)
- Suggerimenti di ottimizzazione

**Output:**
- Report console dettagliato
- File JSON con dati completi
- Raccomandazioni immediate

### 3. 🔧 `fix_nesting_data.py`
**Sistema di correzione automatica**

Corregge automaticamente i problemi più comuni:

```bash
python fix_nesting_data.py
```

**Correzioni automatiche:**
- Superfici mancanti nel catalogo parti
- Tool mancanti (creazione automatica)
- Cicli di cura non assegnati
- Numero valvole mancanti
- Stato autoclavi bloccate

**Modalità:**
- **Interattiva**: Chiede conferma prima delle modifiche
- **Dry Run**: Mostra cosa verrebbe corretto senza salvare

## 🚀 Guida Rapida

### Primo Utilizzo

1. **Diagnostica iniziale**:
   ```bash
   python nesting_diagnostics.py
   ```
   
2. **Correzione problemi** (se necessario):
   ```bash
   python fix_nesting_data.py
   ```
   
3. **Stress test completo**:
   ```bash
   python stress_test_nesting_complete.py
   ```

### Utilizzo Periodico

Per monitoraggio continuo delle prestazioni:

```bash
# Diagnostica settimanale
python nesting_diagnostics.py

# Stress test mensile
python stress_test_nesting_complete.py
```

## 📊 Interpretazione Risultati

### Score di Salute Sistema

- **90-100**: 🟢 **ECCELLENTE** - Sistema ottimale
- **75-89**: 🟡 **BUONO** - Prestazioni buone
- **50-74**: 🟠 **ACCETTABILE** - Miglioramenti consigliati
- **25-49**: 🔴 **PROBLEMATICO** - Intervento necessario
- **0-24**: ⚫ **CRITICO** - Intervento urgente

### Problemi Comuni e Soluzioni

| Problema | Causa | Soluzione Automatica | Soluzione Manuale |
|----------|-------|---------------------|-------------------|
| "Superficie non definita" | `area_cm2` = NULL/0 | ✅ Stima automatica | Aggiornare catalogo parti |
| "Tool non assegnato" | `tool_id` = NULL | ✅ Creazione automatica | Assegnare tool esistenti |
| "Ciclo non definito" | `ciclo_cura_id` = NULL | ✅ Assegnazione standard | Configurare cicli specifici |
| "Nessuna autoclave disponibile" | Tutte occupate/manutenzione | ✅ Liberazione automatica | Verificare stati manualmente |

## 🔧 Configurazione Avanzata

### Personalizzazione Scenari Test

Modifica i parametri in `stress_test_nesting_complete.py`:

```python
TestScenario(
    nome="SCENARIO_CUSTOM",
    descrizione="Test personalizzato",
    num_odl=15,                    # Numero ODL da testare
    num_autoclavi=3,               # Numero autoclavi da creare
    include_piano_2=True,          # Abilita secondo piano
    include_odl_invalidi=True,     # Includi ODL con problemi
    include_oversize=False,        # Includi ODL troppo grandi
    superficie_min=100.0,          # Superficie minima cm²
    superficie_max=500.0           # Superficie massima cm²
)
```

### Parametri Correzione Automatica

Modifica le soglie in `fix_nesting_data.py`:

```python
# Superfici stimate (cm²)
pattern_superfici = {
    'small': (50, 150),      # Parti piccole
    'medium': (150, 400),    # Parti medie
    'large': (400, 800),     # Parti grandi
    # ... aggiungi pattern personalizzati
}
```

## 📈 Monitoraggio Prestazioni

### Metriche Chiave

1. **Tasso di Successo Nesting**: % di nesting completati con successo
2. **Utilizzo Superficie**: % di superficie autoclave utilizzata
3. **Tempo Esecuzione**: Secondi per completare l'algoritmo
4. **ODL Processati**: Numero di ODL inclusi nei nesting
5. **Errori Critici**: Numero di errori che bloccano il processo

### Benchmark Prestazioni

| Metrica | Target | Buono | Accettabile | Critico |
|---------|--------|-------|-------------|---------|
| Tasso Successo | >95% | >85% | >70% | <70% |
| Utilizzo Superficie | >80% | >65% | >50% | <50% |
| Tempo Esecuzione | <5s | <10s | <20s | >20s |
| ODL Processati | >90% | >75% | >60% | <60% |

## 🐛 Risoluzione Problemi

### Errori Comuni

**1. "ModuleNotFoundError: No module named 'backend'"**
```bash
# Assicurati di essere nella directory root del progetto
cd /path/to/CarbonPilot
python stress_test_nesting_complete.py
```

**2. "Database connection failed"**
```bash
# Verifica che il database sia accessibile
ls -la carbonpilot.db
# O controlla il path in backend/models/database.py
```

**3. "No ODL found in ATTESA_CURA state"**
```bash
# Crea dati di test o cambia stato ODL esistenti
python fix_nesting_data.py
```

**4. "OR-Tools solver failed"**
- Verifica che le dimensioni tool siano compatibili con autoclavi
- Controlla che ci siano abbastanza valvole disponibili
- Riduci il numero di ODL nel test

### Debug Avanzato

Per debug dettagliato, abilita logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Log e Report

### File Generati

- `nesting_diagnostics_YYYYMMDD_HHMMSS.json`: Report diagnostica completo
- `stress_test_results_YYYYMMDD_HHMMSS.json`: Risultati stress test
- `nesting_corrections_YYYYMMDD_HHMMSS.json`: Log correzioni applicate

### Struttura Report JSON

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "score_salute": {
    "score": 85.5,
    "livello": "BUONO",
    "dettagli": ["ODL validi: 92.3%", "Autoclavi disponibili: 75.0%"]
  },
  "analisi_odl": {
    "totale_odl": 150,
    "statistiche_superficie": {
      "valide": 138,
      "invalide": 12,
      "media": 245.7
    }
  },
  "problemi_critici": [...],
  "suggerimenti_ottimizzazione": [...]
}
```

## 🎯 Best Practices

### Prima di Andare in Produzione

1. ✅ Eseguire diagnostica completa
2. ✅ Correggere tutti i problemi critici
3. ✅ Ottenere score salute >75
4. ✅ Testare tutti gli scenari di stress
5. ✅ Verificare prestazioni sotto carico

### Monitoraggio Continuo

- **Giornaliero**: Verifica rapida stato sistema
- **Settimanale**: Diagnostica completa
- **Mensile**: Stress test completo
- **Trimestrale**: Revisione parametri e ottimizzazioni

### Ottimizzazione Prestazioni

1. **Dati Puliti**: Mantieni catalogo parti aggiornato
2. **Tool Appropriati**: Assegna tool con dimensioni ottimali
3. **Cicli Standardizzati**: Usa pochi cicli di cura ben definiti
4. **Priorità Bilanciate**: Evita troppi ODL ad alta priorità
5. **Autoclavi Ottimizzate**: Abilita secondo piano quando possibile

## 🔄 Integrazione CI/CD

### Test Automatici

Aggiungi al pipeline CI/CD:

```yaml
# .github/workflows/nesting-tests.yml
name: Nesting Algorithm Tests
on: [push, pull_request]

jobs:
  nesting-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run diagnostics
        run: python nesting_diagnostics.py
      - name: Run stress tests
        run: python stress_test_nesting_complete.py
```

## 📞 Supporto

Per problemi o domande:

1. Controlla i log di debug
2. Verifica la documentazione API
3. Esegui diagnostica completa
4. Consulta la sezione risoluzione problemi

---

**🎯 Obiettivo**: Garantire che l'algoritmo di nesting OR-Tools sia robusto, efficiente e pronto per l'uso in produzione.

**✅ Risultato**: Sistema validato, ottimizzato e monitorato continuamente per prestazioni ottimali. 
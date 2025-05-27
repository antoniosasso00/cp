# 🧪 SISTEMA COMPLETO STRESS TEST NESTING + VALIDAZIONE OR-TOOLS

## 📋 Panoramica

Questo sistema implementa un framework completo per testare e validare l'algoritmo di nesting di CarbonPilot, come richiesto nel prompt originale. Il sistema esegue:

- **Pulizia completa database** ad ogni iterazione
- **Generazione seed dati** realistici e diversificati
- **Test algoritmo OR-Tools** con scenari multipli
- **Validazione vincoli fisici** (peso, superficie, valvole)
- **Test comportamento su 2 piani**
- **Rilevamento errori** e dati corrotti
- **Report dettagliati** con diagnostica completa

## 🎯 Obiettivi del Test

Il sistema è progettato per:

1. **Validare l'algoritmo di nesting** in condizioni reali e stressanti
2. **Identificare vulnerabilità** e punti di miglioramento
3. **Testare la gestione degli errori** e dati inconsistenti
4. **Verificare l'utilizzo del secondo piano** delle autoclavi
5. **Fornire metriche di prestazione** dettagliate
6. **Generare raccomandazioni** per ottimizzazioni

## 📁 Struttura File

```
├── run_complete_nesting_validation.py    # 🚀 Script principale orchestratore
├── stress_test_nesting_complete_v2.py    # 🧪 Engine stress test nesting
├── fix_catalog_structure.py              # 🔧 Correzione struttura catalogo
└── README_STRESS_TEST_NESTING_V2.md     # 📖 Questa documentazione
```

## 🚀 Utilizzo Rapido

### Esecuzione Completa (Raccomandato)

```bash
# Esegue l'intero processo di validazione
python run_complete_nesting_validation.py
```

Questo script esegue automaticamente:
1. Correzione struttura catalogo
2. Stress test nesting (5 iterazioni)
3. Analisi risultati
4. Generazione report finale

### Esecuzione Singoli Componenti

```bash
# Solo correzione catalogo
python fix_catalog_structure.py

# Solo stress test nesting
python stress_test_nesting_complete_v2.py
```

## 📊 Configurazione Test

Il sistema è configurabile tramite la classe `TestConfig`:

```python
config = TestConfig(
    num_iterazioni=5,              # Numero iterazioni test
    num_odl_per_iterazione=15,     # ODL per iterazione
    percentuale_odl_validi=0.6,    # 60% ODL validi
    percentuale_odl_borderline=0.3, # 30% ODL borderline
    percentuale_odl_errati=0.1,    # 10% ODL errati
    abilita_secondo_piano=True,    # Test secondo piano
    log_dettagliato=True           # Logging verboso
)
```

## 🔄 Flusso del Test

### Fase 1: Correzione Catalogo 🔧

- **Analizza struttura** attuale del catalogo
- **Identifica colonne problematiche** (altezza, areacm2)
- **Verifica relazioni** catalogo-tool
- **Corregge dati inconsistenti**
- **Testa calcolo area** dai tools

### Fase 2: Stress Test Nesting 🧪

Per ogni iterazione:

1. **Pulizia completa database**
   ```sql
   DELETE FROM nesting_results;
   DELETE FROM reports;
   DELETE FROM odl;
   DELETE FROM parti;
   DELETE FROM tools;
   DELETE FROM cataloghi;
   DELETE FROM autoclavi;
   DELETE FROM cicli_cura;
   ```

2. **Creazione seed dati**
   - 2 autoclavi (standard + dual-level)
   - 3 cicli di cura diversi
   - 8 cataloghi con tools associati
   - 15 ODL diversificati per scenario

3. **Scenari ODL testati**:
   - **60% ODL validi**: Configurazione ottimale
   - **30% ODL borderline**: Dimensioni/peso al limite
   - **10% ODL errati**: Senza tool, oversize, stato errato

4. **Esecuzione algoritmo OR-Tools**
   - Validazione preliminare ODL
   - Calcolo posizionamento 2D
   - Verifica vincoli fisici
   - Assegnazione autoclavi

5. **Analisi risultati**
   - Nesting creati vs falliti
   - ODL assegnati vs scartati
   - Utilizzo secondo piano
   - Errori algoritmo

### Fase 3: Analisi Finale 📊

- **Prestazioni algoritmo**: Tasso successo, efficienza
- **Stabilità sistema**: Numero errori, robustezza
- **Utilizzo risorse**: Sfruttamento spazio, secondo piano

### Fase 4: Report Finale 📄

- **Report JSON completo** con tutti i dati
- **Report testuale riassuntivo** per lettura rapida
- **Raccomandazioni specifiche** per miglioramenti

## 📈 Metriche Monitorate

### Prestazioni Algoritmo
- **Tasso successo nesting**: % nesting creati con successo
- **Efficienza assegnazione ODL**: % ODL assegnati vs totali
- **Tempo esecuzione**: Performance algoritmo OR-Tools

### Stabilità Sistema
- **Numero errori**: Errori durante esecuzione
- **Robustezza**: Gestione dati corrotti/inconsistenti
- **Recupero errori**: Capacità di continuare dopo errori

### Utilizzo Risorse
- **Sfruttamento superficie**: % utilizzo piano autoclavi
- **Utilizzo secondo piano**: Frequenza uso dual-level
- **Distribuzione carico**: Bilanciamento tra autoclavi

## 🧪 Esempi di Output

### Log Durante Esecuzione
```bash
🧪 ITERAZIONE #1/5
✔️ Nesting #1 creato su AUTO-001-STANDARD
✔️ ODL assegnati: [3, 5, 6, 8, 12]
⚠️ ODL 2 escluso: ciclo non compatibile
❌ Nesting #2 fallito: superficie insufficiente
✔️ Piano 2 utilizzato su AUTO-002-DUAL-LEVEL
```

### Report Finale
```
📊 RISULTATI CHIAVE:
   • Tasso successo: 85.2%
   • Efficienza ODL: 78.4%
   • Stabilità: BUONA
   • Valutazione: OTTIME

💡 RACCOMANDAZIONI PRINCIPALI:
   • ✅ Sistema pronto per produzione
   • 📈 Ottimizzare utilizzo secondo piano
   • 🔧 Migliorare validazione ODL borderline
```

## ⚠️ Correzioni Implementate

### Problema Catalogo Risolto
Come richiesto nel prompt, il sistema corregge:

- **Rimozione campi non necessari** dal catalogo (altezza, areacm2)
- **Calcolo area dai tools**: `area_cm2` calcolata da `tool.lunghezza_piano * tool.larghezza_piano`
- **Validazione relazioni**: Verifica collegamento catalogo-parte-tool
- **Pulizia dati inconsistenti**: Correzione automatica valori errati

### Validazione Algoritmo
- **Controlli pre-nesting**: Validazione ODL, tool, cicli di cura
- **Vincoli fisici**: Peso, superficie, numero valvole
- **Posizionamento 2D**: Algoritmo bin packing realistico
- **Gestione errori**: Logging dettagliato fallimenti OR-Tools

## 🔧 Troubleshooting

### Errori Comuni

1. **Import Error**: Verificare path backend
   ```bash
   export PYTHONPATH="${PYTHONPATH}:./backend"
   ```

2. **Database Lock**: Chiudere connessioni attive
   ```python
   db.close()
   ```

3. **OR-Tools Error**: Verificare installazione
   ```bash
   pip install ortools
   ```

### Debug Mode

Per debug dettagliato:
```python
config.log_dettagliato = True
logging.getLogger().setLevel(logging.DEBUG)
```

## 📋 Requisiti Sistema

### Dipendenze Python
```
sqlalchemy>=1.4.0
ortools>=9.0.0
python-dateutil>=2.8.0
```

### Risorse Hardware
- **RAM**: Minimo 2GB per test completi
- **Storage**: 500MB per database e report
- **CPU**: Algoritmo OR-Tools CPU-intensive

## 🎯 Risultati Attesi

### Sistema Funzionante
- **Tasso successo > 80%**: Algoritmo efficace
- **Errori < 5**: Sistema stabile
- **Utilizzo secondo piano > 20%**: Ottimizzazione spazio

### Sistema da Ottimizzare
- **Tasso successo < 70%**: Rivedere parametri algoritmo
- **Errori > 10**: Problemi stabilità
- **Utilizzo secondo piano = 0%**: Logica assegnazione errata

## 📞 Supporto

Per problemi o domande:
1. Controllare log dettagliati
2. Verificare configurazione database
3. Testare singoli componenti
4. Consultare report errori generati

---

**Autore**: Sistema CarbonPilot  
**Data**: 2025-01-27  
**Versione**: 2.0 
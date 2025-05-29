# 🎛️ Parametri Regolabili Nesting - Guida Utente

## 📋 Introduzione

Il sistema di parametri regolabili per il nesting permette di configurare in tempo reale l'algoritmo di ottimizzazione per adattarlo a diverse esigenze operative. Questa funzionalità offre un controllo granulare sui criteri di posizionamento degli ODL nelle autoclavi.

## 🚀 Come Utilizzare

### 1. Accesso al Pannello Parametri

Il pannello dei parametri è integrato nell'interfaccia di nesting e può essere:
- **Espanso/Collassato**: Clicca sull'header del pannello
- **Configurato**: Modifica i valori nei campi numerici
- **Validato**: Controllo automatico dei range di valori

### 2. Configurazione Parametri

#### 🔧 Distanza Minima Tool (0.1 - 10.0 cm)
- **Cosa fa**: Definisce lo spazio minimo tra i tool durante il posizionamento
- **Quando modificare**: 
  - Aumenta per tool delicati o con parti sporgenti
  - Diminuisci per massimizzare l'utilizzo dello spazio
- **Esempio**: 2.0 cm per operazioni standard, 3.0 cm per tool complessi

#### 🛡️ Padding Bordo Autoclave (0.1 - 5.0 cm)
- **Cosa fa**: Margine di sicurezza dal bordo dell'autoclave
- **Quando modificare**:
  - Aumenta per autoclavi con irregolarità sui bordi
  - Diminuisci per massimizzare l'area utilizzabile
- **Esempio**: 1.5 cm standard, 2.5 cm per autoclavi datate

#### ⚖️ Margine Sicurezza Peso (0 - 50%)
- **Cosa fa**: Percentuale di margine sul peso massimo dell'autoclave
- **Quando modificare**:
  - Aumenta per carichi critici o autoclavi sensibili
  - Diminuisci per massimizzare il carico
- **Esempio**: 10% standard, 20% per operazioni critiche

#### 🎯 Priorità Minima ODL (1 - 10)
- **Cosa fa**: Filtra gli ODL considerando solo quelli con priorità >= soglia
- **Quando modificare**:
  - Aumenta per focalizzarsi su ODL urgenti
  - Mantieni a 1 per considerare tutti gli ODL
- **Esempio**: 1 per operazioni normali, 5+ per situazioni urgenti

#### 📊 Efficienza Minima (30 - 95%)
- **Cosa fa**: Soglia minima di efficienza per accettare un nesting
- **Quando modificare**:
  - Aumenta per garantire utilizzo ottimale dello spazio
  - Diminuisci se è importante processare anche con bassa efficienza
- **Esempio**: 60% standard, 80% per ottimizzazione massima

### 3. Workflow Operativo

#### Fase 1: Configurazione
1. **Apri il pannello parametri** (se collassato)
2. **Modifica i valori** secondo le tue esigenze
3. **Verifica la validazione** (messaggi di errore in rosso)
4. **Applica i parametri** (pulsante "Applica Parametri")

#### Fase 2: Preview
1. **Genera preview** (pulsante nel pannello o area principale)
2. **Analizza i risultati**:
   - Numero ODL disponibili
   - Gruppi per ciclo di cura
   - Autoclavi compatibili
3. **Valuta se i parametri sono appropriati**

#### Fase 3: Generazione Nesting
1. **Genera nesting automatico** con i parametri configurati
2. **Analizza i risultati**:
   - Numero nesting creati
   - ODL processati vs esclusi
   - Efficienza media ottenuta
3. **Itera se necessario** modificando i parametri

## 📊 Interpretazione Risultati

### Metriche Preview
- **ODL Totali**: Quanti ODL sono disponibili con i parametri attuali
- **Gruppi Cicli**: Raggruppamento per compatibilità ciclo di cura
- **Autoclavi Disponibili**: Quante autoclavi possono essere utilizzate

### Metriche Nesting
- **Efficienza**: Percentuale di utilizzo dell'area autoclave
- **Area Utilizzata**: Spazio effettivamente occupato dai tool
- **Peso Totale**: Carico totale rispetto al limite dell'autoclave
- **ODL Inclusi/Esclusi**: Quanti ODL sono stati processati

## 🎯 Scenari d'Uso Comuni

### Scenario 1: Massima Efficienza
```
Distanza Tool: 1.5 cm (ridotta)
Padding Autoclave: 1.0 cm (ridotto)
Margine Peso: 5% (ridotto)
Priorità Minima: 1 (tutti gli ODL)
Efficienza Minima: 80% (alta)
```
**Risultato**: Nesting molto efficienti ma più selettivi

### Scenario 2: Massima Sicurezza
```
Distanza Tool: 3.0 cm (aumentata)
Padding Autoclave: 2.5 cm (aumentato)
Margine Peso: 20% (aumentato)
Priorità Minima: 1 (tutti gli ODL)
Efficienza Minima: 50% (ridotta)
```
**Risultato**: Operazioni più sicure ma meno efficienti

### Scenario 3: ODL Urgenti
```
Distanza Tool: 2.0 cm (standard)
Padding Autoclave: 1.5 cm (standard)
Margine Peso: 10% (standard)
Priorità Minima: 7 (alta)
Efficienza Minima: 60% (standard)
```
**Risultato**: Focus su ODL ad alta priorità

### Scenario 4: Recupero Spazio
```
Distanza Tool: 1.0 cm (minima)
Padding Autoclave: 0.5 cm (minimo)
Margine Peso: 0% (nessun margine)
Priorità Minima: 1 (tutti gli ODL)
Efficienza Minima: 30% (bassa)
```
**Risultato**: Massimo utilizzo spazio, attenzione alla sicurezza

## ⚠️ Avvertenze e Best Practices

### Sicurezza
- **Non ridurre eccessivamente** distanze e margini per tool delicati
- **Monitorare sempre** i risultati prima di procedere con la cura
- **Verificare compatibilità** dei cicli di cura per ogni gruppo

### Performance
- **Parametri troppo restrittivi** possono non generare nesting
- **Efficienza troppo alta** può escludere molti ODL
- **Testare sempre** con preview prima della generazione finale

### Qualità
- **Bilanciare efficienza e sicurezza** secondo le esigenze operative
- **Documentare configurazioni** che funzionano bene per scenari specifici
- **Monitorare risultati** per ottimizzare i parametri nel tempo

## 🔧 Risoluzione Problemi

### Problema: Nessun Nesting Generato
**Possibili Cause**:
- Efficienza minima troppo alta
- Priorità minima troppo alta (esclude troppi ODL)
- Parametri di sicurezza troppo restrittivi

**Soluzioni**:
- Ridurre efficienza minima
- Abbassare priorità minima
- Ridurre margini di sicurezza

### Problema: Efficienza Troppo Bassa
**Possibili Cause**:
- Distanze tool troppo grandi
- Padding autoclave eccessivo
- ODL con dimensioni non ottimali

**Soluzioni**:
- Ridurre distanza minima tool
- Ridurre padding bordo autoclave
- Verificare dimensioni tool nel database

### Problema: Troppi ODL Esclusi
**Possibili Cause**:
- Margine peso troppo conservativo
- Area autoclave insufficiente con padding
- Priorità minima troppo alta

**Soluzioni**:
- Ridurre margine sicurezza peso
- Ridurre padding bordo autoclave
- Abbassare priorità minima

## 📞 Supporto

Per problemi o domande sui parametri di nesting:
1. **Consulta questa guida** per scenari comuni
2. **Testa con preview** prima di generare nesting definitivi
3. **Documenta configurazioni** che funzionano per riferimento futuro
4. **Contatta il supporto tecnico** per problemi persistenti

---

**Versione**: 1.0  
**Data**: 2025-01-28  
**Compatibilità**: CarbonPilot v2.0+ 
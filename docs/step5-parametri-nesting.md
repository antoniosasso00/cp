# 🎛️ Step 5 - Parametri Regolabili Nesting

## 📋 Panoramica

Lo Step 5 implementa un sistema completo di parametri regolabili per l'algoritmo di nesting, permettendo agli utenti di configurare in tempo reale i parametri dell'ottimizzazione per adattarsi a diverse esigenze operative.

## 🎯 Obiettivi Raggiunti

### ✅ Backend - Algoritmo Parametrizzato
- **Parametri Configurabili**: 5 parametri chiave per l'ottimizzazione
- **Validazione Robusta**: Controlli di range e coerenza
- **API RESTful**: Endpoint dedicati per gestione parametri
- **Algoritmo Flessibile**: Adattamento dinamico ai parametri

### ✅ Frontend - Interfaccia Intuitiva
- **Pannello Parametri**: UI collassabile per configurazione
- **Validazione Real-time**: Feedback immediato su valori inseriti
- **Preview Dinamica**: Anteprima risultati con parametri attuali
- **Integrazione Completa**: Workflow completo dalla configurazione ai risultati

## 🏗️ Architettura Implementata

### Backend Components

#### 1. Schema Parametri (`backend/schemas/nesting.py`)
```python
class NestingParameters(BaseModel):
    distanza_minima_tool_cm: float = Field(default=2.0, ge=0.1, le=10.0)
    padding_bordo_autoclave_cm: float = Field(default=1.5, ge=0.1, le=5.0)
    margine_sicurezza_peso_percent: float = Field(default=10.0, ge=0.0, le=50.0)
    priorita_minima: int = Field(default=1, ge=1, le=10)
    efficienza_minima_percent: float = Field(default=60.0, ge=30.0, le=95.0)
```

#### 2. Algoritmo Ottimizzato (`backend/nesting_optimizer/auto_nesting.py`)
```python
class NestingOptimizer:
    def __init__(self, db: Session, parameters: Optional[NestingParameters] = None):
        self.parameters = parameters or NestingParameters()
        
    def calculate_effective_autoclave_area(self, autoclave: Autoclave) -> float:
        # Considera padding configurabile
        padding_mm = self.parameters.padding_bordo_autoclave_cm * 10
        effective_length = max(0, autoclave.lunghezza - (2 * padding_mm))
        effective_width = max(0, autoclave.larghezza_piano - (2 * padding_mm))
        return (effective_length * effective_width) / 100
```

#### 3. API Endpoints (`backend/api/routers/nesting.py`)
- `GET /parameters` - Recupera parametri di default
- `POST /parameters/validate` - Valida parametri forniti
- `POST /preview-with-parameters` - Preview con parametri personalizzati
- `POST /automatic` - Nesting automatico con parametri

### Frontend Components

#### 1. Pannello Parametri (`frontend/src/components/nesting/NestingParametersPanel.tsx`)
- **Accordion UI**: Pannello collassabile per configurazione
- **Validazione Real-time**: Controllo immediato dei valori
- **Gestione Stato**: Tracking modifiche non salvate
- **Azioni**: Applica, Reset, Preview

#### 2. Hook Personalizzato (`frontend/src/hooks/useNestingParameters.ts`)
- **Gestione Stato**: Parametri, loading, errori
- **API Integration**: Metodi per tutte le operazioni
- **Error Handling**: Gestione errori centralizzata

#### 3. Componente Integrato (`frontend/src/components/nesting/NestingWithParameters.tsx`)
- **Layout Responsive**: Grid layout adattivo
- **Workflow Completo**: Dalla configurazione ai risultati
- **Visualizzazione Avanzata**: Metriche e statistiche dettagliate

## 🔧 Parametri Configurabili

### 1. Distanza Minima Tool (0.1 - 10.0 cm)
- **Scopo**: Spazio minimo tra tool durante posizionamento
- **Impatto**: Sicurezza operativa e prevenzione interferenze
- **Default**: 2.0 cm

### 2. Padding Bordo Autoclave (0.1 - 5.0 cm)
- **Scopo**: Margine di sicurezza dal bordo autoclave
- **Impatto**: Area effettiva utilizzabile per nesting
- **Default**: 1.5 cm

### 3. Margine Sicurezza Peso (0 - 50%)
- **Scopo**: Percentuale di margine sul peso massimo autoclave
- **Impatto**: Sicurezza carico e prevenzione sovraccarichi
- **Default**: 10%

### 4. Priorità Minima ODL (1 - 10)
- **Scopo**: Soglia minima priorità ODL da considerare
- **Impatto**: Focalizzazione su ODL più importanti
- **Default**: 1 (tutti gli ODL)

### 5. Efficienza Minima (30 - 95%)
- **Scopo**: Soglia minima efficienza per accettare nesting
- **Impatto**: Qualità risultati e utilizzo ottimale spazio
- **Default**: 60%

## 🎨 Interfaccia Utente

### Pannello Parametri
- **Design**: Card collassabile con accordion
- **Validazione**: Controlli real-time con messaggi errore
- **Feedback**: Badge per modifiche non salvate
- **Azioni**: Pulsanti per applicare, reset, preview

### Area Principale
- **Layout**: Grid responsive 1/3 parametri, 2/3 contenuto
- **Azioni**: Pulsanti per preview e generazione nesting
- **Risultati**: Cards con statistiche colorate e metriche

### Visualizzazione Risultati
- **Preview**: Statistiche ODL, gruppi, autoclavi compatibili
- **Nesting**: Risultati dettagliati con efficienza e utilizzo
- **Metriche**: Cards colorate per diversi tipi di dati

## 🚀 Benefici Implementati

### 1. Flessibilità Operativa
- **Configurazione Dinamica**: Parametri modificabili senza riavvio
- **Adattamento Scenari**: Parametri diversi per situazioni diverse
- **Controllo Qualità**: Soglie configurabili per risultati

### 2. Miglioramento Algoritmo
- **Precisione Calcoli**: Area effettiva vs nominale
- **Gestione Priorità**: Focus su ODL importanti
- **Controllo Efficienza**: Evita nesting poco efficienti
- **Sicurezza Fisica**: Margini per operazioni sicure

### 3. Esperienza Utente
- **Controllo Granulare**: Fine-tuning algoritmo
- **Preview Immediata**: Visualizzazione effetti parametri
- **Feedback Chiaro**: Risultati dettagliati con metriche
- **Interfaccia Intuitiva**: Design pulito e organizzato

## 🔄 Workflow Utente

### 1. Configurazione Parametri
1. Apri pannello parametri (collassabile)
2. Modifica valori desiderati con validazione real-time
3. Applica parametri (badge indica modifiche non salvate)

### 2. Preview Risultati
1. Clicca "Genera Preview" nel pannello o area principale
2. Visualizza statistiche ODL disponibili
3. Controlla compatibilità autoclavi per ogni gruppo

### 3. Generazione Nesting
1. Clicca "Genera Nesting" con parametri configurati
2. Visualizza risultati dettagliati con metriche
3. Analizza efficienza e utilizzo per ogni nesting

### 4. Iterazione e Ottimizzazione
1. Modifica parametri basandosi sui risultati
2. Rigenera preview per vedere effetti
3. Ottimizza fino a risultati soddisfacenti

## 📊 Metriche e Monitoraggio

### Preview Metrics
- **ODL Totali**: Numero ODL disponibili con parametri attuali
- **Gruppi Cicli**: Numero gruppi per ciclo di cura
- **Autoclavi Disponibili**: Autoclavi compatibili
- **Dettagli Gruppi**: Area, peso, autoclavi compatibili per gruppo

### Nesting Results
- **Nesting Creati**: Numero nesting generati con successo
- **ODL Processati**: ODL inclusi nei nesting
- **ODL Esclusi**: ODL non inclusi con motivi
- **Autoclavi Utilizzate**: Numero autoclavi coinvolte
- **Efficienza Media**: Efficienza media dei nesting generati

## 🔧 Configurazione e Deployment

### Backend Setup
1. Schema parametri già integrati in `schemas/nesting.py`
2. Algoritmo aggiornato in `nesting_optimizer/auto_nesting.py`
3. API endpoints disponibili in `api/routers/nesting.py`

### Frontend Setup
1. Componenti disponibili in `components/nesting/`
2. Hook personalizzato in `hooks/useNestingParameters.ts`
3. Integrazione completa in `NestingWithParameters.tsx`

### Testing
- **Backend**: Test parametri, validazione, algoritmo
- **Frontend**: Test componenti, hook, integrazione
- **E2E**: Test workflow completo utente

## 🎯 Prossimi Sviluppi

### Possibili Estensioni
1. **Preset Parametri**: Configurazioni salvate per scenari comuni
2. **Parametri Avanzati**: Algoritmi di posizionamento, strategie ottimizzazione
3. **Analytics**: Storico parametri e risultati per analisi trend
4. **Machine Learning**: Suggerimenti parametri basati su storico

### Ottimizzazioni
1. **Performance**: Cache risultati preview per parametri identici
2. **UX**: Slider per parametri numerici, tooltip esplicativi
3. **Validazione**: Controlli incrociati tra parametri correlati
4. **Monitoring**: Metriche performance algoritmo con diversi parametri

---

**Implementazione completata**: ✅ Step 5 - Parametri Regolabili Nesting
**Data**: 2025-01-28
**Stato**: Pronto per testing e deployment 
# 🔴 MODULI BACKEND NON INTEGRATI NEL FRONTEND

## 📋 Elenco Completo Moduli Disponibili ma Non Utilizzati

### 🔴 **1. Reports (`/v1/reports`)**
**Stato**: Completamente sviluppato ma NON integrato
**Funzionalità**:
- Generazione automatica report PDF per cicli di cura completati
- Lista report con filtri avanzati (tipo, data, utente)
- Download report tramite ID o filename
- Auto-generazione batch report

**Endpoint Disponibili**:
```
POST   /v1/reports/generate          - Genera nuovo report
GET    /v1/reports/                  - Lista report con filtri
GET    /v1/reports/{report_id}/download - Scarica report per ID
GET    /v1/reports/download/{filename} - Scarica report per nome
POST   /v1/reports/auto-generate    - Auto-genera report mancanti
```

**File Backend**: `backend/api/routers/reports.py` (543 linee)

---

### 🔴 **2. ODL Monitoring (`/v1/odl-monitoring`)**
**Stato**: Sistema avanzato NON integrato
**Funzionalità**:
- Statistiche monitoraggio avanzate ODL
- Summary per periodo/filtri
- Sistema di alert automatici
- Tracking stato dettagliato

**Endpoint Disponibili**:
```
GET    /v1/monitoring/stats          - Statistiche generali
GET    /v1/monitoring/summary        - Summary ODL
GET    /v1/monitoring/alerts         - Alert automatici
POST   /v1/monitoring/logs           - Crea log monitoraggio
```

**File Backend**: `backend/api/routers/odl_monitoring.py` (567 linee)

---

### 🔴 **3. Admin (`/v1/admin`)**
**Stato**: Funzionalità critiche NON accessibili dal frontend
**Funzionalità**:
- Backup completo database in JSON
- Ripristino database da backup
- Gestione manutenzione sistema

**Endpoint Disponibili**:
```
GET    /v1/admin/backup             - Esporta database
POST   /v1/admin/restore            - Ripristina database
```

**File Backend**: `backend/api/routers/admin.py` (403 linee)

---

### 🔴 **4. System Logs (`/v1/system-logs`)**
**Stato**: Sistema logging avanzato NON utilizzato
**Funzionalità**:
- Log dettagliati di sistema con livelli
- Filtraggio per entità, utente, azione
- Analisi operazioni sistema

**File Backend**: `backend/api/routers/system_logs.py` (206 linee)

---

### 🔴 **5. Schedules (`/v1/schedules`)**
**Stato**: Sistema schedulazione completo NON integrato
**Funzionalità**:
- Schedulazione automatica ODL per autoclavi
- Schedulazioni ricorrenti
- Stima tempi produzione
- Gestione calendario produzione

**Endpoint Disponibili**:
```
GET    /v1/schedules/                     - Lista schedulazioni
POST   /v1/schedules/                     - Crea schedulazione
GET    /v1/schedules/auto-generate        - Auto-genera schedulazioni
POST   /v1/schedules/recurring            - Crea schedulazione ricorrente
GET    /v1/schedules/production-times/estimate - Stima tempi
```

**File Backend**: `backend/api/routers/schedule.py` (420 linee)

---

### 🔴 **6. Tempo Fasi (`/v1/tempo-fasi`)**
**Stato**: Monitoraggio tempi dettagliato NON utilizzato
**Funzionalità**:
- Tracking preciso tempi per ogni fase ODL
- Statistiche performance per fase
- Previsioni tempi basate su storico

**File Backend**: `backend/api/routers/tempo_fasi.py` (146 linee)

---

### 🔴 **7. Produzione (`/v1/produzione`)**
**Stato**: Dashboard produzione avanzata NON integrata
**Funzionalità**:
- Overview completa stato produzione
- Statistiche tempo reale
- Health check sistema

**Endpoint Disponibili**:
```
GET    /v1/produzione/odl           - ODL in produzione
GET    /v1/produzione/statistiche   - Statistiche generali
GET    /v1/produzione/health        - Health check
```

**File Backend**: `backend/api/routers/produzione.py` (174 linee)

---

## 🎯 **RACCOMANDAZIONI**

### ✅ **Integrare Immediatamente**:
1. **Reports** - Fondamentale per audit e compliance
2. **Admin** - Critico per backup/ripristino
3. **Produzione** - Dashboard operativa essenziale

### ⚠️ **Integrare con Cautela**:
1. **ODL Monitoring** - Può sovrapporre funzionalità esistenti
2. **Schedules** - Complesso, richiede UX dedicata

### 🔄 **Valutare**:
1. **System Logs** - Utile solo per debugging avanzato
2. **Tempo Fasi** - Nice-to-have, non critico

## 📁 **File da Spostare se Non Utilizzati**
- `backend/api/routers/nesting_temp.py` (se sostituito da batch_nesting)
- Moduli di test obsoleti
- Servizi legacy non referenziati

## 🔧 **Prossimi Passi**
1. Implementare switch status batch nel frontend
2. Integrare moduli critici (Reports, Admin, Produzione)  
3. Spostare file obsoleti in questa cartella
4. Aggiornare documentazione API 
# 📂 Context Summary Admin - CarbonPilot

> **Documento di analisi completa del progetto CarbonPilot**  
> Estratto direttamente dal codice esistente per guidare il refactoring della sezione `admin`

---

## 📌 Sezione 1: Struttura e Architettura

### 🗂️ Mappa Completa delle Directory

```
CarbonPilot/
├── backend/                          # API FastAPI + SQLAlchemy
│   ├── api/routers/                  # Router API organizzati per modulo
│   │   ├── admin.py                  # ✅ API admin (backup/restore/database)
│   │   ├── catalogo.py               # ✅ CRUD catalogo completo
│   │   ├── parte.py                  # ✅ CRUD parti
│   │   ├── tool.py                   # ✅ CRUD tools
│   │   ├── autoclave.py              # ✅ CRUD autoclavi
│   │   ├── ciclo_cura.py             # ✅ CRUD cicli di cura
│   │   ├── odl.py                    # ✅ CRUD ODL complesso (1326 righe)
│   │   ├── batch_nesting.py          # ✅ API nesting e batch
│   │   ├── schedule.py               # ✅ Pianificazione
│   │   ├── reports.py                # ✅ Generazione report
│   │   └── system_logs.py            # ✅ Logging sistema
│   ├── models/                       # 14 modelli SQLAlchemy
│   │   ├── autoclave.py              # Modello autoclavi
│   │   ├── catalogo.py               # Modello catalogo
│   │   ├── parte.py                  # Modello parti
│   │   ├── tool.py                   # Modello tools
│   │   ├── odl.py                    # Modello ODL
│   │   ├── nesting_result.py         # Modello nesting
│   │   └── [altri 8 modelli]
│   └── services/                     # Servizi business logic
│
├── frontend/                         # Next.js 14 + TypeScript + Tailwind
│   └── src/
│       ├── app/dashboard/            # Routing basato su ruoli
│       │   ├── layout.tsx            # ✅ Sidebar dinamica per ruoli
│       │   ├── page.tsx              # ✅ Dashboard principale con routing
│       │   ├── admin/                # ⚠️ Sezione admin INCOMPLETA
│       │   │   ├── logs/             # Pagina logs
│       │   │   └── impostazioni/     # Impostazioni admin
│       │   ├── management/           # Sezione management
│       │   │   ├── tools/            # ✅ Gestione tools
│       │   │   ├── reports/          # ✅ Reports
│       │   │   └── odl-monitoring/   # ✅ Monitoraggio ODL
│       │   ├── shared/               # Sezioni condivise
│       │   │   ├── catalog/          # ✅ Gestione catalogo
│       │   │   └── odl/              # ✅ Gestione ODL
│       │   └── curing/               # Sezione curing
│       │       ├── nesting/          # ✅ Nesting e batch
│       │       ├── autoclavi/        # ✅ Gestione autoclavi
│       │       └── cicli-cura/       # ✅ Cicli di cura
│       ├── components/               # Componenti riutilizzabili
│       │   ├── ui/                   # shadcn/ui components
│       │   ├── dashboard/            # Componenti dashboard specifici
│       │   │   ├── DashboardAdmin.tsx    # ✅ Dashboard admin
│       │   │   ├── DashboardManagement.tsx
│       │   │   ├── DashboardCuring.tsx
│       │   │   └── DashboardCleanRoom.tsx
│       │   ├── batch-nesting/        # Componenti nesting
│       │   └── odl-monitoring/       # Componenti monitoraggio
│       └── hooks/                    # Custom hooks
│           └── useUserRole.ts        # ✅ Gestione ruoli utente
│
└── tools/                            # Script di supporto
    ├── print_schema_summary.py       # ✅ Stampa schema DB
    ├── seed_full.py                  # ✅ Seed dati completi
    └── snapshot_structure.py         # ✅ Snapshot struttura
```

### 🔐 Gestione Ruoli e Permessi

**Ruoli definiti in `useUserRole.ts`:**
```typescript
export type UserRole = 'ADMIN' | 'Management' | 'Clean Room' | 'Curing'
```

**Permessi Admin (da `layout.tsx`):**
- ✅ Accesso a TUTTE le sezioni
- ✅ Gestione ODL completa
- ✅ Monitoraggio sistema
- ✅ Gestione catalogo, parti, tools
- ✅ Configurazione autoclavi e cicli
- ✅ Reports e statistiche
- ✅ Nesting e batch management

**Routing condizionato per ruolo:**
- Sidebar dinamica filtra voci per ruolo
- Componenti dashboard caricati dinamicamente
- Protezione a livello di route

---

## 👥 Sezione 2: Ruolo `admin` – Permessi e Flussi

### 📋 Pagine Accessibili all'Admin

**Dashboard Principale (`DashboardAdmin.tsx`):**
- ✅ KPI sistema in tempo reale
- ✅ Sezioni amministrative organizzate
- ✅ Shortcut azioni rapide
- ✅ Storico ODL con filtri avanzati

**Sezioni Admin Specifiche:**
1. **Gestione Utenti** → `/dashboard/users` ❌ NON IMPLEMENTATA
2. **Configurazioni Sistema** → `/dashboard/impostazioni` ⚠️ PARZIALE
3. **Monitoraggio Sistema** → `/dashboard/monitoring` ✅ FUNZIONANTE
4. **Database Management** → `/dashboard/database` ❌ NON IMPLEMENTATA
5. **Reports Avanzati** → `/dashboard/reports` ✅ FUNZIONANTE
6. **Audit & Logs** → `/dashboard/audit` ⚠️ PARZIALE

### 🔗 Collegamenti tra Pagine

**Flusso Principale Admin:**
```
Dashboard Admin → Sezioni Specifiche → CRUD Operations
     ↓
Sidebar Navigation (sempre visibile)
     ↓
Breadcrumb Navigation (mancante in alcune pagine)
```

**Collegamenti Funzionanti:**
- ✅ Dashboard → Catalogo → CRUD completo
- ✅ Dashboard → Tools → CRUD completo  
- ✅ Dashboard → ODL → Monitoraggio avanzato
- ✅ Dashboard → Nesting → Gestione batch
- ✅ Dashboard → Reports → Generazione PDF

**Collegamenti Rotti/Mancanti:**
- ❌ Dashboard → Gestione Utenti (404)
- ❌ Dashboard → Database Management (404)
- ⚠️ Dashboard → Audit Logs (parziale)

### 🛠️ CRUD Disponibili

**Completamente Implementati:**
- ✅ **Catalogo**: Create, Read, Update, Delete + ricerca avanzata
- ✅ **Tools**: CRUD completo + gestione disponibilità
- ✅ **Autoclavi**: CRUD + configurazione parametri
- ✅ **Cicli Cura**: CRUD + parametri tecnici
- ✅ **ODL**: CRUD complesso + workflow stati
- ✅ **Parti**: CRUD + associazioni catalogo/cicli

**Parzialmente Implementati:**
- ⚠️ **Nesting Results**: Read + Update (no Delete per integrità)
- ⚠️ **Schedule**: Create + Read (Update limitato)

**Mancanti:**
- ❌ **Utenti**: Nessun CRUD implementato
- ❌ **Configurazioni Sistema**: Solo lettura

---

## 💻 Sezione 3: Interfaccia Utente Attuale

### 🎨 UI Framework e Componenti

**Stack Tecnologico:**
- ✅ **Next.js 14** con App Router
- ✅ **TypeScript** strict mode
- ✅ **Tailwind CSS** per styling
- ✅ **shadcn/ui** per componenti base
- ✅ **Lucide React** per icone

**Componenti UI Utilizzati:**
```typescript
// Componenti shadcn/ui attivi
- Card, CardContent, CardHeader, CardTitle
- Button, buttonVariants
- Input, Textarea
- Select, SelectContent, SelectItem, SelectTrigger, SelectValue
- Table, TableBody, TableCell, TableHead, TableHeader, TableRow
- Badge, Alert, AlertDescription
- Dialog, DialogContent, DialogHeader, DialogTitle
- DropdownMenu, DropdownMenuContent, DropdownMenuItem
- Tabs, TabsContent, TabsList, TabsTrigger
- Toast (per notifiche)
```

### 📱 Sidebar e Layout

**Sidebar Dinamica (`layout.tsx`):**
```typescript
// Struttura sidebar per ADMIN
const sidebarSections = [
  { title: "Dashboard", items: [...] },
  { title: "Gestione ODL", items: [...], roles: ['ADMIN', 'Management'] },
  { title: "CLEAN ROOM", items: [...], roles: ['ADMIN', 'Clean Room'] },
  { title: "CURING", items: [...], roles: ['ADMIN', 'Curing'] },
  { title: "Pianificazione", items: [...], roles: ['ADMIN', 'Management'] },
  { title: "Flusso Produttivo", items: [...], roles: ['ADMIN', 'Management'] },
  { title: "Amministrazione", items: [...], roles: ['ADMIN', 'Management'] }
]
```

**Caratteristiche UI:**
- ✅ Responsive design (mobile-first)
- ✅ Sidebar collassabile
- ✅ Indicatori stato attivo
- ✅ Animazioni smooth
- ✅ Dark/Light mode ready (theme-provider)

### 🎯 Dashboard Admin Attuale

**Sezioni Presenti:**
1. **Header con Badge Ruolo** ✅
2. **KPI Cards** ✅ (4 metriche principali)
3. **Sezioni Amministrative** ✅ (6 card con azioni)
4. **Shortcuts Rapidi** ✅ (componente DashboardShortcuts)
5. **Tabella ODL History** ✅ (ultimi 15 ODL)

**Dati Mostrati (reali dal DB):**
- ODL Totali / Completati
- Utilizzo Autoclavi (%)
- Nesting Attivi / Totali
- Efficienza Produzione (%)

---

## 🔄 Sezione 4: Stato delle Funzionalità

### 📊 Modulo Catalogo
- **API**: ✅ CRUD completo (`catalogo.py` - 237 righe)
- **Frontend**: ✅ Interfaccia completa con ricerca e filtri
- **Collegamenti**: ✅ Integrato con Parti
- **Seed Data**: ✅ Dati di test disponibili

### 🔧 Modulo Tool
- **API**: ✅ CRUD completo (`tool.py` - 452 righe)
- **Frontend**: ✅ Gestione completa + disponibilità
- **Collegamenti**: ✅ Associato a ODL e Parti
- **Seed Data**: ✅ Tools di esempio

### 🏭 Modulo Autoclave
- **API**: ✅ CRUD completo (`autoclave.py` - 231 righe)
- **Frontend**: ✅ Configurazione parametri tecnici
- **Collegamenti**: ✅ Integrato con Nesting
- **Seed Data**: ✅ Autoclavi configurate

### ⚙️ Modulo Ciclo di Cura
- **API**: ✅ CRUD completo (`ciclo_cura.py` - 260 righe)
- **Frontend**: ✅ Gestione parametri cura
- **Collegamenti**: ✅ Associato a Parti
- **Seed Data**: ✅ Cicli standard

### 📋 Modulo ODL
- **API**: ✅ CRUD complesso (`odl.py` - 1326 righe!)
- **Frontend**: ✅ Interfaccia avanzata + workflow
- **Collegamenti**: ✅ Hub centrale del sistema
- **Seed Data**: ✅ ODL di test con stati diversi

### 🎯 Modulo Nesting
- **API**: ✅ Algoritmi complessi (`batch_nesting.py` - 682 righe)
- **Frontend**: ✅ Visualizzazione 2D + controlli
- **Collegamenti**: ✅ Integrato con ODL e Autoclavi
- **Seed Data**: ✅ Batch di esempio

### 📅 Modulo Schedule
- **API**: ✅ Pianificazione avanzata (`schedule.py` - 420 righe)
- **Frontend**: ✅ Calendario + ricorrenze
- **Collegamenti**: ✅ Integrato con ODL
- **Seed Data**: ⚠️ Limitati

### 📈 Modulo Reports
- **API**: ✅ Generazione PDF (`reports.py` - 543 righe)
- **Frontend**: ✅ Interfaccia generazione
- **Collegamenti**: ✅ Tutti i moduli
- **Seed Data**: ✅ Report di esempio

---

## 📈 Sezione 5: Dashboard Admin

### 📊 Dati Presenti (Reali dal DB)

**KPI Metriche (`useDashboardKPI` hook):**
```typescript
interface KPIData {
  odl_totali: number
  odl_finiti: number
  utilizzo_medio_autoclavi: number
  nesting_attivi: number
  nesting_totali: number
  efficienza_produzione: number
}
```

**Shortcut Attivi:**
- ✅ Nuovo ODL
- ✅ Nuovo Nesting
- ✅ Gestione Catalogo
- ✅ Monitoraggio Sistema
- ✅ Reports Rapidi

### ⚠️ Errori Noti

**Errore Select.Item:**
- ❌ **NON TROVATO** nel codice attuale
- ✅ Tutti i `SelectItem` hanno `value` prop
- ✅ Componenti Select correttamente implementati

**Problemi Dashboard:**
- ⚠️ Loading states potrebbero essere migliorati
- ⚠️ Error boundaries mancanti in alcune sezioni
- ✅ Nesting sono reali (non placeholder)

### 📊 Grafici e Visualizzazioni

**Librerie Utilizzate:**
- ✅ **Lucide React** per icone
- ✅ **CSS Grid/Flexbox** per layout
- ❌ **Nessuna libreria grafici** (Chart.js, Recharts, etc.)

**Visualizzazioni Presenti:**
- ✅ KPI Cards con trend indicators
- ✅ Tabelle con sorting/filtering
- ✅ Canvas 2D per nesting visualization
- ❌ Grafici a torta/barre mancanti

---

## 🧼 Sezione 6: Refactoring Necessario

### 🔄 Componenti Duplicati

**Identificati:**
- ⚠️ `tool.py` e `tool_simple.py` (backend/models/)
- ⚠️ Multiple versioni ODL modal (`odl-modal.tsx`, `odl-modal-improved.tsx`)
- ⚠️ Componenti nesting in `unused/` e `unused_nesting_module/`

### 📁 Pagine da Accorpare

**Opportunità di Unificazione:**
1. **Modali CRUD**: Unificare create/edit in un unico componente
2. **Dashboard Components**: Consolidare logiche comuni
3. **Form Components**: Standardizzare pattern di validazione

### 🔗 Percorsi Interrotti

**Collegamenti Rotti:**
- ❌ `/dashboard/users` → 404
- ❌ `/dashboard/database` → 404  
- ⚠️ `/dashboard/audit` → Implementazione parziale

**Redirect Mancanti:**
- ⚠️ Fallback per ruoli non autorizzati
- ⚠️ Gestione sessioni scadute

### 📂 Riorganizzazione Cartelle

**Proposta Struttura:**
```
components/
├── admin/                    # Componenti specifici admin
│   ├── UserManagement/
│   ├── SystemConfig/
│   └── DatabaseTools/
├── shared/                   # Componenti condivisi
│   ├── CRUD/                # Pattern CRUD riutilizzabili
│   ├── Forms/               # Form standardizzati
│   └── Tables/              # Tabelle con funzionalità comuni
└── archive/                 # Componenti deprecati
    ├── unused/
    └── old-versions/
```

---

## ✅ Output - Stato Attuale

### 🛠️ Parti Pronte e Funzionanti

- ✅ **Backend API**: Tutti i router principali implementati
- ✅ **Database Schema**: 14 modelli completi e relazioni
- ✅ **Autenticazione Ruoli**: Sistema ruoli funzionante
- ✅ **Sidebar Dinamica**: Navigazione basata su permessi
- ✅ **CRUD Principali**: Catalogo, Tools, Autoclavi, Cicli, ODL
- ✅ **Nesting System**: Algoritmi e visualizzazione 2D
- ✅ **Dashboard KPI**: Metriche reali dal database
- ✅ **Reports System**: Generazione PDF funzionante
- ✅ **Responsive UI**: Design mobile-first
- ✅ **TypeScript**: Tipizzazione completa

### ⚠️ Parti Incomplete o in Errore

- ⚠️ **Gestione Utenti**: API mancanti, UI non implementata
- ⚠️ **Database Management**: Solo backup/restore, manca UI
- ⚠️ **Audit Logs**: Backend presente, frontend limitato
- ⚠️ **Error Boundaries**: Mancanti in alcune sezioni
- ⚠️ **Loading States**: Inconsistenti tra componenti
- ⚠️ **Form Validation**: Pattern non standardizzati
- ⚠️ **Breadcrumbs**: Navigazione non sempre chiara

### ❌ Parti Mancanti

- ❌ **User Management UI**: Interfaccia gestione utenti
- ❌ **System Configuration UI**: Pannello configurazioni
- ❌ **Database Tools UI**: Interfaccia gestione DB
- ❌ **Advanced Analytics**: Grafici e dashboard avanzate
- ❌ **Notification System**: Sistema notifiche real-time
- ❌ **Backup Scheduler**: Pianificazione backup automatici
- ❌ **Performance Monitoring**: Metriche performance sistema
- ❌ **Security Audit**: Log sicurezza e accessi

---

## 🎯 Roadmap Refactoring Suggerita

### Fase 1: Consolidamento (Priorità Alta)
1. Rimuovere componenti duplicati
2. Standardizzare pattern CRUD
3. Implementare error boundaries
4. Unificare loading states

### Fase 2: Completamento Admin (Priorità Media)
1. Implementare User Management UI
2. Creare Database Tools interface
3. Completare Audit Logs frontend
4. Aggiungere System Configuration panel

### Fase 3: Miglioramenti UX (Priorità Bassa)
1. Aggiungere grafici avanzati
2. Implementare notifiche real-time
3. Migliorare responsive design
4. Ottimizzare performance

---

*Documento generato automaticamente dal codice esistente - CarbonPilot v1.0* 
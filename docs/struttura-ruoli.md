# Struttura Dashboard Organizzata per Ruoli - CarbonPilot

## 📋 Panoramica

Il sistema dashboard di CarbonPilot è stato riorganizzato per ruoli, creando una struttura più logica e mantenibile. Ogni ruolo ha le proprie pagine specifiche, mentre le funzionalità condivise sono centralizzate.

## 🏗️ Nuova Struttura Directory

```
frontend/src/app/dashboard/
├── page.tsx                    # Router principale (carica dashboard per ruolo)
├── layout.tsx                  # Layout principale con sidebar dinamica
├── admin/                      # 👑 Pagine specifiche ADMIN
│   ├── layout.tsx
│   └── impostazioni/
│       └── page.tsx
├── responsabile/               # 👥 Pagine specifiche RESPONSABILE
│   ├── layout.tsx
│   ├── reports/
│   ├── odl-monitoring/
│   └── statistiche/
├── laminatore/                 # 🔧 Pagine specifiche LAMINATORE
│   ├── layout.tsx
│   ├── parts/
│   ├── tools/
│   ├── produzione/
│   └── tempi/
├── autoclavista/               # 🔥 Pagine specifiche AUTOCLAVISTA
│   ├── layout.tsx
│   ├── nesting/
│   ├── autoclavi/
│   ├── cicli-cura/
│   └── schedule/
└── shared/                     # 🤝 Pagine condivise tra ruoli
    ├── layout.tsx
    ├── catalog/
    └── odl/
```

## 🎯 Mappatura Ruoli e Accessi

### 👑 ADMIN (Accesso Completo)
**Pagine Specifiche:**
- `/dashboard/admin/impostazioni` - Configurazioni di sistema

**Accesso Condiviso:**
- Tutte le pagine di tutti i ruoli
- Dashboard principale con vista admin

### 👥 RESPONSABILE (Gestione e Supervisione)
**Pagine Specifiche:**
- `/dashboard/responsabile/reports` - Reports e analytics
- `/dashboard/responsabile/odl-monitoring` - Monitoraggio ODL in tempo reale
- `/dashboard/responsabile/statistiche` - Statistiche catalogo

**Accesso Condiviso:**
- `/dashboard/shared/catalog` - Catalogo parti
- `/dashboard/shared/odl` - Gestione ODL
- Pagine laminatore e autoclavista (supervisione)

### 🔧 LAMINATORE (Produzione)
**Pagine Specifiche:**
- `/dashboard/laminatore/parts` - Gestione parti
- `/dashboard/laminatore/tools` - Tools e stampi
- `/dashboard/laminatore/produzione` - Operazioni produzione
- `/dashboard/laminatore/tempi` - Tempi e performance

**Accesso Condiviso:**
- `/dashboard/shared/catalog` - Catalogo parti
- `/dashboard/shared/odl` - ODL assegnati

### 🔥 AUTOCLAVISTA (Autoclave)
**Pagine Specifiche:**
- `/dashboard/autoclavista/nesting` - Gestione nesting
- `/dashboard/autoclavista/autoclavi` - Controllo autoclavi
- `/dashboard/autoclavista/cicli-cura` - Cicli di cura
- `/dashboard/autoclavista/schedule` - Scheduling produzione

**Accesso Condiviso:**
- `/dashboard/shared/catalog` - Catalogo parti
- `/dashboard/shared/odl` - ODL per nesting

## 🔄 Sistema di Routing Dinamico

### Dashboard Principale (`/dashboard/page.tsx`)
```typescript
switch (role) {
  case 'ADMIN': return <DashboardAdmin />
  case 'RESPONSABILE': return <DashboardResponsabile />
  case 'LAMINATORE': return <DashboardLaminatore />
  case 'AUTOCLAVISTA': return <DashboardAutoclavista />
  default: return <Redirect to="/select-role" />
}
```

### Sidebar Dinamica (`layout.tsx`)
La sidebar filtra automaticamente le voci in base al ruolo:
- **Sezione Produzione**: Catalogo, Parti, ODL, Tools, Produzione
- **Sezione Autoclave**: Nesting, Autoclavi, Cicli Cura, Scheduling
- **Sezione Controllo**: Monitoraggio, Reports, Statistiche, Impostazioni
- **Sezione Laminazione**: Tempi & Performance

## 📱 Componenti Dashboard per Ruolo

### DashboardAdmin
- Gestione utenti e sistema
- Monitoraggio completo
- Configurazioni avanzate
- Reports amministrativi

### DashboardResponsabile
- Supervisione ODL
- Gestione team
- Analytics produzione
- Controllo qualità

### DashboardLaminatore
- ODL in lavorazione
- Gestione parti e tools
- Registrazione tempi
- Performance personali

### DashboardAutoclavista
- Stato autoclavi
- Cicli programmati
- Nesting ottimizzato
- Scheduling produzione

## 🛠️ Vantaggi della Nuova Struttura

### 1. **Organizzazione Logica**
- Ogni ruolo ha le proprie pagine
- Funzionalità condivise centralizzate
- Struttura intuitiva e scalabile

### 2. **Manutenibilità**
- Codice organizzato per responsabilità
- Facile aggiunta di nuove funzionalità
- Separazione chiara delle competenze

### 3. **Performance**
- Caricamento dinamico per ruolo
- Bundle ottimizzati
- Lazy loading dei componenti

### 4. **Sicurezza**
- Controllo accessi granulare
- Validazione ruoli automatica
- Isolamento funzionalità sensibili

### 5. **UX Migliorata**
- Interfaccia specifica per ruolo
- Navigazione ottimizzata
- Contenuti rilevanti

## 🔧 Implementazione Tecnica

### Layout Gerarchici
```
DashboardLayout (principale)
├── AdminLayout
├── ResponsabileLayout
├── LaminatoreLayout
├── AutoclavistaLayout
└── SharedLayout
```

### Hook useUserRole
Gestisce automaticamente:
- Lettura ruolo da localStorage
- Validazione e persistenza
- Reindirizzamento automatico

### Sidebar Configurabile
```typescript
interface SidebarSection {
  title: string;
  items: SidebarNavItem[];
  roles?: UserRole[]; // Controllo visibilità sezione
}

interface SidebarNavItem {
  title: string;
  href: string;
  icon?: React.ReactNode;
  roles?: UserRole[]; // Controllo visibilità item
}
```

## 🚀 Prossimi Passi

1. **Test Completi**: Verificare tutte le pagine spostate
2. **Aggiornamento Link**: Controllare tutti i link interni
3. **Documentazione API**: Aggiornare endpoint se necessario
4. **Test Ruoli**: Verificare accessi per ogni ruolo
5. **Performance**: Ottimizzare caricamento componenti

## 📝 Note di Migrazione

### Modifiche URL
- `/dashboard/catalog` → `/dashboard/shared/catalog`
- `/dashboard/parts` → `/dashboard/laminatore/parts`
- `/dashboard/tools` → `/dashboard/laminatore/tools`
- `/dashboard/produzione` → `/dashboard/laminatore/produzione`
- `/dashboard/tempi` → `/dashboard/laminatore/tempi`
- `/dashboard/nesting` → `/dashboard/autoclavista/nesting`
- `/dashboard/autoclavi` → `/dashboard/autoclavista/autoclavi`
- `/dashboard/cicli-cura` → `/dashboard/autoclavista/cicli-cura`
- `/dashboard/schedule` → `/dashboard/autoclavista/schedule`
- `/dashboard/reports` → `/dashboard/responsabile/reports`
- `/dashboard/odl/monitoring` → `/dashboard/responsabile/odl-monitoring`
- `/dashboard/catalog/statistiche` → `/dashboard/responsabile/statistiche`
- `/dashboard/impostazioni` → `/dashboard/admin/impostazioni`

### Componenti Mantenuti
- Tutti i componenti dashboard esistenti
- Hook useUserRole
- Sistema di autenticazione
- API endpoints (nessuna modifica)

La nuova struttura mantiene la piena compatibilità funzionale mentre migliora significativamente l'organizzazione e la manutenibilità del codice. 
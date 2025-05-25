# Dashboard Dinamica - Sistema di Ruoli CarbonPilot

## 📋 Panoramica

Il sistema di dashboard dinamica di CarbonPilot carica automaticamente l'interfaccia appropriata in base al ruolo dell'utente, ottimizzando l'esperienza utente e le performance dell'applicazione.

## 🎯 Funzionalità Principali

### 1. Caricamento Dinamico
- **Lazy Loading**: I componenti dashboard vengono caricati solo quando necessari
- **Bundle Optimization**: Riduce la dimensione del bundle iniziale
- **Performance**: Migliora i tempi di caricamento dell'applicazione

### 2. Gestione Ruoli
- **4 Ruoli Supportati**: ADMIN, RESPONSABILE, LAMINATORE, AUTOCLAVISTA
- **Persistenza**: Il ruolo viene salvato in localStorage
- **Validazione**: Controllo automatico della validità del ruolo

### 3. Reindirizzamento Automatico
- **Ruolo Mancante**: Reindirizza a `/select-role` se nessun ruolo è impostato
- **Ruolo Invalido**: Gestisce ruoli non riconosciuti con reindirizzamento

## 🏗️ Architettura

### Struttura File
```
frontend/src/
├── app/dashboard/page.tsx          # Dashboard principale (router)
├── components/dashboard/
│   ├── DashboardAdmin.tsx          # Dashboard Amministratore
│   ├── DashboardResponsabile.tsx   # Dashboard Responsabile
│   ├── DashboardLaminatore.tsx     # Dashboard Laminatore
│   └── DashboardAutoclavista.tsx   # Dashboard Autoclavista
└── hooks/useUserRole.ts            # Hook gestione ruoli
```

### Flusso di Funzionamento

1. **Accesso a `/dashboard`**
   - La dashboard principale legge il ruolo da localStorage
   - Mostra un loading durante il caricamento

2. **Validazione Ruolo**
   - Se il ruolo è valido → carica il componente appropriato
   - Se il ruolo è mancante/invalido → reindirizza a `/select-role`

3. **Caricamento Componente**
   - Utilizza `dynamic()` di Next.js per il lazy loading
   - Mostra un loading specifico durante l'importazione del componente

## 🎨 Dashboard per Ruolo

### 👑 Dashboard Admin
**Funzionalità:**
- Gestione utenti e ruoli
- Configurazioni di sistema
- Monitoraggio e statistiche complete
- Gestione database
- Reports avanzati
- Audit e logs

**Metriche Visualizzate:**
- Utenti attivi
- Sistema uptime
- ODL totali
- Performance generale

### 👥 Dashboard Responsabile
**Funzionalità:**
- Gestione ODL e produzione
- Pianificazione attività
- Supervisione team
- Controllo qualità
- Gestione risorse
- Reports e analytics

**Metriche Visualizzate:**
- ODL attivi
- Efficienza media
- Ritardi
- Completamenti giornalieri

**Features Speciali:**
- Alert e notifiche in tempo reale
- Azioni rapide per operazioni frequenti

### 🔧 Dashboard Laminatore
**Funzionalità:**
- Gestione parti e catalogo
- Operazioni di laminazione
- Controllo qualità
- Gestione strumenti
- Registrazione tempi
- ODL assegnati

**Metriche Visualizzate:**
- ODL in lavorazione
- Efficienza turno
- Tempo medio ciclo
- Controlli QC

**Features Speciali:**
- Lista ODL attivi con progress bar
- Controlli per avvio/pausa operazioni

### 🔥 Dashboard Autoclavista
**Funzionalità:**
- Gestione autoclavi
- Cicli di cura
- Nesting e scheduling
- Monitoraggio processi
- Scheduling produzione
- Reports e analytics

**Metriche Visualizzate:**
- Autoclavi attive
- Efficienza media
- Cicli completati
- Tempo medio ciclo

**Features Speciali:**
- Stato autoclavi in tempo reale con temperatura/pressione
- Cicli programmati con timeline
- Controlli per gestione cicli termici

## 🛠️ Implementazione Tecnica

### Hook useUserRole
```typescript
const { role, isLoading, setRole, clearRole } = useUserRole()
```

**Funzioni Disponibili:**
- `role`: Ruolo corrente dell'utente
- `isLoading`: Stato di caricamento
- `setRole(newRole)`: Imposta un nuovo ruolo
- `clearRole()`: Cancella il ruolo corrente
- `hasRole(targetRole)`: Verifica ruolo specifico
- `isAdmin()`: Verifica se è admin

### Caricamento Dinamico
```typescript
const DashboardAdmin = dynamic(() => import('@/components/dashboard/DashboardAdmin'), {
  loading: () => <DashboardLoading />,
  ssr: false
})
```

**Vantaggi:**
- **Code Splitting**: Ogni dashboard è un chunk separato
- **Lazy Loading**: Caricamento solo quando necessario
- **SSR Disabled**: Evita problemi di idratazione con localStorage

## 🧪 Testing

### Test Locali
1. **Avvia il server**: `npm run dev`
2. **Seleziona un ruolo**: Vai a `/select-role`
3. **Verifica dashboard**: Naviga a `/dashboard`
4. **Testa cambio ruolo**: Usa `useUserRole().setRole()`

### Scenari di Test
- ✅ Accesso con ruolo valido
- ✅ Accesso senza ruolo (reindirizzamento)
- ✅ Cambio ruolo dinamico
- ✅ Ruolo invalido (gestione errore)
- ✅ Performance caricamento

## 🔄 Cambio Ruolo Dinamico

Per cambiare ruolo programmaticamente:
```typescript
const { setRole } = useUserRole()

// Cambio ruolo
setRole('ADMIN')
// La dashboard si aggiorna automaticamente
```

## 📱 Responsive Design

Tutte le dashboard sono ottimizzate per:
- **Desktop**: Layout completo con sidebar
- **Tablet**: Layout adattivo con grid responsive
- **Mobile**: Layout verticale con componenti impilati

## 🎯 Best Practices

### Performance
- Usa `dynamic()` per componenti pesanti
- Implementa loading states appropriati
- Evita re-render inutili con `useCallback`

### UX
- Feedback visivo durante i caricamenti
- Transizioni fluide tra dashboard
- Messaggi di errore chiari

### Manutenibilità
- Componenti modulari e riutilizzabili
- Tipizzazione TypeScript completa
- Documentazione inline del codice

## 🚀 Estensioni Future

### Nuovi Ruoli
Per aggiungere un nuovo ruolo:
1. Aggiorna il tipo `UserRole` in `useUserRole.ts`
2. Crea il componente dashboard in `components/dashboard/`
3. Aggiungi il case nello switch di `page.tsx`
4. Aggiorna la pagina `select-role`

### Personalizzazione
- Dashboard personalizzabili per utente
- Widget drag & drop
- Temi personalizzati per ruolo

## 📊 Metriche e Monitoraggio

Il sistema traccia automaticamente:
- Tempo di caricamento per ruolo
- Utilizzo delle funzionalità per dashboard
- Errori di caricamento componenti
- Performance del lazy loading 
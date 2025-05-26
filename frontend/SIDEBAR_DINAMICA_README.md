# 🎭 Sidebar Dinamica Basata sui Ruoli - CarbonPilot

## 📋 Panoramica

La sidebar dell'applicazione CarbonPilot è ora completamente dinamica e si adatta automaticamente al ruolo dell'utente selezionato. Ogni ruolo vede solo le funzionalità pertinenti al proprio lavoro, migliorando l'esperienza utente e riducendo la confusione.

## 🎯 Configurazione Ruoli

### 👑 ADMIN
**Accesso completo a tutte le funzionalità:**
- Dashboard
- **Gestione ODL**: ODL, Monitoraggio ODL
- **Produzione**: Produzione, Tools/Stampi
- **Autoclave**: Nesting, Autoclavi, Reports
- **Pianificazione**: Schedule
- **Amministrazione**: Catalogo, Parti, Cicli Cura, Statistiche, Tempi & Performance, Impostazioni

### 👨‍💼 RESPONSABILE
**Accesso limitato a gestione e supervisione:**
- Dashboard
- **Gestione ODL**: ODL, Monitoraggio ODL
- **Pianificazione**: Schedule

### 🔧 LAMINATORE
**Accesso focalizzato su produzione:**
- Dashboard
- **Produzione**: Produzione, Tools/Stampi

### 🔥 AUTOCLAVISTA
**Accesso specifico per processo autoclave:**
- Dashboard
- **Autoclave**: Nesting, Autoclavi, Reports

## 🧪 Come Testare

### 1. Test Automatico
```bash
# Esegui il test della logica di filtraggio
cd frontend
node test_role_logic.js
```

### 2. Test Visuale nel Browser
1. Apri `frontend/test_sidebar_roles.html` nel browser
2. Clicca sui pulsanti dei ruoli per vedere la sidebar simulata
3. Verifica che ogni ruolo mostri solo le voci corrette

### 3. Test nell'Applicazione
1. Avvia l'applicazione: `npm run dev`
2. Vai su `http://localhost:3000`
3. Seleziona un ruolo nella landing page
4. Naviga alla dashboard e verifica la sidebar
5. Usa il pulsante "Cambia Ruolo" (solo in sviluppo) per testare altri ruoli

## 🔧 Implementazione Tecnica

### Struttura File
```
frontend/src/app/dashboard/layout.tsx  # Configurazione sidebar principale
frontend/src/hooks/useUserRole.ts      # Hook per gestione ruoli
frontend/src/components/RoleGuard.tsx  # Protezione route
```

### Logica di Filtraggio
```typescript
// Filtra items per ruolo
const filterItemsByRole = (items: SidebarNavItem[], role: UserRole | null) => {
    return items.filter(item => {
        if (!item.roles) return true;  // Visibile a tutti
        if (!role) return false;       // Nessun ruolo = nessun accesso
        return item.roles.includes(role);
    });
};

// Filtra sezioni per ruolo
const filterSectionsByRole = (sections: SidebarSection[], role: UserRole | null) => {
    return sections
        .map(section => ({
            ...section,
            items: filterItemsByRole(section.items, role)
        }))
        .filter(section => {
            if (!section.roles) return section.items.length > 0;
            if (!role) return false;
            return section.roles.includes(role) && section.items.length > 0;
        });
};
```

## 🛡️ Sicurezza e Fallback

### Controlli di Sicurezza
- **RoleGuard**: Reindirizza alla selezione ruolo se mancante
- **localStorage**: Persistenza del ruolo selezionato
- **Validazione client-side**: Controllo ruoli validi

### Fallback Graceful
- Se nessun ruolo: reindirizzamento automatico a `/select-role`
- Se ruolo invalido: pulizia localStorage e reindirizzamento
- Se nessuna voce visibile: messaggio informativo

## 🎨 Personalizzazione

### Aggiungere Nuove Voci
1. Modifica `sidebarSections` in `layout.tsx`
2. Specifica i `roles` autorizzati per ogni voce
3. Aggiorna i test in `test_role_logic.js`

### Modificare Ruoli
1. Aggiorna `UserRole` type in `useUserRole.ts`
2. Modifica la configurazione in `sidebarSections`
3. Aggiorna i test e la documentazione

## 📊 Statistiche Accesso

| Ruolo | Voci Visibili | Percentuale |
|-------|---------------|-------------|
| ADMIN | 15/15 | 100% |
| RESPONSABILE | 4/15 | 27% |
| LAMINATORE | 3/15 | 20% |
| AUTOCLAVISTA | 4/15 | 27% |

## 🚀 Deployment

### Verifica Pre-Deploy
```bash
# Controlla TypeScript
npx tsc --noEmit

# Esegui test ruoli
node test_role_logic.js

# Build produzione
npm run build
```

### Variabili Ambiente
- `NODE_ENV=production`: Nasconde pulsante "Cambia Ruolo"
- `NODE_ENV=development`: Mostra controlli di debug

## 🐛 Troubleshooting

### Problemi Comuni

**Sidebar vuota:**
- Verifica che il ruolo sia impostato in localStorage
- Controlla la console per errori JavaScript

**Ruolo non persistente:**
- Verifica che localStorage sia abilitato
- Controlla che il dominio sia corretto

**Voci mancanti:**
- Verifica la configurazione `roles` in `sidebarSections`
- Controlla che il ruolo sia scritto correttamente (maiuscolo)

### Debug
```javascript
// Console browser
localStorage.getItem('userRole')  // Verifica ruolo corrente
localStorage.setItem('userRole', 'ADMIN')  // Imposta ruolo manualmente
localStorage.removeItem('userRole')  // Rimuovi ruolo
```

## 📝 Changelog

### v2.0.4 - Sidebar Dinamica
- ✅ Implementazione completa filtri per ruolo
- ✅ Riorganizzazione sezioni sidebar
- ✅ Test automatici e manuali
- ✅ Documentazione completa
- ✅ Fallback sicuri per ruoli mancanti

---

**Autore**: Sistema CarbonPilot  
**Data**: 25 Gennaio 2025  
**Versione**: 2.0.4 
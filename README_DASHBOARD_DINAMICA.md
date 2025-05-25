# 🚀 Dashboard Dinamica CarbonPilot - Guida Test

## 📋 Panoramica

Questa guida ti aiuterà a testare il nuovo sistema di dashboard dinamica che carica automaticamente l'interfaccia appropriata in base al ruolo dell'utente.

## 🎯 Funzionalità Implementate

### ✅ Dashboard Specializzate per Ruolo
- **👑 ADMIN**: Gestione completa sistema, utenti, configurazioni, monitoraggio
- **👥 RESPONSABILE**: Supervisione produzione, ODL, team, alert in tempo reale  
- **🔧 LAMINATORE**: Operazioni laminazione, parti, controllo qualità, ODL attivi
- **🔥 AUTOCLAVISTA**: Gestione autoclavi, cicli cura, nesting, scheduling

### ✅ Caricamento Dinamico
- **Lazy Loading**: Componenti caricati solo quando necessari
- **Code Splitting**: Bundle ottimizzati per performance
- **Loading States**: Feedback visivo durante il caricamento

### ✅ Gestione Automatica
- **Reindirizzamento**: Automatico a `/select-role` se ruolo mancante
- **Validazione**: Controllo ruoli validi con gestione errori
- **Persistenza**: Ruolo salvato in localStorage

## 🧪 Come Testare

### 1. Avvia il Server di Sviluppo
```bash
cd frontend
npm run dev
```

Il server sarà disponibile su: http://localhost:3000

### 2. Test Scenario Base

#### Scenario A: Primo Accesso (Nessun Ruolo)
1. Apri http://localhost:3000/dashboard
2. **Risultato Atteso**: Reindirizzamento automatico a `/select-role`
3. **Verifica**: URL cambia in `/select-role` e vedi la pagina di selezione ruolo

#### Scenario B: Selezione Ruolo Admin
1. Dalla pagina `/select-role`, clicca su "Amministratore"
2. **Risultato Atteso**: Reindirizzamento a `/dashboard` con dashboard admin
3. **Verifica**: 
   - Titolo: "Dashboard Amministratore" con icona scudo rossa
   - Badge "ADMIN" in alto a destra
   - 6 sezioni: Gestione Utenti, Configurazioni Sistema, Monitoraggio, Database, Reports, Audit
   - 4 metriche: Utenti Attivi, Sistema Uptime, ODL Totali, Performance

#### Scenario C: Cambio Ruolo Dinamico
1. Apri la console del browser (F12)
2. Esegui: `localStorage.setItem('userRole', 'RESPONSABILE')`
3. Ricarica la pagina (F5)
4. **Risultato Atteso**: Dashboard cambia automaticamente a Responsabile
5. **Verifica**:
   - Titolo: "Dashboard Responsabile" con icona utenti blu
   - Badge "RESPONSABILE" in alto a destra
   - Layout con sidebar alert e azioni rapide

### 3. Test Tutti i Ruoli

#### Test Dashboard Responsabile
```javascript
// Console browser
localStorage.setItem('userRole', 'RESPONSABILE')
location.reload()
```
**Verifica**:
- 6 sezioni principali con icone colorate
- Sidebar con "Alert & Notifiche" e "Azioni Rapide"
- Metriche: ODL Attivi, Efficienza Media, Ritardi, Completati Oggi

#### Test Dashboard Laminatore  
```javascript
// Console browser
localStorage.setItem('userRole', 'LAMINATORE')
location.reload()
```
**Verifica**:
- Icona chiave inglese verde nel titolo
- Sidebar "ODL Attivi" con progress bar
- Metriche operative specifiche per laminazione

#### Test Dashboard Autoclavista
```javascript
// Console browser
localStorage.setItem('userRole', 'AUTOCLAVISTA')
location.reload()
```
**Verifica**:
- Icona fiamma arancione nel titolo
- Sidebar "Stato Autoclavi" con temperatura/pressione
- Sezione "Cicli Programmati" con timeline

### 4. Test Casi Edge

#### Test Ruolo Invalido
```javascript
// Console browser
localStorage.setItem('userRole', 'RUOLO_INESISTENTE')
location.reload()
```
**Risultato Atteso**: Reindirizzamento automatico a `/select-role`

#### Test Ruolo Vuoto
```javascript
// Console browser
localStorage.removeItem('userRole')
location.reload()
```
**Risultato Atteso**: Reindirizzamento automatico a `/select-role`

## 🎨 Elementi UI da Verificare

### Header Dashboard
- **Titolo**: Specifico per ruolo con icona colorata
- **Badge Ruolo**: In alto a destra con colore distintivo
- **Descrizione**: Testo esplicativo delle funzionalità

### Metriche (Cards in alto)
- **4 Cards**: Con icone, valori numerici e trend
- **Colori**: Verde per successo, giallo per warning, rosso per errori
- **Responsive**: Adattamento su mobile (stack verticale)

### Sezioni Principali
- **Grid Layout**: 2-3 colonne su desktop, 1 su mobile
- **Cards Hover**: Effetto shadow al passaggio mouse
- **Icone Colorate**: Ogni sezione con icona distintiva
- **Pulsanti**: "Accedi" per navigazione (placeholder)

### Sidebar (Responsabile, Laminatore, Autoclavista)
- **Layout 3 Colonne**: 2/3 sezioni principali + 1/3 sidebar
- **Cards Sidebar**: Alert, ODL attivi, azioni rapide
- **Responsive**: Sidebar sotto su mobile

## 🔧 Debug e Troubleshooting

### Console Browser
Apri la console (F12) per vedere:
- Log di caricamento ruolo
- Eventuali errori di importazione componenti
- Messaggi di reindirizzamento

### Comandi Utili Console
```javascript
// Verifica ruolo corrente
localStorage.getItem('userRole')

// Cambia ruolo
localStorage.setItem('userRole', 'ADMIN')

// Cancella ruolo
localStorage.removeItem('userRole')

// Ricarica pagina
location.reload()
```

### Verifica Network Tab
- **Chunks Dinamici**: Verifica caricamento lazy dei componenti
- **Bundle Size**: Ogni dashboard dovrebbe essere un chunk separato
- **Performance**: Tempi di caricamento ottimizzati

## 📱 Test Responsive

### Desktop (>1024px)
- Layout completo con sidebar
- Grid 3-4 colonne per metriche
- Tutte le funzionalità visibili

### Tablet (768-1024px)  
- Layout adattivo 2 colonne
- Sidebar sotto le sezioni principali
- Metriche in 2 colonne

### Mobile (<768px)
- Layout verticale singola colonna
- Cards impilate
- Sidebar integrata nel flusso

## ✅ Checklist Test Completo

- [ ] Reindirizzamento automatico senza ruolo
- [ ] Selezione ruolo da `/select-role`
- [ ] Caricamento Dashboard Admin
- [ ] Caricamento Dashboard Responsabile  
- [ ] Caricamento Dashboard Laminatore
- [ ] Caricamento Dashboard Autoclavista
- [ ] Cambio ruolo dinamico senza reload
- [ ] Gestione ruolo invalido
- [ ] Loading states durante caricamento
- [ ] Responsive design su tutti i dispositivi
- [ ] Performance e lazy loading
- [ ] Persistenza ruolo in localStorage

## 🐛 Problemi Comuni

### Dashboard Non Carica
- **Causa**: Errore import componente
- **Soluzione**: Verifica console per errori, controlla path import

### Reindirizzamento Loop
- **Causa**: Ruolo non riconosciuto nel switch
- **Soluzione**: Verifica valore localStorage, usa ruoli validi

### Layout Rotto
- **Causa**: CSS non caricato o conflitti
- **Soluzione**: Verifica Tailwind, controlla classi CSS

### Performance Lenta
- **Causa**: Bundle non ottimizzato
- **Soluzione**: Verifica dynamic imports, controlla Network tab

## 📞 Supporto

Se riscontri problemi durante i test:
1. Controlla la console browser per errori
2. Verifica che il server di sviluppo sia attivo
3. Prova a cancellare localStorage e ricominciare
4. Controlla che tutti i file siano stati creati correttamente

---

**🎉 Buon Testing!** La dashboard dinamica rappresenta un significativo miglioramento dell'UX di CarbonPilot, fornendo interfacce personalizzate e ottimizzate per ogni ruolo utente. 
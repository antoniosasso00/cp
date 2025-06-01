# 🎨 Guida di Stile UI/UX - CarbonPilot v1.4.1

> **TAG:** `v1.4.1-design-tokens`  
> **Data:** 2024  
> **Descrizione:** Sistema di design tokens centralizzato per garantire coerenza visiva in tutto il progetto CarbonPilot.

---

## 📋 Indice

1. [🎨 Palette Colori](#-palette-colori)
2. [🔤 Tipografia](#-tipografia)
3. [📐 Spaziature](#-spaziature)
4. [🔵 Border Radius](#-border-radius)
5. [🌙 Ombre e Elevazioni](#-ombre-e-elevazioni)
6. [🎯 Componenti](#-componenti)
7. [💡 Esempi Pratici](#-esempi-pratici)
8. [🔧 Come Utilizzare i Tokens](#-come-utilizzare-i-tokens)

---

## 🎨 Palette Colori

### Colori Primari
Colori principali del brand CarbonPilot utilizzati per azioni primarie, link e elementi di focus.

| Nome | Hex | Variabile CSS | Classe Tailwind |
|------|-----|---------------|-----------------|
| **Primary** | `#2660ff` | `--color-primary` | `bg-primary` |
| Primary Light | `#4775ff` | `--color-primary-light` | - |
| Primary Dark | `#1a4bcc` | `--color-primary-dark` | - |

```html
<!-- Esempio Button Primary -->
<button class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary-dark">
  Azione Primaria
</button>

<!-- Con design tokens CSS -->
<button class="cp-button-primary">
  Azione Primaria con Design Token
</button>
```

### Colori di Stato
Colori utilizzati per comunicare stati e feedback all'utente.

| Stato | Hex | Variabile CSS | Classe Tailwind |
|-------|-----|---------------|-----------------|
| **Danger/Error** | `#ef4444` | `--color-danger` | `bg-danger` |
| Success | `#22c55e` | `--color-success` | `bg-green-500` |
| Warning | `#f59e0b` | `--color-warning` | `bg-yellow-500` |
| Info | `#3b82f6` | `--color-info` | `bg-blue-500` |

```html
<!-- Card di Errore -->
<div class="cp-card border-l-4 border-danger">
  <div class="flex items-center">
    <span class="cp-danger">⚠️</span>
    <span class="ml-2">Operazione fallita</span>
  </div>
</div>

<!-- Alert di Successo -->
<div class="bg-green-50 border border-green-200 p-4 rounded-lg">
  <span class="text-green-700">✅ Operazione completata con successo</span>
</div>
```

### Colori Strutturali
Colori utilizzati per layout, background e strutture.

| Nome | Hex | Variabile CSS | Classe Tailwind |
|------|-----|---------------|-----------------|
| **Surface** | `#ffffff` | `--color-surface` | `bg-surface` |
| **Gray Background** | `#f5f6fa` | `--color-gray-bg` | `bg-grayBg` |
| Border | `#e2e8f0` | `--color-border` | `border-gray-200` |

```html
<!-- Layout con colori strutturali -->
<div class="bg-grayBg min-h-screen p-6">
  <div class="cp-surface max-w-4xl mx-auto rounded-xl shadow-lg p-8">
    <h1>Contenuto principale</h1>
  </div>
</div>
```

### Scala di Grigi
Sistema completo di grigi per testi, bordi e elementi secondari.

| Livello | Hex | Uso Principale |
|---------|-----|----------------|
| Gray 50 | `#f8fafc` | Background molto leggero |
| Gray 100 | `#f1f5f9` | Background leggero |
| Gray 200 | `#e2e8f0` | Bordi |
| Gray 300 | `#cbd5e1` | Bordi attivi |
| Gray 400 | `#94a3b8` | Placeholder |
| Gray 500 | `#64748b` | Testo secondario |
| Gray 600 | `#475569` | Testo principale chiaro |
| Gray 700 | `#334155` | Testo principale |
| Gray 800 | `#1e293b` | Testo forte |
| Gray 900 | `#0f172a` | Testo massimo contrasto |

---

## 🔤 Tipografia

### Scale Font
Sistema di dimensioni dei font basato su progressione geometrica.

| Size | Dimensione | Variabile CSS | Classe Tailwind | Uso |
|------|------------|---------------|-----------------|-----|
| xs | 12px | `--font-size-xs` | `text-xs` | Caption, note |
| sm | 14px | `--font-size-sm` | `text-sm` | Testo piccolo |
| base | 16px | `--font-size-base` | `text-base` | Testo corpo |
| lg | 18px | `--font-size-lg` | `text-lg` | Testo enfatizzato |
| xl | 20px | `--font-size-xl` | `text-xl` | Sottotitoli |
| 2xl | 24px | `--font-size-2xl` | `text-2xl` | Titoli sezione |
| 3xl | 30px | `--font-size-3xl` | `text-3xl` | Titoli pagina |
| 4xl | 36px | `--font-size-4xl` | `text-4xl` | Titoli principali |
| 5xl | 48px | `--font-size-5xl` | `text-5xl` | Titoli hero |

### Pesi Font

| Peso | Valore | Variabile CSS | Classe Tailwind | Uso |
|------|--------|---------------|-----------------|-----|
| Light | 300 | `--font-weight-light` | `font-light` | Testo decorativo |
| Normal | 400 | `--font-weight-normal` | `font-normal` | Testo corpo |
| Medium | 500 | `--font-weight-medium` | `font-medium` | Enfasi leggera |
| Semibold | 600 | `--font-weight-semibold` | `font-semibold` | Sottotitoli |
| Bold | 700 | `--font-weight-bold` | `font-bold` | Titoli |
| Extrabold | 800 | `--font-weight-extrabold` | `font-extrabold` | Titoli forti |

```html
<!-- Esempio Gerarchia Tipografica -->
<article class="space-y-4">
  <h1 class="text-4xl font-bold text-gray-900">Titolo Principale</h1>
  <h2 class="text-2xl font-semibold text-gray-800">Sottotitolo</h2>
  <p class="text-base text-gray-600 leading-relaxed">
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. 
    Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
  </p>
  <small class="text-sm text-gray-400">Nota informativa</small>
</article>
```

---

## 📐 Spaziature

### Sistema di Spaziature
Scala basata su incrementi di 4px per coerenza visiva.

| Nome | Valore | Variabile CSS | Classe Tailwind | Uso |
|------|--------|---------------|-----------------|-----|
| xs | 4px | `--spacing-xs` | `p-1` | Spaziature minime |
| sm | 8px | `--spacing-sm` | `p-2` | Padding piccolo |
| md | 12px | `--spacing-md` | `p-3` | Padding medio |
| lg | 16px | `--spacing-lg` | `p-4` | Padding standard |
| xl | 24px | `--spacing-xl` | `p-6` | Padding grande |
| 2xl | 32px | `--spacing-2xl` | `p-8` | Padding molto grande |
| 3xl | 48px | `--spacing-3xl` | `p-12` | Spaziature sezioni |
| **Custom** | **288px** | `--spacing-custom` | `p-72` | **Design Token specifico** |

```html
<!-- Esempio Layout con Spaziature -->
<div class="p-6 space-y-4">
  <div class="cp-card p-xl">
    <h3 class="mb-md">Titolo Card</h3>
    <p class="mb-lg">Contenuto della card con spaziature consistent.</p>
    <button class="px-lg py-md">Azione</button>
  </div>
</div>
```

---

## 🔵 Border Radius

### Sistema Border Radius
Definisce la morbidezza degli angoli per diversi componenti.

| Nome | Valore | Variabile CSS | Classe Tailwind | Uso |
|------|--------|---------------|-----------------|-----|
| none | 0 | `--radius-none` | `rounded-none` | Elementi quadrati |
| sm | 2px | `--radius-sm` | `rounded-sm` | Input, piccoli elementi |
| md | 6px | `--radius-md` | `rounded-md` | Card piccole |
| lg | 8px | `--radius-lg` | `rounded-lg` | Card standard |
| **xl** | **16px** | `--radius-xl` | `rounded-xl` | **Design Token - Card grandi** |
| **2xl** | **24px** | `--radius-2xl` | `rounded-2xl` | **Design Token - Container** |
| 3xl | 32px | `--radius-3xl` | `rounded-3xl` | Card hero |
| full | 9999px | `--radius-full` | `rounded-full` | Elementi circolari |

```html
<!-- Esempi Border Radius -->
<div class="grid grid-cols-2 gap-4">
  <!-- Card Standard -->
  <div class="cp-card rounded-xl">
    <h4>Card con Design Token xl</h4>
  </div>
  
  <!-- Container Grande -->
  <div class="bg-surface p-8 rounded-2xl shadow-lg">
    <h4>Container con Design Token 2xl</h4>
  </div>
</div>
```

---

## 🌙 Ombre e Elevazioni

### Sistema Ombre
Crea profondità e gerarchia visiva utilizzando ombre soft e moderne.

| Nome | Valore | Variabile CSS | Uso |
|------|--------|---------------|-----|
| sm | `0 1px 2px 0 rgba(0,0,0,0.05)` | `--shadow-sm` | Bordi leggeri |
| md | `0 4px 6px -1px rgba(0,0,0,0.1)` | `--shadow-md` | Card standard |
| lg | `0 10px 15px -3px rgba(0,0,0,0.1)` | `--shadow-lg` | Card elevate |
| xl | `0 20px 25px -5px rgba(0,0,0,0.1)` | `--shadow-xl` | Modal, dropdown |
| 2xl | `0 25px 50px -12px rgba(0,0,0,0.25)` | `--shadow-2xl` | Overlay importanti |

```html
<!-- Esempi Elevazioni -->
<div class="space-y-6">
  <div class="p-6 bg-surface rounded-lg shadow-sm">Elevazione minima</div>
  <div class="p-6 bg-surface rounded-lg shadow-md">Elevazione media</div>
  <div class="p-6 bg-surface rounded-lg shadow-lg">Elevazione alta</div>
  <div class="p-6 bg-surface rounded-lg shadow-2xl">Elevazione massima</div>
</div>
```

---

## 🎯 Componenti

### Card Standard
Componente base per contenuti strutturati.

```html
<!-- Card con Design Tokens -->
<div class="cp-card">
  <h3 class="text-xl font-semibold mb-3">Titolo Card</h3>
  <p class="text-gray-600 mb-4">Descrizione del contenuto della card.</p>
  <button class="cp-button-primary">Azione Primaria</button>
</div>

<!-- Card Tailwind -->
<div class="bg-surface border border-gray-200 rounded-xl shadow-md p-6">
  <h3 class="text-xl font-semibold mb-3">Titolo Card</h3>
  <p class="text-gray-600 mb-4">Descrizione del contenuto della card.</p>
  <button class="bg-primary text-white px-6 py-3 rounded-lg hover:bg-primary-dark">
    Azione Primaria
  </button>
</div>
```

### Buttons
Sistema di pulsanti con stati e varianti.

```html
<!-- Button Primary -->
<button class="cp-button-primary">Primary Action</button>
<button class="bg-primary text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-dark transition-colors">
  Primary Tailwind
</button>

<!-- Button Danger -->
<button class="cp-button-danger">Delete Action</button>
<button class="bg-danger text-white px-6 py-3 rounded-lg font-medium hover:bg-red-600 transition-colors">
  Danger Tailwind
</button>

<!-- Button Secondary -->
<button class="bg-gray-100 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors">
  Secondary Action
</button>
```

### Form Elements
Stili coerenti per input e form controls.

```html
<!-- Input con Design Tokens -->
<div class="space-y-2">
  <label class="text-sm font-medium text-gray-700">Label</label>
  <input 
    type="text" 
    class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:border-primary focus:ring-2 focus:ring-primary/20"
    placeholder="Inserisci testo..."
  />
</div>

<!-- Select -->
<select class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:border-primary">
  <option>Seleziona opzione</option>
  <option>Opzione 1</option>
  <option>Opzione 2</option>
</select>
```

---

## 💡 Esempi Pratici

### Dashboard Card
```html
<div class="cp-card">
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold">ODL Attivi</h3>
    <span class="bg-primary/10 text-primary px-3 py-1 rounded-full text-sm font-medium">
      42 attivi
    </span>
  </div>
  <p class="text-gray-600 mb-6">
    Monitora lo stato degli ordini di lavoro in tempo reale.
  </p>
  <div class="flex gap-3">
    <button class="cp-button-primary">Visualizza Tutti</button>
    <button class="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200">
      Filtri
    </button>
  </div>
</div>
```

### Alert System
```html
<!-- Success Alert -->
<div class="bg-green-50 border-l-4 border-green-400 p-4 rounded-r-lg">
  <div class="flex">
    <span class="text-green-600 text-xl">✅</span>
    <div class="ml-3">
      <h4 class="text-green-800 font-medium">Operazione completata</h4>
      <p class="text-green-600 text-sm">ODL #1234 aggiornato con successo.</p>
    </div>
  </div>
</div>

<!-- Error Alert -->
<div class="bg-red-50 border-l-4 border-danger p-4 rounded-r-lg">
  <div class="flex">
    <span class="text-danger text-xl">⚠️</span>
    <div class="ml-3">
      <h4 class="text-red-800 font-medium">Errore nell'operazione</h4>
      <p class="text-red-600 text-sm">Impossibile salvare i dati. Riprova.</p>
    </div>
  </div>
</div>
```

### Navigation Menu
```html
<nav class="bg-surface border-r border-gray-200 p-4">
  <ul class="space-y-2">
    <li>
      <a href="#" class="flex items-center p-3 text-gray-700 rounded-lg hover:bg-gray-100 hover:text-primary">
        <span class="mr-3">📊</span>
        Dashboard
      </a>
    </li>
    <li>
      <a href="#" class="flex items-center p-3 bg-primary/10 text-primary rounded-lg">
        <span class="mr-3">🔧</span>
        ODL Management
      </a>
    </li>
    <li>
      <a href="#" class="flex items-center p-3 text-gray-700 rounded-lg hover:bg-gray-100 hover:text-primary">
        <span class="mr-3">📋</span>
        Reports
      </a>
    </li>
  </ul>
</nav>
```

---

## 🔧 Come Utilizzare i Tokens

### Priorità di Utilizzo

1. **Prima priorità:** Classi con Design Tokens specifici
   ```html
   <button class="cp-button-primary">Azione</button>
   <div class="cp-card">Contenuto</div>
   ```

2. **Seconda priorità:** Classi Tailwind con tokens CarbonPilot
   ```html
   <button class="bg-primary text-white rounded-xl p-6">Azione</button>
   ```

3. **Terza priorità:** Variabili CSS custom
   ```css
   .custom-component {
     background-color: var(--color-primary);
     border-radius: var(--radius-xl);
     padding: var(--spacing-xl);
   }
   ```

### Best Practices

✅ **DO:**
- Utilizzare sempre i design tokens quando disponibili
- Mantenere coerenza nelle spaziature (multipli di 4px)
- Utilizzare la scala colori definita
- Applicare le ombre per creare gerarchia visiva

❌ **DON'T:**
- Non usare valori hardcoded per colori o spaziature
- Non mescolare font weights casuali
- Non utilizzare border radius casuali
- Non creare colori custom senza consultare il design system

### Responsive Design
```html
<!-- Esempio responsive con design tokens -->
<div class="cp-card">
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div class="p-4 bg-grayBg rounded-xl">Item 1</div>
    <div class="p-4 bg-grayBg rounded-xl">Item 2</div>
    <div class="p-4 bg-grayBg rounded-xl">Item 3</div>
  </div>
</div>
```

---

## 📝 Note per Sviluppatori

- **File Design Tokens:** `frontend/styles/design-tokens.css`
- **Configurazione Tailwind:** `frontend/tailwind.config.ts`
- **Import:** Automatico tramite `globals.css`

### Aggiornamenti Futuri
Per aggiungere nuovi design tokens:

1. Aggiorna `design-tokens.css` con le nuove variabili
2. Aggiorna `tailwind.config.ts` se necessario
3. Aggiorna questa guida di stile
4. Testa tutti i componenti esistenti
5. Aggiorna il `changelog.md`

---

**Versione:** v1.4.1-design-tokens  
**Ultimo aggiornamento:** 2024  
**Prossima revisione:** Da pianificare in base ai feedback 
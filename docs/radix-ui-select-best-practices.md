# Radix UI Select - Best Practices e Risoluzione Errori

## Problema Comune: "A <Select.Item /> must have a value prop that is not an empty string"

### Descrizione del Problema
Radix UI Select non accetta valori vuoti (`""`) per le `SelectItem`. Questo errore si verifica quando si tenta di creare un'opzione "Tutti" o "Nessuna selezione" con valore vuoto.

### ❌ Codice Problematico
```tsx
<Select value={filter} onValueChange={setFilter}>
  <SelectTrigger>
    <SelectValue placeholder="Seleziona..." />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="">Tutti</SelectItem> {/* ERRORE! */}
    <SelectItem value="option1">Opzione 1</SelectItem>
    <SelectItem value="option2">Opzione 2</SelectItem>
  </SelectContent>
</Select>
```

### ✅ Soluzione Corretta
```tsx
<Select 
  value={filter || 'all'} 
  onValueChange={(value) => setFilter(value === 'all' ? '' : value)}
>
  <SelectTrigger>
    <SelectValue placeholder="Seleziona..." />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="all">Tutti</SelectItem> {/* OK! */}
    <SelectItem value="option1">Opzione 1</SelectItem>
    <SelectItem value="option2">Opzione 2</SelectItem>
  </SelectContent>
</Select>
```

## Componente SafeSelect

Per semplificare l'uso e prevenire errori futuri, è disponibile il componente `SafeSelect`:

```tsx
import { SafeSelect } from "@/components/ui/safe-select"

<SafeSelect 
  value={filter} 
  onValueChange={setFilter}
  placeholder="Seleziona..."
  allOptionLabel="Tutti gli elementi"
>
  <SelectItem value="option1">Opzione 1</SelectItem>
  <SelectItem value="option2">Opzione 2</SelectItem>
</SafeSelect>
```

### Vantaggi del SafeSelect
- Gestione automatica dei valori vuoti
- Prevenzione dell'errore Radix UI
- API semplificata per lo sviluppatore
- Configurabile (etichetta e valore dell'opzione "Tutti")

## Pattern di Implementazione

### 1. Filtri con Opzione "Tutti"
```tsx
const [statusFilter, setStatusFilter] = useState<string>('')

// Pattern corretto
<Select 
  value={statusFilter || 'all'} 
  onValueChange={(value) => setStatusFilter(value === 'all' ? '' : value)}
>
  <SelectContent>
    <SelectItem value="all">Tutti gli stati</SelectItem>
    <SelectItem value="active">Attivo</SelectItem>
    <SelectItem value="inactive">Inattivo</SelectItem>
  </SelectContent>
</Select>
```

### 2. Select con Valore Opzionale
```tsx
const [selectedValue, setSelectedValue] = useState<string | undefined>(undefined)

// Pattern corretto
<Select 
  value={selectedValue || 'none'} 
  onValueChange={(value) => setSelectedValue(value === 'none' ? undefined : value)}
>
  <SelectContent>
    <SelectItem value="none">Nessuna selezione</SelectItem>
    <SelectItem value="option1">Opzione 1</SelectItem>
    <SelectItem value="option2">Opzione 2</SelectItem>
  </SelectContent>
</Select>
```

### 3. Select con Placeholder Persistente
```tsx
const [value, setValue] = useState<string>('')

// Pattern corretto per mantenere il placeholder
<Select 
  value={value || 'placeholder'} 
  onValueChange={(value) => setValue(value === 'placeholder' ? '' : value)}
>
  <SelectTrigger>
    <SelectValue placeholder="Scegli un'opzione" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="placeholder" disabled>Scegli un'opzione</SelectItem>
    <SelectItem value="option1">Opzione 1</SelectItem>
    <SelectItem value="option2">Opzione 2</SelectItem>
  </SelectContent>
</Select>
```

## Checklist per Sviluppatori

Prima di implementare un Select, verifica:

- [ ] Nessuna `SelectItem` ha `value=""` (stringa vuota)
- [ ] Se serve un'opzione "Tutti/Nessuno", usa un valore specifico (es. "all", "none")
- [ ] La logica `onValueChange` converte correttamente i valori speciali
- [ ] Il `value` del Select non è mai `undefined` o `""`
- [ ] Considera l'uso di `SafeSelect` per casi semplici

## Riferimenti

- [Radix UI GitHub Issue #1569](https://github.com/radix-ui/primitives/issues/1569)
- [Code with Mosh Forum Discussion](https://forum.codewithmosh.com/t/a-select-item-must-have-a-value-prop-that-is-not-an-empty-string-this-is-because-the-select-value-can-be-set-to-an-empty-string-to-clear-the-selection-and-show-the-placeholder/23078/7)
- [Radix UI Select Documentation](https://www.radix-ui.com/docs/primitives/components/select)

## File Corretti nel Progetto

I seguenti file sono stati corretti per seguire queste best practices:

- `frontend/src/components/dashboard/ODLHistoryTable.tsx`
- `frontend/src/app/dashboard/admin/logs/page.tsx`
- `frontend/src/app/dashboard/responsabile/logs/page.tsx`

Questi file possono essere usati come riferimento per implementazioni future. 
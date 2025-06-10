# StatusCard Component

Componente riusabile per pannelli numerici interattivi con badge trend e funzionalità click per dashboard.

## Caratteristiche

- **Interattività**: Click per applicare filtri o navigazione
- **Badge Trend**: Indicatori Δ giornalieri con icone (↗️ ↘️ ➖)
- **Colori Tematici**: 6 varianti di colore predefinite
- **Accessibilità**: Hover effects e stati visivi
- **TypeScript**: Completamente tipizzato

## Utilizzo Base

```tsx
import { StatusCard } from '@/shared/components/ui/StatusCard';
import { Users } from 'lucide-react';

<StatusCard
  title="Utenti Attivi"
  value={142}
  icon={Users}
  color="blue"
  trend={{ value: 5, type: 'increase' }}
  onClick={() => handleFilter('users')}
/>
```

## Props

### StatusCardProps

| Prop | Tipo | Default | Descrizione |
|------|------|---------|-------------|
| `title` | `string` | - | Titolo della card |
| `value` | `number` | - | Valore numerico principale |
| `icon` | `LucideIcon` | - | Icona da mostrare |
| `color` | `'blue' \| 'green' \| 'red' \| 'yellow' \| 'purple' \| 'gray'` | `'blue'` | Tema colore |
| `trend` | `{ value: number; type: 'increase' \| 'decrease' \| 'stable' }` | - | Badge trend giornaliero |
| `onClick` | `() => void` | - | Callback click |
| `className` | `string` | - | CSS class aggiuntiva |
| `clickable` | `boolean` | `!!onClick` | Abilita hover effects |
| `description` | `string` | - | Testo descrittivo |

## Componente Helper: BatchStatusCard

Helper specializzato per stati batch con configurazioni predefinite:

```tsx
import { BatchStatusCard } from '@/shared/components/ui/StatusCard';

<BatchStatusCard
  status="sospeso"  // 'total' | 'sospeso' | 'confermato' | 'loaded' | 'cured' | 'completato'
  title="In Sospeso"
  value={23}
  trend={{ value: -2, type: 'decrease' }}
  onClick={() => applyFilter('sospeso')}
/>
```

## Trend Indicators

Il sistema trend confronta automaticamente today vs yesterday:

- **Increase** (↗️): `value > 0` - Verde
- **Decrease** (↘️): `value < 0` - Rosso  
- **Stable** (➖): `value = 0` - Grigio

## Implementazione Dashboard

### 1. Hook per calcolare trend

```tsx
import { useBatchTrends } from '@/shared/hooks/useBatchTrends';

const trends = useBatchTrends(batches);
```

### 2. Filtri via URL query

```tsx
import { useRouter, useSearchParams } from 'next/navigation';

const handleStatusFilter = (status: string) => {
  const params = new URLSearchParams(searchParams.toString());
  params.set('status', status);
  router.push(`?${params.toString()}`);
}
```

### 3. Indicatori stato attivo

```tsx
<StatusCard
  // ... props
  className={statusFilter === 'sospeso' ? 'ring-2 ring-yellow-500' : ''}
/>
```

## Esempi Avanzati

### Con descrizione e trend complesso

```tsx
<StatusCard
  title="Performance Sistema"
  value={87}
  icon={Activity}
  color="green"
  description="% uptime nelle ultime 24h"
  trend={{ value: 12, type: 'increase' }}
  onClick={() => navigate('/performance')}
/>
```

### Non clickable con stato custom

```tsx
<StatusCard
  title="Read-only Metric"
  value={999}
  icon={Info}
  color="gray"
  clickable={false}
  description="Valore di sola lettura"
/>
```

## Stili e Temi

Ogni tema colore include:
- Testo principale
- Sfondo icona  
- Hover effect
- Border focus (ring)

### Mapping Colori

```tsx
blue: 'text-blue-600 bg-blue-50 hover:bg-blue-100'
green: 'text-green-600 bg-green-50 hover:bg-green-100'
red: 'text-red-600 bg-red-50 hover:bg-red-100'
yellow: 'text-yellow-600 bg-yellow-50 hover:bg-yellow-100'
purple: 'text-purple-600 bg-purple-50 hover:bg-purple-100'
gray: 'text-gray-600 bg-gray-50 hover:bg-gray-100'
```

## Best Practices

1. **Consistenza**: Usa sempre lo stesso colore per lo stesso tipo di dato
2. **Feedback Visivo**: Applica ring border per stato attivo
3. **Trend Significativi**: Mostra solo delta > 0 per evitare noise
4. **Click Semantico**: onClick dovrebbe corrispondere al contenuto della card
5. **Performance**: Memorizza trend calculations con useMemo

## Accessibilità

- ✅ Keyboard navigation support
- ✅ Screen reader friendly
- ✅ High contrast colors
- ✅ Hover/focus indicators
- ✅ Semantic HTML structure 
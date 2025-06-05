# Esempi di Utilizzo - Costanti Centralizzate

## 🎯 Come utilizzare le costanti centralizzate

### 1. **Import delle Costanti**

```typescript
// Import delle costanti
import { 
  ODL_STATUS_LABELS,
  ODL_STATUS_COLORS,
  ODL_STATUS_ICONS,
  BATCH_STATUS_COLORS,
  USER_ROLE_LABELS,
  getBadgeColor,
  getLabel,
  isTransitionAllowed
} from '@/shared/lib/constants';

// Import dei tipi
import type { 
  ODLStatus, 
  BatchStatus, 
  UserRole,
  ODLStatusConfig 
} from '@/shared/types';
```

### 2. **Utilizzo nei Componenti Badge**

```typescript
// Prima (hardcoded)
const getBadgeColor = (status: string) => {
  switch (status) {
    case 'Cura':
      return 'bg-orange-100 text-orange-800 border-orange-300';
    case 'Finito':
      return 'bg-green-100 text-green-800 border-green-300';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300';
  }
};

// Dopo (centralizzato)
const badgeColor = getBadgeColor('odl_status', status);
const label = getLabel('odl_status', status);

// Utilizzo nel JSX
<Badge className={badgeColor}>
  {label}
</Badge>
```

### 3. **Configurazione Dinamica Stati ODL**

```typescript
// Prima (configurazione statica)
const ODL_STATUS_CONFIG = {
  'Cura': {
    label: 'Cura',
    color: 'bg-orange-100 text-orange-800 border-orange-300',
    icon: PlayCircle,
    canTransitionTo: ['Finito']
  }
  // ... altri stati
};

// Dopo (configurazione dinamica)
const createODLStatusConfig = (): Record<ODLStatus, ODLStatusConfig> => {
  const config: Record<string, ODLStatusConfig> = {};
  
  ODL_STATUSES.forEach(status => {
    config[status] = {
      status,
      label: ODL_STATUS_LABELS[status],
      description: ODL_STATUS_DESCRIPTIONS[status],
      color: ODL_STATUS_COLORS[status],
      icon: ODL_STATUS_ICONS[status],
      canTransitionTo: [...ODL_STATUS_TRANSITIONS[status]]
    };
  });
  
  return config as Record<ODLStatus, ODLStatusConfig>;
};
```

### 4. **Validazione Transizioni**

```typescript
// Prima (logica sparsa)
const canTransition = (current: string, next: string): boolean => {
  if (current === 'Cura' && next === 'Finito') return true;
  if (current === 'Attesa Cura' && next === 'Cura') return true;
  // ... altre transizioni
  return false;
};

// Dopo (centralizzato)
const canTransition = isTransitionAllowed('odl', currentStatus, newStatus);

// Utilizzo nel componente
const handleStatusChange = (newStatus: ODLStatus) => {
  if (!isTransitionAllowed('odl', currentStatus, newStatus)) {
    setError(`Transizione da ${currentStatus} a ${newStatus} non consentita`);
    return;
  }
  // Procedi con il cambio stato
};
```

### 5. **Rendering Condizionale per Ruoli**

```typescript
// Prima (valori hardcoded)
const isAdmin = userRole === 'ADMIN';
const canManage = userRole === 'ADMIN' || userRole === 'Management';

// Dopo (usando costanti)
import { USER_ROLES } from '@/shared/lib/constants';

const isAdmin = userRole === USER_ROLES[0]; // 'ADMIN'
const canManage = [USER_ROLES[0], USER_ROLES[1]].includes(userRole); // 'ADMIN', 'Management'

// Ancora meglio con utility
const hasAdminRole = (role: UserRole): boolean => role === 'ADMIN';
const hasManagementAccess = (role: UserRole): boolean => 
  ['ADMIN', 'Management'].includes(role);
```

### 6. **Generazione Dinamica di Select/Dropdown**

```typescript
// Prima (opzioni hardcoded)
const statusOptions = [
  { value: 'sospeso', label: 'Sospeso' },
  { value: 'confermato', label: 'Confermato' },
  { value: 'terminato', label: 'Terminato' }
];

// Dopo (generazione dinamica)
const statusOptions = BATCH_STATUSES.map(status => ({
  value: status,
  label: BATCH_STATUS_LABELS[status]
}));

// Utilizzo nel JSX
<Select>
  {statusOptions.map(option => (
    <SelectItem key={option.value} value={option.value}>
      {option.label}
    </SelectItem>
  ))}
</Select>
```

### 7. **Hook Personalizzato per Stati**

```typescript
// Hook personalizzato che utilizza le costanti
import { useState, useCallback } from 'react';
import { ODL_STATUS_TRANSITIONS, isTransitionAllowed } from '@/shared/lib/constants';
import type { ODLStatus } from '@/shared/types';

export const useODLStatusManager = (initialStatus: ODLStatus) => {
  const [currentStatus, setCurrentStatus] = useState<ODLStatus>(initialStatus);
  const [error, setError] = useState<string | null>(null);

  const changeStatus = useCallback((newStatus: ODLStatus) => {
    if (!isTransitionAllowed('odl', currentStatus, newStatus)) {
      setError(`Transizione da ${currentStatus} a ${newStatus} non consentita`);
      return false;
    }
    
    setCurrentStatus(newStatus);
    setError(null);
    return true;
  }, [currentStatus]);

  const getAvailableTransitions = useCallback(() => {
    return ODL_STATUS_TRANSITIONS[currentStatus] || [];
  }, [currentStatus]);

  return {
    currentStatus,
    changeStatus,
    getAvailableTransitions,
    error,
    clearError: () => setError(null)
  };
};
```

### 8. **Componente Badge Riutilizzabile**

```typescript
// Componente Badge che utilizza le costanti centralizzate
import { getBadgeColor, getLabel } from '@/shared/lib/constants';
import { Badge } from '@/components/ui/badge';

interface StatusBadgeProps {
  type: 'odl_status' | 'batch_status' | 'user_role' | 'autoclave_status';
  value: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ 
  type, 
  value, 
  className 
}) => {
  const color = getBadgeColor(type, value);
  const label = getLabel(type, value);

  return (
    <Badge className={`${color} ${className || ''}`}>
      {label}
    </Badge>
  );
};

// Utilizzo
<StatusBadge type="odl_status" value="Cura" />
<StatusBadge type="batch_status" value="confermato" />
<StatusBadge type="user_role" value="ADMIN" />
```

### 9. **Filtri Dinamici**

```typescript
// Generazione dinamica di filtri per tabelle
const createStatusFilters = () => {
  return [
    {
      key: 'all',
      label: 'Tutti',
      value: '',
      count: totalCount
    },
    ...ODL_STATUSES.map(status => ({
      key: status,
      label: ODL_STATUS_LABELS[status],
      value: status,
      count: getCountByStatus(status)
    }))
  ];
};

// Utilizzo nei filtri
const statusFilters = createStatusFilters();
```

### 10. **Validazione Form con Costanti**

```typescript
// Schema di validazione usando le costanti
import { z } from 'zod';
import { ODL_STATUSES, USER_ROLES } from '@/shared/lib/constants';

const odlSchema = z.object({
  status: z.enum(ODL_STATUSES),
  assignedTo: z.enum(USER_ROLES),
  priority: z.number().min(1).max(10)
});

// Utilizzo nel form
const form = useForm({
  resolver: zodResolver(odlSchema),
  defaultValues: {
    status: ODL_STATUSES[0], // 'Preparazione'
    assignedTo: USER_ROLES[2], // 'Clean Room'
    priority: 5
  }
});
```

## 🎯 Vantaggi dell'Approccio Centralizzato

### ✅ **Manutenibilità**
- Modifica di un colore/etichetta in un solo posto
- Aggiunta di nuovi stati senza toccare i componenti
- Refactoring semplificato

### ✅ **Coerenza**
- Stessi colori e etichette in tutta l'app
- Comportamento uniforme per stati simili
- UX consistente

### ✅ **Type Safety**
- Autocompletamento per stati validi
- Errori di compilazione per stati non esistenti
- Validazione automatica delle transizioni

### ✅ **Scalabilità**
- Facile aggiunta di nuovi tipi di stato
- Configurazione modulare
- Riutilizzo di logica comune

---

**Nota**: Questi esempi mostrano come migrare da codice hardcoded a un approccio centralizzato usando le costanti e i tipi definiti in `@/shared/lib/constants` e `@/shared/types`. 
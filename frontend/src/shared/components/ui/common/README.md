# Common UI Components

Componenti condivisi riutilizzabili per l'interfaccia utente di CarbonPilot.

## Componenti Disponibili

### MetricCard
Card per visualizzare metriche con icone, badge e indicatori di trend.

```tsx
import { MetricCard, CompactMetricCard } from '@/shared/components/ui/common'

<MetricCard
  title="ODL Attivi"
  value={127}
  description="In produzione"
  icon={Package}
  badge="Attivo"
  variant="success"
  trend={{ value: 12.5, label: 'vs scorsa settimana' }}
  onClick={() => console.log('clicked')}
/>

<CompactMetricCard
  title="Efficienza"
  value="92%"
  icon={Target}
  variant="success"
/>
```

**Props:**
- `title`: Titolo della metrica
- `value`: Valore principale (string | number)
- `description?`: Descrizione opzionale
- `icon?`: Icona Lucide
- `variant?`: Stile della card ('default' | 'success' | 'warning' | 'destructive')
- `badge?`: Badge di stato
- `trend?`: Indicatore di trend con valore percentuale
- `onClick?`: Handler per click
- `selected?`: Se la card è selezionata
- `loading?`: Stato di caricamento

### StepSidebar
Sidebar per navigazione step-by-step con scroll automatico.

```tsx
import { StepSidebar, useStepNavigation } from '@/shared/components/ui/common'

const steps = [
  {
    id: 'setup',
    title: 'Configurazione',
    description: 'Impostazione parametri',
    status: 'completed',
    clickable: true
  },
  {
    id: 'process',
    title: 'Elaborazione',
    status: 'current',
    badge: 'In corso'
  }
]

<StepSidebar
  steps={steps}
  currentStepId="process"
  onStepClick={(stepId) => console.log(stepId)}
  title="Processo di Nesting"
  orientation="vertical"
  showNumbers={true}
  enableAutoScroll={true}
/>

// Con hook per gestione stato
const {
  steps,
  currentStepId,
  goToStep,
  completeStep,
  goToNextStep
} = useStepNavigation(initialSteps)
```

**Props:**
- `steps`: Array di step items
- `currentStepId?`: Step attualmente attivo
- `onStepClick?`: Callback per click su step
- `allowNavigation?`: Se permettere navigazione libera
- `orientation?`: 'vertical' | 'horizontal'
- `title?`: Titolo della sidebar
- `showNumbers?`: Se mostrare numeri degli step
- `enableAutoScroll?`: Se abilitare scroll automatico

**StepItem Interface:**
- `id`: ID univoco
- `title`: Titolo dello step
- `description?`: Descrizione
- `status`: 'pending' | 'current' | 'completed' | 'error'
- `clickable?`: Se lo step è cliccabile
- `badge?`: Badge opzionale
- `badgeVariant?`: Variante del badge

### AccordionPanel
Pannelli accordion per informazioni collassabili.

```tsx
import { AccordionPanel, SingleAccordion, useAccordionState } from '@/shared/components/ui/common'

const items = [
  {
    id: 'info',
    title: 'Informazioni',
    icon: 'info',
    badge: 'Importante',
    content: <div>Contenuto del pannello</div>
  }
]

<AccordionPanel
  items={items}
  allowMultiple={false}
  variant="default"
  showSeparators={true}
/>

// Pannello singolo
<SingleAccordion
  title="Dettagli"
  icon="info"
  content={<div>Contenuto</div>}
  defaultOpen={true}
/>

// Con hook per controllo stato
const { openItems, toggle, openAll, closeAll } = useAccordionState(['item1'])
```

**Props:**
- `items`: Array di pannelli
- `allowMultiple?`: Apertura multipla pannelli
- `defaultOpenItems?`: Pannelli aperti inizialmente
- `variant?`: 'default' | 'minimal' | 'bordered'
- `showSeparators?`: Separatori tra pannelli

**AccordionPanelItem Interface:**
- `id`: ID univoco
- `title`: Titolo del pannello
- `content`: Contenuto React
- `icon?`: 'info' | 'warning' | 'success' | 'error' | ReactNode
- `badge?`: Badge opzionale
- `disabled?`: Se disabilitato
- `onToggle?`: Callback apertura/chiusura

### ToolRect (Re-export)
Componenti per rendering tool nel canvas (da nesting).

```tsx
import { NestingToolRect, normalizeToolData, TOOL_COLORS } from '@/shared/components/ui/common'

// Disponibili con alias per evitare conflitti:
// - NestingToolRect
// - NestingSimpleToolRect  
// - normalizeToolData
// - TOOL_COLORS
// - getToolColor
// - getToolStatus
```

## Testing

I componenti sono pronti per test Vitest quando il framework sarà configurato:

```bash
# Quando Vitest sarà configurato:
# npm run test src/shared/components/ui/common/
# npm run test:watch src/shared/components/ui/common/
```

## Storybook

I componenti sono pronti per Storybook quando sarà configurato:

```bash
# Quando Storybook sarà configurato:
# npm run storybook
# 
# Componenti disponibili in:
# - UI/Common/MetricCard
# - UI/Common/StepSidebar
# - UI/Common/AccordionPanel
```

## Utilizzo negli Sprint

### Sprint 2 - Nesting Redesign

I componenti sono progettati per supportare le funzionalità dello Sprint 2:

- **MetricCard**: Metriche efficienza e statistiche batch
- **StepSidebar**: Navigazione processo nesting step-by-step
- **AccordionPanel**: Informazioni collassabili sotto il canvas
- **ToolRect**: Rendering ottimizzato tool nel canvas

### Pattern di Utilizzo

```tsx
// Dashboard con metriche
import { MetricCard } from '@/shared/components/ui/common'

const NestingDashboard = () => (
  <div className="grid grid-cols-4 gap-4">
    <MetricCard title="Efficienza" value="85%" variant="success" />
    <MetricCard title="ODL" value={12} icon={Package} />
    <MetricCard title="Batch" value="3/5" badge="Attivi" />
  </div>
)

// Processo con step
import { StepSidebar } from '@/shared/components/ui/common'

const NestingProcess = () => {
  const { steps, currentStepId, goToStep } = useStepNavigation(processSteps)
  
  return (
    <div className="flex">
      <StepSidebar 
        steps={steps}
        currentStepId={currentStepId}
        onStepClick={goToStep}
        className="w-64"
      />
      <main className="flex-1">
        {/* Contenuto step */}
      </main>
    </div>
  )
}

// Informazioni sotto canvas
import { AccordionPanel } from '@/shared/components/ui/common'

const NestingResults = () => (
  <div>
    <canvas>{/* Canvas nesting */}</canvas>
    <AccordionPanel
      items={[
        { id: 'efficiency', title: 'Analisi Efficienza', content: <EfficiencyAnalysis /> },
        { id: 'tools', title: 'Dettagli Tool', content: <ToolsList /> },
        { id: 'warnings', title: 'Avvisi', content: <WarningsList /> }
      ]}
      variant="minimal"
    />
  </div>
)
```

## Note Tecniche

- Tutti i componenti sono `'use client'` per compatibilità Next.js
- TypeScript tipizzato forte con interfacce complete
- Accessibilità con stati hover/focus appropriati
- Responsive design con Tailwind CSS
- Testing completo con Vitest e React Testing Library
- Documentazione Storybook per ogni variante

## Contribuire

Quando aggiungi nuovi componenti common:

1. Crea il componente in `./ComponentName.tsx`
2. Esporta nel `./index.ts`
3. Aggiorna questo README
4. Quando Storybook/Vitest saranno configurati:
   - Aggiungi le stories in `./ComponentName.stories.tsx`
   - Aggiungi i test in `./ComponentName.test.tsx` 
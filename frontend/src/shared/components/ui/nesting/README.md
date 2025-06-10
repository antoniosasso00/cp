# Nesting UI Components Library

A comprehensive React/Tailwind component library for nesting visualization in CarbonPilot aerospace manufacturing system.

## Overview

This library provides modular, reusable components for displaying batch nesting results, tool positions, autoclave information, and interactive canvas controls. All components follow modern React patterns with TypeScript support and Tailwind CSS styling.

## Installation & Usage

```tsx
import { 
  NestingCanvas, 
  BatchStatusBadge, 
  EfficiencyMeter 
} from '@/shared/components/ui/nesting'
```

## Components

### 🏷️ BatchStatusBadge

Status badges with consistent styling and icons for batch states.

```tsx
<BatchStatusBadge 
  status="confermato" 
  size="md" 
  variant="solid" 
/>
```

**Props:**
- `status`: `'draft' | 'sospeso' | 'confermato' | 'loaded' | 'cured' | 'terminato'`
- `size`: `'sm' | 'md' | 'lg'` (default: `'md'`)
- `variant`: `'default' | 'outline' | 'solid'` (default: `'default'`)

**Variants:**
- `BatchStatusBadge` - Standard badge with shadcn/ui styling
- Utility functions: `getBatchStatusColor()`, `getBatchStatusLabel()`, `getBatchStatusIcon()`

### 📊 EfficiencyMeter

Progress bars with color-coded efficiency thresholds.

```tsx
<EfficiencyMeter 
  percentage={75} 
  size="lg" 
  showLabel={true} 
/>
```

**Props:**
- `percentage`: `number` (0-100)
- `size`: `'sm' | 'md' | 'lg'` (default: `'md'`)
- `showLabel`: `boolean` (default: `true`)

**Thresholds:**
- 🔴 Poor: < 30%
- 🟡 Average: 30-50%
- 🟢 Good: 50-85%
- 🟢 Excellent: > 85%

### 🎮 NestingControls

Interactive controls for zoom, grid, and view options.

```tsx
<NestingControls
  onZoomIn={handleZoomIn}
  onZoomOut={handleZoomOut}
  onZoomReset={handleZoomReset}
  onToggleGrid={handleToggleGrid}
  showGrid={true}
  zoom={1.2}
/>
```

**Features:**
- Zoom in/out/reset controls
- Grid and ruler toggles
- Tooltips toggle
- Fullscreen option
- Custom hook: `useNestingControls()`

### 📐 GridLayer

Canvas grid with ruler measurements for spatial reference.

```tsx
<GridLayer
  width={1000}
  height={800}
  showRuler={true}
  gridSpacing={100}
/>
```

**Features:**
- Configurable grid spacing (default: 100mm)
- Ruler with cm measurements
- Performance optimized for large canvases
- Variant: `AdaptiveGridLayer` with major/minor spacing

### 🔧 ToolRect

Visual representation of tools with state-based coloring.

```tsx
<ToolRect
  tool={toolPosition}
  onClick={handleToolClick}
  isSelected={false}
  showTooltips={true}
/>
```

**States:**
- 🟢 Valid: Properly positioned
- 🟡 Rotated: Tool has been rotated
- 🟠 Out of Bounds: Exceeds autoclave dimensions
- 🔴 Excluded: Excluded from batch

### 📋 ToolPositionCard

Information cards displaying tool details and metrics.

```tsx
<ToolPositionCard
  tool={toolPosition}
  selected={false}
  onClick={handleSelect}
/>
```

**Features:**
- Position coordinates (x, y)
- Dimensions (width × height)
- Weight and part numbers
- Status indicators
- Variant: `CompactToolPositionCard`

### 🏭 AutoclaveInfoCard

Autoclave information with efficiency integration.

```tsx
<AutoclaveInfoCard
  autoclave={autoclaveInfo}
  efficiency={75}
  metrics={batchMetrics}
/>
```

**Features:**
- Autoclave specifications
- Efficiency visualization
- Capacity metrics
- Variants: `CompactAutoclaveInfoCard`, `AutoclaveHeader`

### 🎨 NestingCanvas

Main orchestrating component that integrates all other components.

```tsx
<NestingCanvas
  batchData={batchData}
  showControls={true}
  showGrid={true}
  showRuler={true}
  onToolClick={handleToolClick}
/>
```

**Features:**
- Complete nesting visualization
- Interactive tool selection
- Zoom and pan controls
- Grid and ruler overlays
- Error handling and loading states
- Variants: `SimpleNestingCanvas`, `NestingCanvasOverview`

## TypeScript Support

All components include comprehensive TypeScript interfaces:

```tsx
interface ToolPosition {
  odl_id: number
  x: number
  y: number
  width: number
  height: number
  peso: number
  rotated: boolean | string
  part_number?: string
  tool_nome?: string
  excluded?: boolean
}

interface AutoclaveInfo {
  id: number
  nome: string
  lunghezza: number
  larghezza_piano: number
  codice: string
}
```

## Styling

Components use Tailwind CSS with shadcn/ui base components:
- Consistent color palette
- Responsive design patterns
- Dark mode support (where applicable)
- Accessibility-first approach

## Testing

### Playwright Tests
```bash
npx playwright test tests/nesting-components.spec.ts
```

### Manual Testing
See `__stories__/examples.tsx` for interactive examples of all components.

## Performance

- **Optimized rendering** for large datasets (100+ tools)
- **Memoized components** to prevent unnecessary re-renders
- **Lazy loading** for complex canvas operations
- **Tree-shaking** support for minimal bundle size

## Accessibility

- ARIA labels on interactive elements
- Keyboard navigation support
- Screen reader compatible
- High contrast color schemes
- Focus management

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Dependencies

- React 18+
- Tailwind CSS 3+
- shadcn/ui components
- Lucide React (icons)
- Konva.js (canvas rendering)

## Migration

For migrating from legacy components, see [MIGRATION.md](./MIGRATION.md).

## Examples

Check `__stories__/examples.tsx` for comprehensive usage examples:

```tsx
import { NestingComponentsExamples } from '@/shared/components/ui/nesting/__stories__/examples'

// Use in development or documentation
<NestingComponentsExamples />
```

## Contributing

1. Follow existing component patterns
2. Include TypeScript interfaces
3. Add examples to `__stories__/examples.tsx`
4. Update tests in `tests/`
5. Document props and variants

## License

Part of the CarbonPilot aerospace manufacturing system. 
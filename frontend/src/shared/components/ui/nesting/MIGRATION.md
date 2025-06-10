# Nesting UI Components Migration Guide

## Overview

This document outlines the migration from legacy nesting components to the new centralized Nesting UI Components Library located in `frontend/src/shared/components/ui/nesting/`.

## New Components Library Structure

```
frontend/src/shared/components/ui/nesting/
├── types.ts                    # TypeScript interfaces
├── index.ts                    # Main exports
├── batch-status-badge.tsx      # Status badges with variants
├── efficiency-meter.tsx        # Progress bars for efficiency
├── nesting-controls.tsx        # Zoom and view controls
├── grid-layer.tsx             # Canvas grid and ruler
├── tool-rect.tsx              # Tool visualization
├── tool-position-card.tsx     # Tool information cards
├── autoclave-info-card.tsx    # Autoclave information
├── nesting-canvas.tsx         # Main orchestrating component
├── __stories__/               # Examples and documentation
│   └── examples.tsx
└── tests/                     # Playwright tests
    └── nesting-components.spec.ts
```

## Legacy Components to Remove

### 1. Legacy NestingCanvas
**Location:** `frontend/src/modules/nesting/result/[batch_id]/NestingCanvas.tsx`
**Size:** 989 lines
**Issues:** 
- Monolithic component with mixed concerns
- Duplicated functionality now available in modular components
- Hard to maintain and test

**Migration:**
```tsx
// OLD - Legacy monolithic component
import NestingCanvas from '@/modules/nesting/result/[batch_id]/NestingCanvas'

// NEW - Modular component from UI library
import { NestingCanvas } from '@/shared/components/ui/nesting'
```

### 2. Inline Status Badges
**Location:** Various files using inline Badge components for batch status
**Example:** `frontend/src/shared/components/batch-nesting/BatchListWithControls.tsx`

**Migration:**
```tsx
// OLD - Inline badge with manual styling
<Badge className={`${statusColor} px-2 py-1`}>
  <StatusIcon className="h-3 w-3 mr-1" />
  {batch.stato.charAt(0).toUpperCase() + batch.stato.slice(1)}
</Badge>

// NEW - Standardized component
import { BatchStatusBadge } from '@/shared/components/ui/nesting'
<BatchStatusBadge status={batch.stato} size="md" />
```

### 3. Custom Grid/Ruler Components
**Location:** Embedded in legacy NestingCanvas
**Issues:** 
- Performance issues with too many DOM elements
- Not reusable across components

**Migration:**
```tsx
// OLD - Inline grid component
const GridLayer = ({ width, height }) => { /* 50+ lines */ }

// NEW - Optimized reusable component
import { GridLayer } from '@/shared/components/ui/nesting'
<GridLayer width={width} height={height} showRuler={true} />
```

## Migration Steps

### Phase 1: Update Imports
1. Replace legacy NestingCanvas imports with new library imports
2. Update component props to match new interfaces
3. Test functionality in development

### Phase 2: Remove Legacy Files
1. Delete `frontend/src/modules/nesting/result/[batch_id]/NestingCanvas.tsx`
2. Remove inline status badge implementations
3. Clean up unused utility functions

### Phase 3: Update References
1. Update any remaining references to legacy components
2. Update documentation and examples
3. Run full test suite

## Benefits of Migration

### 1. Modularity
- Each component has a single responsibility
- Easy to test individual components
- Reusable across different contexts

### 2. Consistency
- Standardized props and interfaces
- Consistent styling and behavior
- Better TypeScript support

### 3. Performance
- Optimized rendering for large datasets
- Proper memoization and state management
- Reduced bundle size through tree-shaking

### 4. Maintainability
- Clear separation of concerns
- Comprehensive test coverage
- Better error handling

## Component Mapping

| Legacy | New Component | Notes |
|--------|---------------|-------|
| Inline status badges | `BatchStatusBadge` | Supports variants and sizes |
| Manual efficiency display | `EfficiencyMeter` | Color-coded thresholds |
| Embedded zoom controls | `NestingControls` | Consistent UI patterns |
| Inline grid rendering | `GridLayer` | Performance optimized |
| Tool rectangles | `ToolRect` | State-based coloring |
| Tool info displays | `ToolPositionCard` | Standardized layout |
| Autoclave headers | `AutoclaveInfoCard` | Comprehensive info display |
| Monolithic canvas | `NestingCanvas` | Orchestrates all components |

## Testing

The new components include:
- Playwright end-to-end tests
- Component examples for manual testing
- TypeScript interfaces for compile-time safety

## Support

For questions about migration:
1. Check the examples in `__stories__/examples.tsx`
2. Review the TypeScript interfaces in `types.ts`
3. Run the Playwright tests to verify functionality

## Timeline

- **Phase 1:** Update imports and test (1-2 days)
- **Phase 2:** Remove legacy files (1 day)  
- **Phase 3:** Final cleanup and testing (1 day)

Total estimated time: 3-4 days 
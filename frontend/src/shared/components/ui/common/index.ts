// Common UI Components
export { MetricCard, CompactMetricCard } from './MetricCard'
export type { MetricCardProps } from './MetricCard'

export { StepSidebar, useStepNavigation } from './StepSidebar'
export type { StepSidebarProps, StepItem } from './StepSidebar'

export { AccordionPanel, SingleAccordion, useAccordionState } from './AccordionPanel'
export type { AccordionPanelProps, AccordionPanelItem, SingleAccordionProps } from './AccordionPanel'

// Re-export from nesting for compatibility (with alias to avoid conflicts)
export { 
  ToolRect as NestingToolRect, 
  SimpleToolRect as NestingSimpleToolRect, 
  normalizeToolData, 
  TOOL_COLORS,
  getToolColor,
  getToolStatus 
} from '../nesting/tool-rect'
export type { ToolRectProps as NestingToolRectProps } from '../nesting/types' 
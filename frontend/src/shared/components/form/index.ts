export { FormField } from './FormField'
export { FormSelect } from './FormSelect'
export { FormWrapper } from './FormWrapper'

// Tipi utili per i form
export interface SelectOption {
  value: string | number
  label: string
  disabled?: boolean
}

export interface FormFieldBaseProps {
  label: string
  name: string
  disabled?: boolean
  loading?: boolean
  error?: string
  description?: string
  required?: boolean
  className?: string
} 
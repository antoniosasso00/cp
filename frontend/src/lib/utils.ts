import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Utility per combinare classi tailwind in modo efficiente
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Formatta una data in formato leggibile italiano
 */
export function formatDateIT(date: string | Date): string {
  if (!date) return '';
  return new Date(date).toLocaleDateString('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Ritarda l'esecuzione di una funzione
 */
export const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms)); 
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Utility per combinare classi tailwind in modo efficiente
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Formatta una data in formato italiano (DD/MM/YYYY)
 * @param date Data da formattare (string, Date, o null/undefined)
 * @returns Data formattata o stringa vuota se input non valido
 */
export function formatDateIT(date: string | Date | null | undefined): string {
  if (!date) return '';
  
  const d = typeof date === 'string' ? new Date(date) : date;
  
  // Verifica che la data sia valida
  if (isNaN(d.getTime())) return '';
  
  return d.toLocaleDateString('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
}

/**
 * Formatta una data e ora in formato italiano (DD/MM/YYYY HH:MM)
 * @param date Data da formattare (string, Date, o null/undefined)
 * @returns Data e ora formattata o stringa vuota se input non valido
 */
export function formatDateTime(date: string | Date | null | undefined): string {
  if (!date) return '';
  
  const d = typeof date === 'string' ? new Date(date) : date;
  
  // Verifica che la data sia valida
  if (isNaN(d.getTime())) return '';
  
  return d.toLocaleDateString('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * Formatta la durata in ore e minuti
 * @param minutes Durata in minuti (numero o null)
 * @returns Durata formattata (es. "2h 15m") o "-" se null
 */
export function formatDuration(minutes: number | null): string {
  if (minutes === null) return '-';
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  
  if (hours === 0) {
    return `${mins} min`;
  }
  
  return `${hours}h ${mins}m`;
}

/**
 * Ritarda l'esecuzione di una funzione
 */
export const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms)); 
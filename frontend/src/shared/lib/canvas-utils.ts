/**
 * Canvas utilities per l'auto-fit e gestione dimensioni
 */
import React from 'react'

interface FitToContainerOptions {
  /** Padding interno in px */
  padding?: number
  /** Scale massimo consentito */
  maxScale?: number
  /** Se centrare il canvas dopo il fit */
  center?: boolean
}

interface FitResult {
  scale: number
  offsetX: number
  offsetY: number
  containerWidth: number
  containerHeight: number
}

/**
 * Calcola il fit ottimale del canvas nel container
 */
export const fitCanvasToContainer = (
  containerElement: HTMLElement,
  canvasWidth: number,
  canvasHeight: number,
  options: FitToContainerOptions = {}
): FitResult => {
  const {
    padding = 40,
    maxScale = 1.0,
    center = true
  } = options

  const containerWidth = containerElement.offsetWidth
  const containerHeight = containerElement.offsetHeight

  // Calcola area disponibile considerando il padding
  const availableWidth = containerWidth - (padding * 2)
  const availableHeight = containerHeight - (padding * 2)

  // Calcola scale per fit
  const scaleX = availableWidth / canvasWidth
  const scaleY = availableHeight / canvasHeight
  const scale = Math.min(scaleX, scaleY, maxScale)

  // Calcola offset per centrare se richiesto
  let offsetX = padding
  let offsetY = padding

  if (center) {
    const scaledWidth = canvasWidth * scale
    const scaledHeight = canvasHeight * scale
    offsetX = (containerWidth - scaledWidth) / 2
    offsetY = (containerHeight - scaledHeight) / 2
  }

  return {
    scale,
    offsetX,
    offsetY,
    containerWidth,
    containerHeight
  }
}

/**
 * Hook per auto-fit con debounce del resize
 */
export const useCanvasAutoFit = (
  containerRef: React.RefObject<HTMLElement>,
  canvasWidth: number,
  canvasHeight: number,
  options: FitToContainerOptions = {},
  onFitChange?: (result: FitResult) => void
) => {
  const [fitResult, setFitResult] = React.useState<FitResult | null>(null)

  React.useEffect(() => {
    if (!containerRef.current) return

    let resizeTimeout: NodeJS.Timeout

    const handleResize = () => {
      clearTimeout(resizeTimeout)
      resizeTimeout = setTimeout(() => {
        if (containerRef.current) {
          const result = fitCanvasToContainer(
            containerRef.current,
            canvasWidth,
            canvasHeight,
            options
          )
          setFitResult(result)
          onFitChange?.(result)
        }
      }, 100) // 100ms debounce
    }

    // Initial fit
    handleResize()

    // Window resize handler
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      clearTimeout(resizeTimeout)
    }
  }, [containerRef, canvasWidth, canvasHeight, options, onFitChange])

  return fitResult
}

/**
 * Scroll to top e focus elemento
 */
export const scrollToTopAndFocus = (elementId?: string) => {
  // Scroll to top
  window.scrollTo({ top: 0, behavior: 'smooth' })
  
  // Focus elemento se specificato
  if (elementId) {
    setTimeout(() => {
      const element = document.getElementById(elementId)
      if (element) {
        element.focus()
        element.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }, 300) // Aspetta che lo scroll finisca
  }
} 
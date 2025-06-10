import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { 
  ToolRect, 
  SimpleToolRect, 
  calculateDynamicFontSize, 
  isTextVisible, 
  mapODLIdToNumber,
  testSmallAreaRendering
} from './tool-rect'
import type { ToolPosition } from './types'

// Mock per il componente Canvas
jest.mock('@/shared/components/canvas/CanvasWrapper', () => ({
  Rect: ({ children, ...props }: any) => <div data-testid="rect" {...props}>{children}</div>,
  Text: ({ text, ...props }: any) => <span data-testid="text" {...props}>{text}</span>,
  Group: ({ children, ...props }: any) => <div data-testid="group" {...props}>{children}</div>
}))

describe('ToolRect Component', () => {
  const mockTool: ToolPosition = {
    odl_id: 123,
    x: 10,
    y: 20,
    width: 100,
    height: 80,
    peso: 25.5,
    rotated: false,
    part_number: 'P123456',
    numero_odl: '2024001',
    descrizione_breve: 'Test Component Description',
    excluded: false
  }

  const defaultProps = {
    tool: mockTool,
    autoclaveWidth: 1000,
    autoclaveHeight: 800,
    showTooltips: true
  }

  describe('Font Size Calculation', () => {
    test('calculateDynamicFontSize should return appropriate sizes', () => {
      // Test casi estremi
      expect(calculateDynamicFontSize(10, 10)).toBeCloseTo(6, 1) // Area molto piccola
      expect(calculateDynamicFontSize(100, 100)).toBeCloseTo(12, 1) // Area media
      expect(calculateDynamicFontSize(200, 200)).toBeCloseTo(16, 1) // Area grande
      
      // Test limiti
      expect(calculateDynamicFontSize(1, 1)).toBe(6) // Minimo
      expect(calculateDynamicFontSize(1000, 1000)).toBe(16) // Massimo
    })

    test('isTextVisible should work correctly', () => {
      expect(isTextVisible(50, 30, 10)).toBe(true) // Dimensioni sufficienti
      expect(isTextVisible(30, 15, 8)).toBe(false) // Troppo piccolo
      expect(isTextVisible(100, 50, 6)).toBe(false) // Font troppo piccolo
      expect(isTextVisible(80, 40, 12)).toBe(true) // Tutti i requisiti soddisfatti
    })
  })

  describe('ODL Number Mapping', () => {
    test('mapODLIdToNumber should use numero_odl when available', () => {
      const toolWithNumber = { ...mockTool, numero_odl: '2024001' }
      expect(mapODLIdToNumber(toolWithNumber)).toBe('2024001')
    })

    test('mapODLIdToNumber should generate from odl_id when numero_odl missing', () => {
      const toolWithoutNumber = { ...mockTool, numero_odl: '', odl_id: 123 }
      expect(mapODLIdToNumber(toolWithoutNumber)).toBe('ODL000123')
    })

    test('mapODLIdToNumber should handle missing data gracefully', () => {
      const emptyTool = {}
      expect(mapODLIdToNumber(emptyTool)).toBe('ODL000000')
    })
  })

  describe('Small Area Rendering Tests', () => {
    test('testSmallAreaRendering should return expected results', () => {
      const results = testSmallAreaRendering()
      
      expect(results).toHaveLength(4)
      
      // Test primo caso: area troppo piccola
      expect(results[0]).toEqual({
        width: 30,
        height: 20,
        expected: 'No text',
        fontSize: '6.0',
        textVisible: false,
        result: 'Hidden'
      })

      // Test ultimo caso: area grande
      const lastResult = results[results.length - 1]
      expect(lastResult.width).toBe(120)
      expect(lastResult.height).toBe(80)
      expect(lastResult.textVisible).toBe(true)
      expect(lastResult.result).toBe('Visible')
    })
  })

  describe('ToolRect Rendering', () => {
    test('should render basic tool rectangle', () => {
      render(<ToolRect {...defaultProps} />)
      
      const groups = screen.getAllByTestId('group')
      expect(groups.length).toBeGreaterThan(0)
    })

    test('should show ODL number when space permits', () => {
      const largeToolProps = {
        ...defaultProps,
        tool: { ...mockTool, width: 120, height: 80 }
      }
      
      render(<ToolRect {...largeToolProps} />)
      
      const texts = screen.getAllByTestId('text')
      const odlText = texts.find(t => t.textContent?.includes('2024001'))
      expect(odlText).toBeInTheDocument()
    })

    test('should hide text on very small tools', () => {
      const smallToolProps = {
        ...defaultProps,
        tool: { ...mockTool, width: 20, height: 15 }
      }
      
      render(<ToolRect {...smallToolProps} />)
      
      const texts = screen.getAllByTestId('text')
      // Non dovrebbe esserci testo visibile
      expect(texts.length).toBe(0)
    })

    test('should show rotation indicator when rotated', () => {
      const rotatedToolProps = {
        ...defaultProps,
        tool: { ...mockTool, rotated: true }
      }
      
      render(<ToolRect {...rotatedToolProps} />)
      
      const texts = screen.getAllByTestId('text')
      const rotationIndicator = texts.find(t => t.textContent === 'R')
      expect(rotationIndicator).toBeInTheDocument()
    })

    test('should show out of bounds warning', () => {
      const outOfBoundsProps = {
        ...defaultProps,
        tool: { ...mockTool, x: 950, width: 100 }, // Esce dai limiti dell'autoclave (1000px)
        autoclaveWidth: 1000
      }
      
      render(<ToolRect {...outOfBoundsProps} />)
      
      const texts = screen.getAllByTestId('text')
      const warningIndicator = texts.find(t => t.textContent === '!')
      expect(warningIndicator).toBeInTheDocument()
    })
  })

  describe('SimpleToolRect', () => {
    test('should render simplified version', () => {
      render(<SimpleToolRect {...defaultProps} />)
      
      const groups = screen.getAllByTestId('group')
      expect(groups.length).toBeGreaterThan(0)
    })

    test('should show only ODL number in simple version', () => {
      const largeToolProps = {
        ...defaultProps,
        tool: { ...mockTool, width: 100, height: 60 }
      }
      
      render(<SimpleToolRect {...largeToolProps} />)
      
      const texts = screen.getAllByTestId('text')
      expect(texts.length).toBe(1) // Solo numero ODL
      expect(texts[0].textContent).toBe('2024001')
    })
  })

  describe('Tooltip Integration', () => {
    test('should handle mouse events for tooltip', () => {
      const { container } = render(<ToolRect {...defaultProps} />)
      
      const toolGroup = container.querySelector('[data-testid="group"]')
      expect(toolGroup).toBeInTheDocument()
      
      // Test hover events (gli eventi mouse sono gestiti tramite props)
      expect(toolGroup).toHaveAttribute('onMouseEnter')
      expect(toolGroup).toHaveAttribute('onMouseLeave')
    })

    test('should disable tooltips when showTooltips is false', () => {
      const noTooltipsProps = { ...defaultProps, showTooltips: false }
      render(<ToolRect {...noTooltipsProps} />)
      
      // Il componente dovrebbe renderizzare normalmente anche senza tooltip
      const groups = screen.getAllByTestId('group')
      expect(groups.length).toBeGreaterThan(0)
    })
  })

  describe('Interactive Features', () => {
    test('should handle click events', () => {
      const onClickMock = jest.fn()
      const clickableProps = { ...defaultProps, onClick: onClickMock }
      
      const { container } = render(<ToolRect {...clickableProps} />)
      
      const toolGroup = container.querySelector('[data-testid="group"]')
      expect(toolGroup).toHaveStyle('cursor: pointer')
    })

    test('should show selection indicator when selected', () => {
      const selectedProps = { ...defaultProps, isSelected: true }
      render(<ToolRect {...selectedProps} />)
      
      const rects = screen.getAllByTestId('rect')
      // Dovrebbe esserci un rettangolo aggiuntivo per l'indicatore di selezione
      expect(rects.length).toBeGreaterThan(1)
    })
  })

  describe('Performance Edge Cases', () => {
    test('should handle malformed tool data', () => {
      const malformedTool = {
        odl_id: '123', // String invece di number
        x: 'invalid',
        y: null,
        width: undefined,
        height: 0,
        peso: 'heavy',
        rotated: 'yes'
      }
      
      // Non dovrebbe crashare
      expect(() => {
        render(<ToolRect tool={malformedTool as any} autoclaveWidth={1000} autoclaveHeight={800} />)
      }).not.toThrow()
    })

    test('should handle missing required props gracefully', () => {
      const minimalTool = { odl_id: 1, x: 0, y: 0, width: 50, height: 50, peso: 0, rotated: false }
      
      expect(() => {
        render(<ToolRect tool={minimalTool} autoclaveWidth={1000} autoclaveHeight={800} />)
      }).not.toThrow()
    })
  })
}) 
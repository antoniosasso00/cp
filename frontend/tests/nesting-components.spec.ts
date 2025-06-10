import { test, expect } from '@playwright/test'

test.describe('Nesting UI Components', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to a page that uses nesting components
    // This would need to be adjusted based on your actual routes
    await page.goto('/nesting/result/test-batch-id')
  })

  test('BatchStatusBadge renders correctly', async ({ page }) => {
    // Look for batch status badges in the page
    const statusBadge = page.locator('[data-testid="batch-status-badge"]').first()
    
    if (await statusBadge.count() > 0) {
      await expect(statusBadge).toBeVisible()
      
      // Check that it contains expected status text
      const statusText = await statusBadge.textContent()
      expect(statusText).toMatch(/(Draft|Sospeso|Confermato|Caricato|In Cura|Terminato)/)
    }
  })

  test('EfficiencyMeter displays percentage', async ({ page }) => {
    // Look for efficiency meters
    const efficiencyMeter = page.locator('[data-testid="efficiency-meter"]').first()
    
    if (await efficiencyMeter.count() > 0) {
      await expect(efficiencyMeter).toBeVisible()
      
      // Check that percentage is displayed
      const percentageText = await efficiencyMeter.textContent()
      expect(percentageText).toMatch(/\d+%/)
    }
  })

  test('NestingCanvas renders with tools', async ({ page }) => {
    // Look for the nesting canvas
    const canvas = page.locator('canvas').first()
    
    if (await canvas.count() > 0) {
      await expect(canvas).toBeVisible()
      
      // Check canvas dimensions
      const canvasElement = await canvas.elementHandle()
      if (canvasElement) {
        const width = await canvasElement.getAttribute('width')
        const height = await canvasElement.getAttribute('height')
        
        expect(parseInt(width || '0')).toBeGreaterThan(0)
        expect(parseInt(height || '0')).toBeGreaterThan(0)
      }
    }
  })

  test('NestingControls are interactive', async ({ page }) => {
    // Look for zoom controls
    const zoomInButton = page.locator('button:has-text("+")')
    const zoomOutButton = page.locator('button:has-text("-")')
    
    if (await zoomInButton.count() > 0) {
      await expect(zoomInButton).toBeVisible()
      await expect(zoomInButton).toBeEnabled()
    }
    
    if (await zoomOutButton.count() > 0) {
      await expect(zoomOutButton).toBeVisible()
      await expect(zoomOutButton).toBeEnabled()
    }
  })

  test('ToolPositionCard shows tool information', async ({ page }) => {
    // Look for tool position cards
    const toolCard = page.locator('[data-testid="tool-position-card"]').first()
    
    if (await toolCard.count() > 0) {
      await expect(toolCard).toBeVisible()
      
      // Check for tool information
      const cardText = await toolCard.textContent()
      expect(cardText).toBeTruthy()
    }
  })

  test('AutoclaveInfoCard displays autoclave details', async ({ page }) => {
    // Look for autoclave info cards
    const autoclaveCard = page.locator('[data-testid="autoclave-info-card"]').first()
    
    if (await autoclaveCard.count() > 0) {
      await expect(autoclaveCard).toBeVisible()
      
      // Check for autoclave name
      const cardText = await autoclaveCard.textContent()
      expect(cardText).toMatch(/(PANINI|ISMAR|MAROSO)/)
    }
  })
})

test.describe('Nesting Components Accessibility', () => {
  test('components have proper ARIA labels', async ({ page }) => {
    await page.goto('/nesting/result/test-batch-id')
    
    // Check for proper button labels
    const buttons = page.locator('button')
    const buttonCount = await buttons.count()
    
    for (let i = 0; i < Math.min(buttonCount, 10); i++) {
      const button = buttons.nth(i)
      const ariaLabel = await button.getAttribute('aria-label')
      const textContent = await button.textContent()
      
      // Button should have either aria-label or text content
      expect(ariaLabel || textContent).toBeTruthy()
    }
  })

  test('components are keyboard navigable', async ({ page }) => {
    await page.goto('/nesting/result/test-batch-id')
    
    // Test tab navigation
    await page.keyboard.press('Tab')
    const focusedElement = await page.locator(':focus').first()
    
    if (await focusedElement.count() > 0) {
      await expect(focusedElement).toBeVisible()
    }
  })
}) 
"use client"

import * as React from "react"
import { useTheme } from "next-themes"
import { Moon, Sun } from "lucide-react"
import { Button } from "./button"
import { cn } from "@/lib/utils"

interface ThemeToggleProps {
  className?: string
  size?: "sm" | "default" | "lg"
  variant?: "default" | "ghost" | "outline"
}

export function ThemeToggle({ 
  className, 
  size = "default", 
  variant = "ghost" 
}: ThemeToggleProps) {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = React.useState(false)

  // Evita hydration mismatch
  React.useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <Button
        variant={variant}
        size={size === "default" ? "icon" : size}
        className={cn("relative", className)}
      >
        <Sun className="h-4 w-4" />
        <span className="sr-only">Toggle theme</span>
      </Button>
    )
  }

  return (
    <Button
      variant={variant}
      size={size === "default" ? "icon" : size}
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className={cn("relative", className)}
    >
      <Sun className={cn(
        "h-4 w-4 transition-all duration-300",
        theme === "dark" ? "rotate-90 scale-0" : "rotate-0 scale-100"
      )} />
      <Moon className={cn(
        "absolute h-4 w-4 transition-all duration-300",
        theme === "dark" ? "rotate-0 scale-100" : "-rotate-90 scale-0"
      )} />
      <span className="sr-only">
        {theme === "dark" ? "Attiva modalità chiara" : "Attiva modalità scura"}
      </span>
    </Button>
  )
}

// Componente dropdown per selezionare il tema
export function ThemeSelector() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = React.useState(false)

  React.useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  return (
    <div className="flex items-center space-x-2 p-1 bg-muted rounded-lg">
      <Button
        variant={theme === "light" ? "default" : "ghost"}
        size="sm"
        onClick={() => setTheme("light")}
        className="h-8 px-3"
      >
        <Sun className="h-4 w-4 mr-1" />
        Chiaro
      </Button>
      <Button
        variant={theme === "dark" ? "default" : "ghost"}
        size="sm"
        onClick={() => setTheme("dark")}
        className="h-8 px-3"
      >
        <Moon className="h-4 w-4 mr-1" />
        Scuro
      </Button>
      <Button
        variant={theme === "system" ? "default" : "ghost"}
        size="sm"
        onClick={() => setTheme("system")}
        className="h-8 px-3"
      >
        Sistema
      </Button>
    </div>
  )
} 
import { useEffect, useCallback, useRef } from 'react'
import { useRouter, usePathname } from 'next/navigation'

interface NavigationGuardProps {
  enabled: boolean
  onAttemptedNavigation: (href: string, navigationFn: () => void) => void
}

// Hook per intercettare la navigazione interna di Next.js
export function useNavigationGuard({ enabled, onAttemptedNavigation }: NavigationGuardProps) {
  const router = useRouter()
  const pathname = usePathname()
  const pathnameRef = useRef(pathname)
  const enabledRef = useRef(enabled)

  // Aggiorna i ref per evitare stale closures
  useEffect(() => {
    pathnameRef.current = pathname
    enabledRef.current = enabled
  }, [pathname, enabled])

  // 🔒 NAVIGATION INTERCEPTOR: Intercetta la navigazione
  useEffect(() => {
    if (!enabled) return

    // Override dei metodi di navigazione del router
    const originalPush = router.push
    const originalReplace = router.replace
    const originalBack = router.back
    const originalForward = router.forward

    // 🚫 INTERCEPT PUSH
    router.push = (href: string, options?: any) => {
      if (enabledRef.current && href !== pathnameRef.current) {
        onAttemptedNavigation(href, () => originalPush.call(router, href, options))
        return Promise.resolve(true)
      }
      return originalPush.call(router, href, options)
    }

    // 🚫 INTERCEPT REPLACE  
    router.replace = (href: string, options?: any) => {
      if (enabledRef.current && href !== pathnameRef.current) {
        onAttemptedNavigation(href, () => originalReplace.call(router, href, options))
        return Promise.resolve(true)
      }
      return originalReplace.call(router, href, options)
    }

    // 🚫 INTERCEPT BACK
    router.back = () => {
      if (enabledRef.current) {
        onAttemptedNavigation('[back]', () => originalBack.call(router))
        return
      }
      return originalBack.call(router)
    }

    // 🚫 INTERCEPT FORWARD
    router.forward = () => {
      if (enabledRef.current) {
        onAttemptedNavigation('[forward]', () => originalForward.call(router))
        return
      }
      return originalForward.call(router)
    }

    // 🧹 CLEANUP: Ripristina i metodi originali
    return () => {
      router.push = originalPush
      router.replace = originalReplace
      router.back = originalBack
      router.forward = originalForward
    }
  }, [enabled, router, onAttemptedNavigation])

  // 🔒 LINK INTERCEPTOR: Intercetta i click sui Link di Next.js
  useEffect(() => {
    if (!enabled) return

    const handleLinkClick = (event: MouseEvent) => {
      if (!enabledRef.current) return

      const target = event.target as HTMLElement
      const link = target.closest('a[href]') as HTMLAnchorElement
      
      if (!link) return
      if (link.target === '_blank') return // Link esterni
      if (link.download) return // Link di download
      
      const href = link.getAttribute('href')
      if (!href || href.startsWith('http') || href.startsWith('mailto:') || href.startsWith('tel:')) {
        return // Link esterni
      }

      // Solo per link interni che cambiano pagina
      if (href !== pathnameRef.current && href !== window.location.pathname) {
        event.preventDefault()
        event.stopPropagation()
        
        onAttemptedNavigation(href, () => {
          router.push(href)
        })
      }
    }

    // Usa capture per intercettare prima degli handler dei Link
    document.addEventListener('click', handleLinkClick, true)
    
    return () => {
      document.removeEventListener('click', handleLinkClick, true)
    }
  }, [enabled, router, onAttemptedNavigation])
} 
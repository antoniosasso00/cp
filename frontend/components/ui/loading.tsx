import { Loader2 } from 'lucide-react';

interface LoadingProps {
  size?: number;
  className?: string;
}

export function Loading({ size = 24, className = '' }: LoadingProps) {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      <Loader2 className="animate-spin" size={size} />
    </div>
  );
}

export function LoadingPage() {
  return (
    <div className="flex h-screen w-full items-center justify-center">
      <Loading size={48} />
    </div>
  );
}

export function LoadingOverlay() {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <Loading size={48} />
    </div>
  );
} 
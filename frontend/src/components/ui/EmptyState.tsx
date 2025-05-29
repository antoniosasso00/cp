import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  message: string;
  description?: string;
  icon?: React.ReactNode;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  message,
  description,
  icon = '🛠',
  className,
  size = 'md'
}) => {
  const sizeClasses = {
    sm: 'py-8 px-4',
    md: 'py-12 px-6',
    lg: 'py-16 px-8'
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  };

  const iconSizeClasses = {
    sm: 'text-2xl',
    md: 'text-3xl',
    lg: 'text-4xl'
  };

  return (
    <Card className={cn(
      "border-dashed border-2 border-gray-200 bg-gray-50/50",
      className
    )}>
      <CardContent className={cn(
        "flex flex-col items-center justify-center text-center",
        sizeClasses[size]
      )}>
        <div className={cn(
          "mb-3 opacity-60",
          iconSizeClasses[size]
        )}>
          {icon}
        </div>
        <h3 className={cn(
          "font-medium text-gray-600 mb-1",
          textSizeClasses[size]
        )}>
          {message}
        </h3>
        {description && (
          <p className="text-sm text-gray-500 max-w-md">
            {description}
          </p>
        )}
      </CardContent>
    </Card>
  );
};

export default EmptyState; 
import React from 'react';
import { cn } from '../../utils';

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'text' | 'circle' | 'rect';
  size?: 'sm' | 'md' | 'lg';
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className,
  variant = 'default',
  size = 'md',
  ...props
}) => {
  const baseStyles = 'animate-pulse bg-gray-200 dark:bg-white/5 rounded';

  const variants = {
    default: 'rounded-lg',
    text: 'rounded',
    circle: 'rounded-full',
    rect: 'rounded-none',
  };

  const sizes = {
    sm: 'h-4',
    md: 'h-6',
    lg: 'h-8',
  };

  const circleSizes = {
    sm: 'h-8 w-8',
    md: 'h-12 w-12',
    lg: 'h-16 w-16',
  };

  const sizeClass = variant === 'circle' ? circleSizes[size] : sizes[size];

  return <div className={cn(baseStyles, variants[variant], sizeClass, className)} {...props} />;
};

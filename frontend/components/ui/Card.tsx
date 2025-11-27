import React from 'react';
import { cn } from '../../utils';

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => (
  <div
    className={cn(
      // Apple HIG:
      // Light: Very subtle black alpha border (black/5) instead of solid gray.
      // Dark: White/5 border for separation without harsh lines.
      'bg-white/80 dark:bg-gray-900/40 backdrop-blur-xl rounded-xl border border-black/5 dark:border-white/5 shadow-sm transition-all duration-200',
      className
    )}
    {...props}
  >
    {children}
  </div>
);

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => (
  <div
    className={cn('px-6 py-4 border-b border-black/5 dark:border-white/5', className)}
    {...props}
  >
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  className,
  children,
  ...props
}) => (
  <h3
    className={cn(
      'text-base font-semibold text-gray-900 dark:text-gray-100 tracking-tight',
      className
    )}
    {...props}
  >
    {children}
  </h3>
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  className,
  children,
  ...props
}) => (
  <p className={cn('text-sm text-gray-500 dark:text-gray-400 mt-1', className)} {...props}>
    {children}
  </p>
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => (
  <div className={cn('p-6', className)} {...props}>
    {children}
  </div>
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => (
  <div
    className={cn(
      'px-6 py-3 bg-gray-50/50 dark:bg-white/5 border-t border-black/5 dark:border-white/5 rounded-b-xl flex items-center',
      className
    )}
    {...props}
  >
    {children}
  </div>
);

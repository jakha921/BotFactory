import React from 'react';
import { Loader2 } from 'lucide-react';
import { motion, type HTMLMotionProps } from 'framer-motion';
import { cn } from '../../utils';

interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'size'> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'icon';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  className,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  icon,
  disabled,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg border select-none';

  const variants = {
    // Apple HIG: Solid color, no strong shadow, clear contrast
    primary:
      'bg-primary hover:bg-primary-dark text-white border-transparent focus:ring-primary-light shadow-sm hover:shadow',

    // Apple HIG: Subtle border (black/10 instead of gray-200), clean background. Dark mode uses white-alpha border.
    secondary:
      'bg-white dark:bg-white/5 text-gray-700 dark:text-gray-200 border-black/10 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/10 shadow-sm',

    // Apple HIG: Plain text/icon, background appears on hover
    ghost:
      'bg-transparent border-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-100/50 dark:hover:bg-white/10 hover:text-gray-900 dark:hover:text-gray-200',

    danger:
      'bg-red-500 hover:bg-red-600 text-white border-transparent focus:ring-red-400 shadow-sm',

    icon: 'p-2 bg-transparent border-transparent hover:bg-gray-100 dark:hover:bg-white/10 rounded-full text-gray-500 dark:text-gray-400',
  };

  const sizes = {
    sm: 'text-xs px-3 py-1.5 h-7 gap-1.5',
    md: 'text-sm px-4 py-2 h-9 gap-2',
    lg: 'text-base px-6 py-3 h-11 gap-2.5',
  };

  const iconSizes = {
    sm: 'h-7 w-7 p-0',
    md: 'h-9 w-9 p-0',
    lg: 'h-11 w-11 p-0',
  };

  const activeSize = variant === 'icon' ? iconSizes[size] : sizes[size];

  return (
    <motion.button
      whileTap={{ scale: disabled || isLoading ? 1 : 0.97 }}
      className={cn(baseStyles, variants[variant], activeSize, className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
      {!isLoading && icon && <span className="flex-shrink-0">{icon}</span>}
      {children as React.ReactNode}
    </motion.button>
  );
};

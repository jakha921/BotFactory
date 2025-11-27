import React from 'react';
import { cn } from '../../utils';
import { Label } from './Label';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Textarea: React.FC<TextareaProps> = ({
  label,
  error,
  helperText,
  className,
  id,
  required,
  ...props
}) => {
  const textareaId = id || React.useId();

  return (
    <div className="w-full space-y-1.5">
      {label && (
        <Label htmlFor={textareaId} required={required}>
          {label}
        </Label>
      )}
      <textarea
        id={textareaId}
        className={cn(
          'block w-full rounded-lg border px-3 py-2 shadow-sm transition-colors sm:text-sm min-h-[80px] resize-y focus:outline-none focus:ring-2 focus:ring-primary/20',
          // Light: Subtle border (black/10)
          'border-black/10 bg-white text-gray-900 placeholder:text-gray-400 focus:border-primary',
          // Dark: Glass effect with subtle white border (white/10)
          'dark:border-white/10 dark:bg-white/5 dark:text-gray-100 dark:placeholder:text-gray-500 dark:focus:border-primary/50',
          error && 'border-red-500 focus:border-red-500 focus:ring-red-500',
          className
        )}
        {...props}
      />
      {error && (
        <p className="text-sm text-red-500 animate-in fade-in slide-in-from-top-1">{error}</p>
      )}
      {!error && helperText && (
        <p className="text-xs text-gray-500 dark:text-gray-400">{helperText}</p>
      )}
    </div>
  );
};

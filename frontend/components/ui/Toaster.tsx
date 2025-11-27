import React from 'react';
import { Toaster as SonnerToaster } from 'sonner';

export const Toaster: React.FC = () => {
  return (
    <SonnerToaster
      position="top-right"
      expand={true}
      richColors={true}
      closeButton
      toastOptions={{
        classNames: {
          toast:
            'bg-white/90 dark:bg-gray-900/90 backdrop-blur-xl border border-black/5 dark:border-white/5 rounded-xl shadow-lg',
          title: 'text-gray-900 dark:text-white font-medium',
          description: 'text-gray-500 dark:text-gray-400 text-sm',
          error: 'border-red-200 dark:border-red-900/50',
          success: 'border-emerald-200 dark:border-emerald-900/50',
          warning: 'border-amber-200 dark:border-amber-900/50',
          info: 'border-blue-200 dark:border-blue-900/50',
        },
      }}
    />
  );
};

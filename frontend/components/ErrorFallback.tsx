import React from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from './ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/Card';

interface ErrorFallbackProps {
  error: Error | null;
  resetErrorBoundary?: () => void;
}

export const ErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetErrorBoundary }) => {
  const handleReset = () => {
    if (resetErrorBoundary) {
      resetErrorBoundary();
    } else {
      window.location.reload();
    }
  };

  const handleGoHome = () => {
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50/50 dark:bg-gray-950">
      <Card className="max-w-md w-full border-red-200 dark:border-red-900/50">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-full bg-red-100 dark:bg-red-900/30">
              <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <CardTitle className="text-red-900 dark:text-red-100">Что-то пошло не так</CardTitle>
              <CardDescription>Произошла непредвиденная ошибка</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50/50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30">
              <p className="text-sm font-medium text-red-900 dark:text-red-200 mb-1">
                {error.name || 'Error'}
              </p>
              <p className="text-xs text-red-700 dark:text-red-300 font-mono break-all">
                {error.message || 'Unknown error occurred'}
              </p>
            </div>
          )}

          <div className="flex gap-2">
            <Button
              variant="primary"
              onClick={handleReset}
              icon={<RefreshCw className="w-4 h-4" />}
            >
              Попробовать снова
            </Button>
            <Button variant="secondary" onClick={handleGoHome} icon={<Home className="w-4 h-4" />}>
              На главную
            </Button>
          </div>

          {process.env.NODE_ENV === 'development' && error && (
            <details className="mt-4 p-3 rounded-lg bg-gray-100 dark:bg-white/5 border border-black/5 dark:border-white/5">
              <summary className="text-xs font-medium text-gray-600 dark:text-gray-400 cursor-pointer mb-2">
                Детали ошибки (только для разработки)
              </summary>
              <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-auto max-h-48 font-mono">
                {error.stack || error.toString()}
              </pre>
            </details>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

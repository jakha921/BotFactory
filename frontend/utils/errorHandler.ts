import { toast } from 'sonner';
import { ApiError } from '../types';

/**
 * Handles API errors and displays user-friendly messages
 * @param error - The error object (can be ApiError, Error, or unknown)
 * @param defaultMessage - Default message to show if error is not recognized
 */
export const handleApiError = (
  error: unknown,
  defaultMessage: string = 'Произошла ошибка'
): void => {
  // Log error to console for debugging
  console.error('API Error:', error);

  let message = defaultMessage;

  // Handle ApiError type
  if (error && typeof error === 'object' && 'message' in error) {
    const apiError = error as ApiError;
    message = apiError.message || defaultMessage;

    // Show specific error toast
    if (apiError.status) {
      // Handle specific HTTP status codes
      switch (apiError.status) {
        case 400:
          toast.error(`Некорректный запрос: ${message}`);
          return;
        case 401:
          toast.error('Необходима авторизация');
          return;
        case 403:
          toast.error('Доступ запрещен');
          return;
        case 404:
          toast.error('Ресурс не найден');
          return;
        case 429:
          toast.error('Слишком много запросов. Попробуйте позже');
          return;
        case 500:
          toast.error('Ошибка сервера. Попробуйте позже');
          return;
        default:
          toast.error(message);
          return;
      }
    }

    toast.error(message);
    return;
  }

  // Handle standard Error objects
  if (error instanceof Error) {
    message = error.message || defaultMessage;
    toast.error(message);
    return;
  }

  // Handle string errors
  if (typeof error === 'string') {
    toast.error(error);
    return;
  }

  // Fallback to default message
  toast.error(defaultMessage);
};

/**
 * Checks if an error is an ApiError
 */
export const isApiError = (error: unknown): error is ApiError => {
  return (
    error !== null &&
    typeof error === 'object' &&
    'message' in error &&
    typeof (error as ApiError).message === 'string'
  );
};

/**
 * Extracts error message from unknown error type
 */
export const getErrorMessage = (error: unknown): string => {
  if (isApiError(error)) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return 'Произошла неизвестная ошибка';
};

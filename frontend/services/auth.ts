/**
 * Authentication service for Bot Factory API
 * Handles login, register, logout, and token management
 */
import { User, ApiError } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  name: string;
  password: string;
  password_confirm: string;
  plan?: 'Free' | 'Pro' | 'Enterprise';
}

export interface AuthResponse {
  user: User;
  tokens: {
    access: string;
    refresh: string;
  };
}

export interface Tokens {
  access: string;
  refresh: string;
}

/**
 * Get stored tokens from localStorage
 */
export const getTokens = (): Tokens | null => {
  try {
    const tokens = localStorage.getItem('bot_factory_tokens');
    return tokens ? JSON.parse(tokens) : null;
  } catch {
    return null;
  }
};

/**
 * Save tokens to localStorage
 */
export const saveTokens = (tokens: Tokens): void => {
  localStorage.setItem('bot_factory_tokens', JSON.stringify(tokens));
};

/**
 * Remove tokens from localStorage
 */
export const clearTokens = (): void => {
  localStorage.removeItem('bot_factory_tokens');
};

/**
 * Get access token for API requests
 */
export const getAccessToken = (): string | null => {
  const tokens = getTokens();
  return tokens?.access || null;
};

/**
 * API request wrapper with error handling
 */
const apiRequest = async <T>(
  url: string,
  options: RequestInit = {}
): Promise<T> => {
  const token = getAccessToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers,
    });

    const data = await response.json();

    if (!response.ok) {
      // Handle Django error format
      const error: ApiError = {
        message: data.error?.message || data.message || `HTTP ${response.status}: ${response.statusText}`,
        status: response.status,
        code: data.error?.code || data.code,
      };
      throw error;
    }

    return data;
  } catch (error) {
    if (error instanceof Error && 'status' in error) {
      throw error;
    }
    const apiError: ApiError = {
      message: error instanceof Error ? error.message : 'Network error',
      status: 0,
    };
    throw apiError;
  }
};

/**
 * Register a new user
 */
export const register = async (payload: RegisterPayload): Promise<AuthResponse> => {
  const response = await apiRequest<AuthResponse>('/auth/register/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  if (response.tokens) {
    saveTokens(response.tokens);
  }

  return response;
};

/**
 * Login user
 */
export const login = async (payload: LoginPayload): Promise<AuthResponse> => {
  const response = await apiRequest<AuthResponse>('/auth/login/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  if (response.tokens) {
    saveTokens(response.tokens);
  }

  return response;
};

/**
 * Logout user
 */
export const logout = async (): Promise<void> => {
  const tokens = getTokens();
  
  if (tokens?.refresh) {
    try {
      await apiRequest('/auth/logout/', {
        method: 'POST',
        body: JSON.stringify({ refresh: tokens.refresh }),
      });
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout API error:', error);
    }
  }

  clearTokens();
};

/**
 * Refresh access token
 */
export const refreshToken = async (): Promise<Tokens> => {
  const tokens = getTokens();
  
  if (!tokens?.refresh) {
    throw new Error('No refresh token available');
  }

  const response = await apiRequest<{ access: string }>('/auth/refresh/', {
    method: 'POST',
    body: JSON.stringify({ refresh: tokens.refresh }),
  });

  const newTokens = {
    access: response.access,
    refresh: tokens.refresh,
  };

  saveTokens(newTokens);
  return newTokens;
};

/**
 * Get current user
 */
export const getCurrentUser = async (): Promise<User> => {
  return apiRequest<User>('/auth/me/');
};

/**
 * Update current user
 */
export const updateCurrentUser = async (updates: Partial<User>): Promise<User> => {
  return apiRequest<User>('/auth/me/update/', {
    method: 'PATCH',
    body: JSON.stringify(updates),
  });
};


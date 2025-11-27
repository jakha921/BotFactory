import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '../types';
import * as authService from '../services/auth';
import { toast } from 'sonner';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, passwordConfirm: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (updates: Partial<User>) => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
  initialize: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          const response = await authService.login({ email, password });
          
          // Transform user data to match frontend User type
          const user: User = {
            id: response.user.id,
            name: response.user.name,
            email: response.user.email,
            plan: response.user.plan || 'Free',
            telegramId: response.user.telegram_id || '',
            avatar: response.user.avatar || '',
          };

          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          });

          toast.success('Successfully logged in!');
        } catch (error: any) {
          set({ isLoading: false });
          const message = error.message || 'Login failed. Please try again.';
          toast.error(message);
          throw error;
        }
      },

      register: async (name: string, email: string, password: string, passwordConfirm: string) => {
        set({ isLoading: true });
        try {
          const response = await authService.register({
            email,
            name,
            password,
            password_confirm: passwordConfirm,
            plan: 'Free',
          });

          // Transform user data to match frontend User type
          const user: User = {
            id: response.user.id,
            name: response.user.name,
            email: response.user.email,
            plan: response.user.plan || 'Free',
            telegramId: response.user.telegram_id || '',
            avatar: response.user.avatar || '',
          };

          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          });

          toast.success('Account created successfully!');
        } catch (error: any) {
          set({ isLoading: false });
          const message = error.message || 'Registration failed. Please try again.';
          toast.error(message);
          throw error;
        }
      },

      logout: async () => {
        try {
          await authService.logout();
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          set({
            user: null,
            isAuthenticated: false,
          });
          toast.success('Logged out successfully');
        }
      },

      updateUser: async (updates: Partial<User>) => {
        try {
          // Transform updates to backend format
          const backendUpdates: any = {};
          if (updates.name) backendUpdates.name = updates.name;
          if (updates.email) backendUpdates.email = updates.email;
          if (updates.avatar) backendUpdates.avatar = updates.avatar;
          if (updates.plan) backendUpdates.plan = updates.plan;
          if (updates.telegramId !== undefined) {
            // Convert string to number for backend
            backendUpdates.telegramId = updates.telegramId ? parseInt(updates.telegramId, 10) : null;
          }

          const updatedUser = await authService.updateCurrentUser(backendUpdates);

          // Transform response to frontend User type
          const user: User = {
            id: updatedUser.id,
            name: updatedUser.name,
            email: updatedUser.email,
            plan: updatedUser.plan || 'Free',
            telegramId: updatedUser.telegram_id || '',
            avatar: updatedUser.avatar || '',
          };

          set({ user });
          toast.success('Profile updated successfully');
        } catch (error: any) {
          const message = error.message || 'Failed to update profile';
          toast.error(message);
          throw error;
        }
      },

      fetchCurrentUser: async () => {
        try {
          const userData = await authService.getCurrentUser();
          
          // Transform user data to match frontend User type
          const user: User = {
            id: userData.id,
            name: userData.name,
            email: userData.email,
            plan: userData.plan || 'Free',
            telegramId: userData.telegram_id || '',
            avatar: userData.avatar || '',
          };

          set({
            user,
            isAuthenticated: true,
          });
        } catch (error) {
          // If fetch fails, user is not authenticated
          set({
            user: null,
            isAuthenticated: false,
          });
          authService.clearTokens();
          throw error;
        }
      },

      initialize: async () => {
        const tokens = authService.getTokens();
        
        if (tokens?.access) {
          try {
            await get().fetchCurrentUser();
          } catch (error) {
            // Token might be expired, try to refresh
            try {
              await authService.refreshToken();
              await get().fetchCurrentUser();
            } catch (refreshError) {
              // Refresh failed, clear tokens
              authService.clearTokens();
              set({
                user: null,
                isAuthenticated: false,
              });
            }
          }
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        // Only persist user, not tokens (tokens are stored separately)
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

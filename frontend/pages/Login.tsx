import React, { useState } from 'react';
import { Bot, Lock, Mail, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { useAuthStore } from '../store/useAuthStore';

interface LoginProps {
  onNavigate: (page: 'register' | 'forgot-password') => void;
}

export const Login: React.FC<LoginProps> = ({ onNavigate }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState('admin@botfactory.com');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const { login, isLoading: authLoading } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login(email, password);
      // Navigation will be handled by App.tsx based on isAuthenticated state
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const isLoadingState = isLoading || authLoading;

  return (
    <div className="min-h-screen w-full flex bg-white dark:bg-gray-900">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gray-900 relative overflow-hidden items-center justify-center">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-dark to-purple-900 opacity-90" />
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=1965&auto=format&fit=crop')] bg-cover bg-center mix-blend-overlay" />

        <div className="relative z-10 text-center p-12 max-w-xl">
          <div className="mb-8 inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 shadow-2xl">
            <Bot className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-white mb-6 tracking-tight">
            Build AI Agents <br /> in Minutes
          </h1>
          <p className="text-lg text-gray-300 leading-relaxed mb-8">
            Deploy intelligent bots to Telegram with our drag-and-drop builder. Integrated with
            Gemini 2.5 for lightning-fast responses and native audio support.
          </p>
          <div className="flex gap-4 justify-center">
            <div className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 backdrop-blur-sm text-gray-300 text-sm">
              🚀 No-code Builder
            </div>
            <div className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 backdrop-blur-sm text-gray-300 text-sm">
              ⚡️ Gemini Powered
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 lg:p-24">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center lg:text-left">
            <div className="lg:hidden flex justify-center mb-6">
              <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center">
                <Bot className="w-7 h-7 text-white" />
              </div>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">
              Welcome back
            </h2>
            <p className="mt-2 text-gray-500 dark:text-gray-400">
              Enter your credentials to access your bot factory.
            </p>
          </div>

          {error && (
            <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6 mt-8">
            <Input
              label="Email address"
              type="email"
              placeholder="name@company.com"
              required
              startIcon={<Mail className="w-5 h-5" />}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoadingState}
            />

            <div className="space-y-1">
              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                required
                startIcon={<Lock className="w-5 h-5" />}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoadingState}
              />
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => onNavigate('forgot-password')}
                  className="text-sm font-medium text-primary hover:text-primary-dark transition-colors"
                  disabled={isLoadingState}
                >
                  Forgot password?
                </button>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full"
              size="lg"
              isLoading={isLoadingState}
              icon={!isLoadingState && <ArrowRight className="w-4 h-4" />}
              disabled={isLoadingState}
            >
              {isLoadingState ? 'Signing in...' : 'Sign in'}
            </Button>
          </form>

          <div className="text-center mt-6">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => onNavigate('register')}
                className="font-semibold text-primary hover:text-primary-dark transition-colors"
                disabled={isLoadingState}
              >
                Create account
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

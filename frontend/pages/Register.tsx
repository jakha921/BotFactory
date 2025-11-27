import React, { useState } from 'react';
import { Bot, Mail, ArrowRight, User, Lock } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { useAuthStore } from '../store/useAuthStore';

interface RegisterProps {
  onNavigate: (page: 'login') => void;
}

export const Register: React.FC<RegisterProps> = ({ onNavigate }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const { register, isLoading: authLoading } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (password !== passwordConfirm) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setIsLoading(true);

    try {
      await register(name, email, password, passwordConfirm);
      // Navigation will be handled by App.tsx based on isAuthenticated state
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const isLoadingState = isLoading || authLoading;

  return (
    <div className="min-h-screen w-full flex bg-white dark:bg-gray-900">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gray-900 relative overflow-hidden items-center justify-center">
        <div className="absolute inset-0 bg-gradient-to-bl from-indigo-900 to-gray-900 opacity-90" />
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center mix-blend-overlay" />

        <div className="relative z-10 text-center p-12 max-w-xl">
          <div className="mb-8 inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 shadow-2xl">
            <Bot className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-white mb-6 tracking-tight">Join the Revolution</h1>
          <p className="text-lg text-gray-300 leading-relaxed mb-8">
            Create your account today and start building intelligent agents that transform how you
            interact with your customers.
          </p>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 lg:p-24">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center lg:text-left">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">
              Create an account
            </h2>
            <p className="mt-2 text-gray-500 dark:text-gray-400">
              Start your 14-day free trial. No credit card required.
            </p>
          </div>

          {error && (
            <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6 mt-8">
            <Input
              label="Full Name"
              placeholder="John Doe"
              required
              startIcon={<User className="w-5 h-5" />}
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isLoadingState}
            />

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

            <div className="space-y-4">
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
              <Input
                label="Confirm Password"
                type="password"
                placeholder="••••••••"
                required
                startIcon={<Lock className="w-5 h-5" />}
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                disabled={isLoadingState}
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              size="lg"
              isLoading={isLoadingState}
              icon={!isLoadingState && <ArrowRight className="w-4 h-4" />}
              disabled={isLoadingState}
            >
              {isLoadingState ? 'Creating account...' : 'Create Account'}
            </Button>
          </form>

          <div className="text-center mt-6">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => onNavigate('login')}
                className="font-semibold text-primary hover:text-primary-dark transition-colors"
                disabled={isLoadingState}
              >
                Sign in
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import { Mail, ArrowRight, ArrowLeft, KeyRound } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

interface ForgotPasswordProps {
  onNavigate: (page: 'login') => void;
}

export const ForgotPassword: React.FC<ForgotPasswordProps> = ({ onNavigate }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isSent, setIsSent] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      setIsSent(true);
    }, 1500);
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
      <div className="w-full max-w-md bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-black/5 dark:border-white/5 overflow-hidden">
        <div className="p-8">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-indigo-50 dark:bg-indigo-900/30 rounded-full flex items-center justify-center">
              <KeyRound className="w-8 h-8 text-primary" />
            </div>
          </div>

          <h2 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-2">
            {isSent ? 'Check your email' : 'Reset password'}
          </h2>

          <p className="text-center text-gray-500 dark:text-gray-400 mb-8 text-sm">
            {isSent
              ? 'We have sent a password reset link to your email address.'
              : "Enter the email address associated with your account and we'll send you a link to reset your password."}
          </p>

          {!isSent ? (
            <form onSubmit={handleSubmit} className="space-y-6">
              <Input
                label="Email address"
                type="email"
                placeholder="name@company.com"
                required
                startIcon={<Mail className="w-5 h-5" />}
              />

              <Button
                type="submit"
                className="w-full"
                size="lg"
                isLoading={isLoading}
                icon={!isLoading && <ArrowRight className="w-4 h-4" />}
              >
                {isLoading ? 'Sending link...' : 'Send Reset Link'}
              </Button>
            </form>
          ) : (
            <div className="space-y-4">
              <Button variant="secondary" className="w-full" onClick={() => setIsSent(false)}>
                Resend email
              </Button>
            </div>
          )}

          <div className="mt-8 text-center">
            <button
              onClick={() => onNavigate('login')}
              className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to log in
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import { Check, CreditCard, Zap, Bot, FileText, Crown, X, ShieldCheck } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Label } from '../components/ui/Label';
import { api } from '../services/api';
import { toast } from 'sonner';
import { cn } from '../utils';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '../store/useAuthStore';
import { UsageData } from '../types';

export const Subscription: React.FC = () => {
  console.log('[Subscription] Component rendered');
  const [usage, setUsage] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { updateUser, user } = useAuthStore();

  // Payment Modal State
  const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentStep, setPaymentStep] = useState<'form' | 'success'>('form');
  const [selectedPlan, setSelectedPlan] = useState<string>('');

  useEffect(() => {
    const loadUsage = async () => {
      setIsLoading(true);
      try {
        const data = await api.subscription.usage() as any;
        // Sync initial usage data with global user plan if available, otherwise default
        const effectivePlan = user?.plan && user.plan !== 'Free' ? user.plan : data.plan;
        setUsage({ ...data, plan: effectivePlan });
      } catch (error) {
        console.error('[Subscription] Failed to load usage:', error);
        toast.error('Failed to load subscription data. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };
    loadUsage();
  }, [user?.plan]);

  const handleUpgrade = (planName: string) => {
    setSelectedPlan(planName);
    setPaymentStep('form');
    setIsUpgradeModalOpen(true);
  };

  const handlePaymentSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsProcessing(true);

    // Simulate payment processing
    setTimeout(() => {
      setIsProcessing(false);
      setPaymentStep('success');

      // Update global user state
      updateUser({ plan: selectedPlan });

      // Update local state for immediate feedback
      setUsage((prev: any) => ({
        ...prev,
        plan: selectedPlan,
      }));
    }, 2000);
  };

  const plans = [
    {
      name: 'Free',
      price: '$0',
      period: '/mo',
      description: 'For hobbyists and testing.',
      features: ['1 Bot', '10 Documents', '100 API calls/mo', 'Community Support'],
      cta: 'Current Plan',
      current: usage?.plan === 'Free',
    },
    {
      name: 'Pro',
      price: '$29',
      period: '/mo',
      description: 'For creators and small teams.',
      features: [
        '5 Bots',
        '500 Documents',
        '10,000 API calls/mo',
        'Priority Support',
        'Gemini Pro Access',
      ],
      cta: 'Upgrade to Pro',
      highlight: true,
      current: usage?.plan === 'Pro',
    },
    {
      name: 'Enterprise',
      price: '$99',
      period: '/mo',
      description: 'For scaling businesses.',
      features: [
        'Unlimited Bots',
        '10,000 Documents',
        '100,000 API calls/mo',
        'Dedicated Manager',
        'SSO & Audit Logs',
      ],
      cta: 'Contact Sales',
      current: usage?.plan === 'Enterprise',
    },
  ];

  if (isLoading || !usage) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Subscription & Billing</h1>
        <p className="text-gray-500 dark:text-gray-400">Manage your plan and monitor usage.</p>
      </div>

      {/* Usage Stats - Fixed Dark Mode Colors */}
      <Card className="border-black/5 dark:border-white/5 bg-white dark:bg-gray-900">
        <CardContent className="p-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Current Usage</h2>
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                Resets on {new Date(usage.renewalDate).toLocaleDateString()}
              </p>
            </div>
            <Badge variant="success" className="px-3 py-1">
              {usage.plan} Plan Active
            </Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Bots Usage */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-300 flex items-center gap-2">
                  <Bot className="w-4 h-4" /> Active Bots
                </span>
                <span className="font-mono text-gray-900 dark:text-white">
                  {usage.bots.used} / {usage.bots.limit}
                </span>
              </div>
              <div className="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{
                    width: `${Math.min((usage.bots.used / usage.bots.limit) * 100, 100)}%`,
                  }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                  className="h-full bg-blue-500 rounded-full"
                />
              </div>
            </div>

            {/* Docs Usage */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-300 flex items-center gap-2">
                  <FileText className="w-4 h-4" /> Knowledge Base
                </span>
                <span className="font-mono text-gray-900 dark:text-white">
                  {usage.documents.used} / {usage.documents.limit} docs
                </span>
              </div>
              <div className="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{
                    width: `${Math.min((usage.documents.used / usage.documents.limit) * 100, 100)}%`,
                  }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                  className="h-full bg-purple-500 rounded-full"
                />
              </div>
            </div>

            {/* API Usage */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-300 flex items-center gap-2">
                  <Zap className="w-4 h-4" /> API Calls
                </span>
                <span className="font-mono text-gray-900 dark:text-white">
                  {usage.apiCalls.used.toLocaleString()} / {usage.apiCalls.limit.toLocaleString()}
                </span>
              </div>
              <div className="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{
                    width: `${Math.min((usage.apiCalls.used / usage.apiCalls.limit) * 100, 100)}%`,
                  }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                  className={cn(
                    'h-full rounded-full',
                    usage.apiCalls.used / usage.apiCalls.limit > 0.8
                      ? 'bg-amber-500'
                      : 'bg-emerald-500'
                  )}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <Card
            key={plan.name}
            className={cn(
              'relative flex flex-col transition-all duration-200',
              plan.highlight
                ? 'border-primary ring-1 ring-primary shadow-xl shadow-primary/10 z-10 md:-mt-4 md:-mb-4'
                : 'border-black/5 dark:border-white/5 bg-gray-50/50 dark:bg-white/5'
            )}
          >
            {plan.highlight && (
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-primary text-white px-3 py-1 rounded-full text-xs font-bold tracking-wide shadow-sm">
                MOST POPULAR
              </div>
            )}

            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                {plan.name}
                {plan.name === 'Enterprise' && <Crown className="w-5 h-5 text-amber-500" />}
              </CardTitle>
              <div className="mt-4 flex items-baseline text-gray-900 dark:text-white">
                <span className="text-4xl font-extrabold tracking-tight">{plan.price}</span>
                <span className="ml-1 text-xl font-semibold text-gray-500">{plan.period}</span>
              </div>
              <CardDescription className="mt-2">{plan.description}</CardDescription>
            </CardHeader>

            <CardContent className="flex-1 flex flex-col">
              <ul className="space-y-4 mb-8 flex-1">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start">
                    <div className="flex-shrink-0">
                      <Check className="h-5 w-5 text-emerald-500" />
                    </div>
                    <p className="ml-3 text-sm text-gray-700 dark:text-gray-300">{feature}</p>
                  </li>
                ))}
              </ul>

              <Button
                variant={plan.current ? 'secondary' : plan.highlight ? 'primary' : 'secondary'}
                className="w-full justify-center"
                disabled={plan.current}
                onClick={() => !plan.current && handleUpgrade(plan.name)}
              >
                {plan.current ? 'Current Plan' : plan.cta}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Billing History */}
      <div className="mt-12">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Billing History</h3>
        <Card className="overflow-hidden border-black/5 dark:border-white/5">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-50 dark:bg-white/5 text-gray-500 font-medium border-b border-black/5 dark:border-white/5">
                <tr>
                  <th className="px-6 py-3">Invoice</th>
                  <th className="px-6 py-3">Date</th>
                  <th className="px-6 py-3">Amount</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3 text-right">Download</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/5 dark:divide-white/5">
                <tr className="hover:bg-gray-50 dark:hover:bg-white/5">
                  <td className="px-6 py-4 font-medium text-gray-900 dark:text-white">
                    INV-2024-001
                  </td>
                  <td className="px-6 py-4 text-gray-500 dark:text-gray-400">Mar 01, 2025</td>
                  <td className="px-6 py-4 text-gray-900 dark:text-white">$29.00</td>
                  <td className="px-6 py-4">
                    <Badge variant="success">Paid</Badge>
                  </td>
                  <td className="px-6 py-4 text-right text-primary cursor-pointer hover:underline">
                    PDF
                  </td>
                </tr>
                <tr className="hover:bg-gray-50 dark:hover:bg-white/5">
                  <td className="px-6 py-4 font-medium text-gray-900 dark:text-white">
                    INV-2024-002
                  </td>
                  <td className="px-6 py-4 text-gray-500 dark:text-gray-400">Feb 01, 2025</td>
                  <td className="px-6 py-4 text-gray-900 dark:text-white">$29.00</td>
                  <td className="px-6 py-4">
                    <Badge variant="success">Paid</Badge>
                  </td>
                  <td className="px-6 py-4 text-right text-primary cursor-pointer hover:underline">
                    PDF
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Payment Modal */}
      <AnimatePresence>
        {isUpgradeModalOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-50"
              onClick={() => !isProcessing && setIsUpgradeModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-black/5 dark:border-white/5 z-50 overflow-hidden"
            >
              {paymentStep === 'form' ? (
                <form onSubmit={handlePaymentSubmit}>
                  <div className="p-6 border-b border-black/5 dark:border-white/5 flex justify-between items-center bg-gray-50/50 dark:bg-gray-900/50">
                    <div>
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                        Secure Checkout
                      </h3>
                      <p className="text-sm text-gray-500">Upgrading to {selectedPlan}</p>
                    </div>
                    <Button
                      type="button"
                      variant="icon"
                      size="md"
                      onClick={() => setIsUpgradeModalOpen(false)}
                    >
                      <X className="w-5 h-5" />
                    </Button>
                  </div>

                  <div className="p-6 space-y-5">
                    <div className="space-y-2">
                      <Label>Card Information</Label>
                      <div className="relative">
                        <CreditCard className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
                        <input
                          type="text"
                          className="w-full pl-10 pr-4 py-2 border border-black/10 dark:border-white/10 rounded-lg bg-white dark:bg-white/5 focus:ring-2 focus:ring-primary/20 outline-none text-sm text-gray-900 dark:text-white placeholder:text-gray-400"
                          placeholder="0000 0000 0000 0000"
                          required
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Expiry Date</Label>
                        <input
                          type="text"
                          className="w-full px-4 py-2 border border-black/10 dark:border-white/10 rounded-lg bg-white dark:bg-white/5 focus:ring-2 focus:ring-primary/20 outline-none text-sm text-gray-900 dark:text-white placeholder:text-gray-400"
                          placeholder="MM/YY"
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>CVC</Label>
                        <input
                          type="text"
                          className="w-full px-4 py-2 border border-black/10 dark:border-white/10 rounded-lg bg-white dark:bg-white/5 focus:ring-2 focus:ring-primary/20 outline-none text-sm text-gray-900 dark:text-white placeholder:text-gray-400"
                          placeholder="123"
                          required
                        />
                      </div>
                    </div>

                    <div className="bg-gray-50 dark:bg-white/5 p-3 rounded-lg text-xs text-gray-500 dark:text-gray-400 flex gap-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
                      Payments are secure and encrypted. You will be charged immediately.
                    </div>
                  </div>

                  <div className="p-6 border-t border-black/5 dark:border-white/5 flex justify-end gap-3">
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => setIsUpgradeModalOpen(false)}
                    >
                      Cancel
                    </Button>
                    <Button type="submit" isLoading={isProcessing}>
                      Pay & Upgrade
                    </Button>
                  </div>
                </form>
              ) : (
                <div className="p-8 flex flex-col items-center text-center">
                  <div className="w-16 h-16 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center text-emerald-600 dark:text-emerald-400 mb-4 animate-in zoom-in duration-300">
                    <Check className="w-8 h-8" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                    Upgrade Successful!
                  </h3>
                  <p className="text-gray-500 dark:text-gray-400 mb-6">
                    Welcome to the {selectedPlan} plan. Your new limits are active immediately.
                  </p>
                  <Button className="w-full" onClick={() => setIsUpgradeModalOpen(false)}>
                    Done
                  </Button>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

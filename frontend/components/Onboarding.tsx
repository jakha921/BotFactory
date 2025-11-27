import React, { useState } from 'react';
import { Bot, BarChart3, Sparkles, ArrowRight, Check } from 'lucide-react';
import { Button } from './ui/Button';
import { cn } from '../utils';

interface OnboardingProps {
  onComplete: () => void;
}

const STEPS = [
  {
    title: 'Welcome to Bot Factory',
    description:
      'Your all-in-one platform for building, managing, and analyzing AI chatbots powered by Gemini 2.5.',
    icon: Bot,
    color: 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400',
  },
  {
    title: 'Real-time Analytics',
    description:
      'Track user engagement, conversation quality, and token usage with our advanced dashboard.',
    icon: BarChart3,
    color: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400',
  },
  {
    title: 'Gemini Powered',
    description:
      "Leverage Google's latest multimodal models to create human-like experiences for your users.",
    icon: Sparkles,
    color: 'bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400',
  },
];

export const Onboarding: React.FC<OnboardingProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);

  const handleNext = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      onComplete();
    }
  };

  const CurrentIcon = STEPS[currentStep].icon;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-gray-900/60 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-md p-8 mx-4 relative overflow-hidden border border-gray-200 dark:border-gray-800">
        {/* Background Decorative Elements */}
        <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-primary to-purple-500" />

        {/* Content */}
        <div className="flex flex-col items-center text-center space-y-6 mt-4">
          <div
            className={cn(
              'w-20 h-20 rounded-2xl flex items-center justify-center transition-all duration-500 shadow-sm',
              STEPS[currentStep].color
            )}
          >
            <CurrentIcon className="w-10 h-10 transition-all duration-300" />
          </div>

          <div className="space-y-2 min-h-[120px]">
            <h2
              key={currentStep}
              className="text-2xl font-bold text-gray-900 dark:text-white animate-in slide-in-from-bottom-2 duration-500"
            >
              {STEPS[currentStep].title}
            </h2>
            <p
              key={currentStep + '-desc'}
              className="text-gray-500 dark:text-gray-400 animate-in slide-in-from-bottom-3 duration-500 delay-100 leading-relaxed"
            >
              {STEPS[currentStep].description}
            </p>
          </div>
        </div>

        {/* Navigation & Actions */}
        <div className="mt-8 space-y-6">
          {/* Step Indicators */}
          <div className="flex justify-center gap-2">
            {STEPS.map((_, idx) => (
              <div
                key={idx}
                className={cn(
                  'w-2 h-2 rounded-full transition-all duration-300',
                  idx === currentStep ? 'w-8 bg-primary' : 'bg-gray-200 dark:bg-gray-700'
                )}
              />
            ))}
          </div>

          <div className="flex gap-3">
            <Button
              variant="ghost"
              className="flex-1 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
              onClick={onComplete}
            >
              Skip
            </Button>
            <Button
              className="flex-[2]"
              onClick={handleNext}
              icon={
                currentStep === STEPS.length - 1 ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <ArrowRight className="w-4 h-4" />
                )
              }
            >
              {currentStep === STEPS.length - 1 ? 'Get Started' : 'Next'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

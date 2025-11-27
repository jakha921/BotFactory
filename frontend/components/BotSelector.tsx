import React from 'react';
import { Check, ChevronsUpDown, Bot } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '../store/useAppStore';
import { cn } from '../utils';

interface BotSelectorProps {
  onCreateNew: () => void;
}

export const BotSelector: React.FC<BotSelectorProps> = ({ onCreateNew }) => {
  const { bots, selectedBotId, setSelectedBotId } = useAppStore();
  const [isOpen, setIsOpen] = React.useState(false);

  // Ensure bots is always an array
  const botsArray = Array.isArray(bots) ? bots : [];
  const selectedBot = botsArray.find((b) => b.id === selectedBotId);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center justify-between transition-all duration-200',
          'w-10 px-0 justify-center sm:w-48 sm:px-3 sm:justify-between h-9', // Mobile: square icon button, Desktop: wide
          'text-sm rounded-lg',
          'bg-white dark:bg-gray-800 border border-black/5 dark:border-white/10',
          'hover:border-black/10 dark:hover:border-white/20 hover:shadow-sm',
          'focus:outline-none focus:ring-2 focus:ring-primary/20'
        )}
      >
        <div className="flex items-center gap-2 truncate">
          <div className="w-5 h-5 rounded bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center flex-shrink-0">
            <Bot className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
          </div>
          <span
            className={cn('truncate font-medium hidden sm:block', !selectedBot && 'text-gray-400')}
          >
            {selectedBot ? selectedBot.name : 'Select Bot'}
          </span>
        </div>
        <ChevronsUpDown className="w-4 h-4 text-gray-400 ml-2 shrink-0 hidden sm:block" />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <div className="fixed inset-0 z-30" onClick={() => setIsOpen(false)} />
            <motion.div
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 4 }}
              className="absolute top-full right-0 sm:left-auto sm:right-0 w-64 mt-1 z-40 bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl rounded-xl border border-black/5 dark:border-white/10 shadow-xl py-1 max-h-80 overflow-y-auto custom-scrollbar"
            >
              <div className="px-2 py-1.5 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Available Bots
              </div>

              {botsArray.length === 0 && (
                <div className="px-3 py-2 text-sm text-gray-500">No bots found.</div>
              )}

              {botsArray.map((bot) => (
                <button
                  key={bot.id}
                  onClick={() => {
                    setSelectedBotId(bot.id);
                    setIsOpen(false);
                  }}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2 text-sm transition-colors hover:bg-gray-50 dark:hover:bg-white/5',
                    selectedBotId === bot.id
                      ? 'bg-indigo-50/50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400'
                      : 'text-gray-700 dark:text-gray-200'
                  )}
                >
                  <div className="w-8 h-8 rounded-lg bg-gray-100 dark:bg-gray-700/50 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="flex-1 text-left truncate">
                    <div className="font-medium truncate">{bot.name}</div>
                    <div className="text-xs text-gray-400 truncate">{bot.model}</div>
                  </div>
                  {selectedBotId === bot.id && (
                    <Check className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                  )}
                </button>
              ))}

              <div className="border-t border-black/5 dark:border-white/5 mt-1 pt-1 px-2 pb-1">
                <button
                  onClick={() => {
                    setSelectedBotId('new'); // Set context to new
                    setIsOpen(false);
                    onCreateNew(); // Trigger navigation
                  }}
                  className="w-full text-left px-2 py-1.5 text-xs font-medium text-gray-500 hover:text-primary transition-colors rounded-md hover:bg-gray-50 dark:hover:bg-white/5"
                >
                  + Create New Bot
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

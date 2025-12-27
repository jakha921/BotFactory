import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Bot } from '../types';

interface AppState {
  bots: Bot[];
  selectedBotId: string | null;
  monitoringUserId: string | null; // For navigation from Users to Monitoring
  testTelegramUserId: string; // Added for Developer Settings

  setBots: (bots: Bot[]) => void;
  setSelectedBotId: (id: string | null) => void;
  setMonitoringUserId: (id: string | null) => void;
  setTestTelegramUserId: (id: string) => void;
  getSelectedBot: () => Bot | undefined;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      bots: [],
      selectedBotId: null,
      monitoringUserId: null,
      testTelegramUserId: '',

      setBots: (bots) => {
        // Ensure bots is always an array
        const botsArray = Array.isArray(bots) ? bots : [];
        set({ bots: botsArray });
      },

      setSelectedBotId: (id) => set({ selectedBotId: id }),

      setMonitoringUserId: (id) => set({ monitoringUserId: id }),

      setTestTelegramUserId: (id) => set({ testTelegramUserId: id }),

      getSelectedBot: () => {
        const { bots, selectedBotId } = get();
        if (!Array.isArray(bots)) return undefined;
        return bots.find((b) => b.id === selectedBotId);
      },
    }),
    {
      name: 'bot-factory-storage',
      partialize: (state) => ({
        selectedBotId: state.selectedBotId,
        testTelegramUserId: state.testTelegramUserId,
      }),
    }
  )
);

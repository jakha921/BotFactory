import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Bot, ApiKey } from '../types';

interface AppState {
  bots: Bot[];
  apiKeys: ApiKey[];
  selectedBotId: string | null;
  monitoringUserId: string | null; // For navigation from Users to Monitoring
  testTelegramUserId: string; // Added for Developer Settings

  setBots: (bots: Bot[]) => void;
  setSelectedBotId: (id: string | null) => void;
  setMonitoringUserId: (id: string | null) => void;
  setTestTelegramUserId: (id: string) => void;
  getSelectedBot: () => Bot | undefined;
  addApiKey: (key: ApiKey) => void;
  deleteApiKey: (id: string) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      bots: [],
      apiKeys: [],
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

      addApiKey: (key) =>
        set((state) => ({
          apiKeys: [...state.apiKeys, key],
        })),

      deleteApiKey: (id) =>
        set((state) => ({
          apiKeys: state.apiKeys.filter((k) => k.id !== id),
        })),
    }),
    {
      name: 'bot-factory-storage',
      partialize: (state) => ({
        apiKeys: state.apiKeys,
        selectedBotId: state.selectedBotId,
        testTelegramUserId: state.testTelegramUserId,
      }),
    }
  )
);

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ChatMessage } from '../types';

interface ChatState {
  messages: ChatMessage[];
  addMessage: (msg: ChatMessage) => void;
  setMessages: (msgs: ChatMessage[]) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      messages: [
        {
          id: '1',
          role: 'model',
          content: 'Hello! I am your AI assistant. How can I help you today?',
          timestamp: new Date(),
        },
      ],
      addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
      setMessages: (msgs) => set({ messages: msgs }),
      clearMessages: () => set({ messages: [] }),
    }),
    {
      name: 'bot-chat-storage',
      // Custom serialization needed because Date objects become strings in JSON
      onRehydrateStorage: () => (state) => {
        if (state && state.messages) {
          state.messages = state.messages.map((msg: ChatMessage | unknown) => {
            // Type guard to check if msg is a valid ChatMessage
            if (msg && typeof msg === 'object' && 'timestamp' in msg) {
              const chatMsg = msg as ChatMessage;
              // Check if timestamp is already a Date object
              if (chatMsg.timestamp instanceof Date) {
                return chatMsg;
              }
              // Try to parse timestamp string or number
              const timestamp =
                typeof chatMsg.timestamp === 'string' || typeof chatMsg.timestamp === 'number'
                  ? new Date(chatMsg.timestamp)
                  : new Date();
              // Validate that date is valid
              if (isNaN(timestamp.getTime())) {
                return { ...chatMsg, timestamp: new Date() };
              }
              return { ...chatMsg, timestamp };
            }
            // Fallback for invalid messages
            return {
              id: 'unknown',
              role: 'model' as const,
              content: '',
              timestamp: new Date(),
            } as ChatMessage;
          });
        }
      },
    }
  )
);

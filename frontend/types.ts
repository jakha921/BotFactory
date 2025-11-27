export enum BotStatus {
  ACTIVE = 'active',
  PAUSED = 'paused',
  ERROR = 'error',
  DRAFT = 'draft',
}

export interface InlineKeyboardButton {
  text: string;
  callback_data?: string;
  url?: string;
  web_app?: any;
  switch_inline_query?: string;
  switch_inline_query_current_chat?: string;
  pay?: boolean;
}

export interface InlineKeyboardRow {
  buttons: InlineKeyboardButton[];
}

export interface InlineKeyboardConfig {
  [keyboardName: string]: InlineKeyboardButton[][]; // Array of rows, each row is an array of buttons
}

export interface FormStep {
  field: string;
  type: 'text' | 'number' | 'choice' | 'file' | 'textarea' | 'email' | 'phone';
  prompt: string;
  required?: boolean;
  options?: string[]; // For choice type
  validation?: {
    min_length?: number;
    max_length?: number;
    min_value?: number;
    max_value?: number;
  };
}

export interface FormConfig {
  name: string;
  steps: FormStep[];
  submit_handler?: string;
}

export interface FormsConfig {
  [formName: string]: FormConfig;
}

export interface UIConfig {
  inline_keyboards?: InlineKeyboardConfig;
  forms?: FormsConfig;
  welcome_message?: string;
  help_message?: string;
  default_inline_keyboard?: InlineKeyboardButton[][];
}

export interface Bot {
  id: string;
  name: string;
  description: string;
  status: BotStatus;
  conversationsCount: number;
  documentsCount: number;
  model: string;
  provider: 'gemini' | 'openai' | 'anthropic';
  temperature: number;
  systemInstruction: string;
  thinkingBudget?: number; // Added for Gemini 3.0 / 2.5 thinking models
  telegramToken?: string;
  avatar?: string; // Emoji or URL
  createdAt: string;
  uiConfig?: UIConfig; // UI configuration for Telegram bot
  defaultInlineKeyboard?: InlineKeyboardButton[][];
  welcomeMessage?: string;
  helpMessage?: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  plan?: string; // Added plan property
  telegramId?: string; // Added telegramId property
}

export interface TelegramUser {
  id: string;
  telegramId: string;
  username?: string;
  firstName: string;
  lastName?: string;
  avatarUrl?: string;
  firstSeen: string;
  lastActive: string;
  messageCount: number;
  botId: string;
  notes?: string;
  status: 'active' | 'blocked'; // Added status
}

import { LucideIcon } from 'lucide-react';

export interface KPI {
  title: string;
  value: string | number;
  trend: number;
  trendDirection: 'up' | 'down' | 'neutral';
  icon: LucideIcon;
  color: 'indigo' | 'green' | 'amber' | 'blue';
}

// API Types
export interface ApiError {
  message: string;
  status?: number;
  code?: string;
}

export interface ApiResponse<T> {
  data: T;
  error?: ApiError;
}

export type UserStatus = 'active' | 'blocked';

export interface UpdateUserStatusPayload {
  status: UserStatus;
}

export interface SaveSnippetPayload {
  id?: string;
  title: string;
  content: string;
  tags: string[];
  botId: string;
}

export interface ChatAttachment {
  id: string;
  type: 'image' | 'file' | 'audio';
  url: string;
  name: string;
  size?: string;
  file?: File; // Store File object for processing on backend
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'model';
  content: string;
  timestamp: Date;
  isThinking?: boolean;
  isFlagged?: boolean;
  attachments?: ChatAttachment[]; // Added attachments
}

export interface ChatSession {
  id: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  lastMessage: string;
  timestamp: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  isFlagged: boolean;
  botId: string;
  unreadCount?: number;
}

export interface Document {
  id: string;
  name: string;
  type: 'pdf' | 'txt' | 'docx' | 'md';
  size: string;
  status: 'indexing' | 'ready' | 'error';
  uploadDate: string;
  botId: string; // Link to specific bot
}

export interface TextSnippet {
  id: string;
  title: string;
  content: string;
  tags: string[];
  botId: string;
  updatedAt: string;
}

export interface Notification {
  id: string;
  title: string;
  description: string;
  time: string;
  read: boolean;
  type: 'info' | 'warning' | 'success';
}

export interface ApiKey {
  id: string;
  name: string;
  key: string;
  provider: 'openai' | 'gemini' | 'anthropic';
  created: string;
}

export type View =
  | 'login'
  | 'dashboard'
  | 'bots'
  | 'bot-chat'
  | 'settings'
  | 'bot-settings'
  | 'knowledge'
  | 'users'
  | 'subscription'
  | 'monitoring';

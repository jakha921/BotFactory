import { LucideIcon } from 'lucide-react';
import {
  Bot,
  KPI,
  TelegramUser,
  Document,
  TextSnippet,
  ChatSession,
  ChatMessage,
  UpdateUserStatusPayload,
  SaveSnippetPayload,
  ApiError,
  UIConfig,
  InlineKeyboardButton,
} from '../types';
import { getAccessToken } from './auth';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Helper function to construct full API URL
const getApiUrl = (path: string): string => {
  // Remove leading slash if present to avoid double slashes
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  return `${API_BASE_URL}/${cleanPath}`;
};


/**
 * Parse Django error response format
 */
const parseError = async (response: Response): Promise<ApiError> => {
  try {
    const data = await response.json();

    // Django error format: { error: { message, code, status, details } }
    if (data.error) {
      return {
        message: data.error.message || `HTTP ${response.status}: ${response.statusText}`,
        status: data.error.status || response.status,
        code: data.error.code,
      };
    }

    // DRF validation error format
    if (response.status === 400 && typeof data === 'object') {
      const messages: string[] = [];
      for (const [key, value] of Object.entries(data)) {
        if (Array.isArray(value)) {
          messages.push(...value.map((v) => `${key}: ${v}`));
        } else if (typeof value === 'string') {
          messages.push(`${key}: ${value}`);
        }
      }
      return {
        message: messages.length > 0 ? messages.join(', ') : 'Validation error',
        status: response.status,
        code: 'validation_error',
      };
    }

    return {
      message: data.message || data.detail || `HTTP ${response.status}: ${response.statusText}`,
      status: response.status,
      code: data.code,
    };
  } catch {
    return {
      message: `HTTP ${response.status}: ${response.statusText}`,
      status: response.status,
    };
  }
};

// API client with JWT authentication
const client = {
  get: async <T = unknown>(url: string): Promise<T> => {
    try {
      const token = getAccessToken();
      const headers: HeadersInit = {};

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch(getApiUrl(url), {
        method: 'GET',
        headers,
      });

      if (!res.ok) {
        const error = await parseError(res);
        throw error;
      }

      return await res.json();
    } catch (e) {
      if (e && typeof e === 'object' && 'status' in e) {
        throw e;
      }
      const error: ApiError = {
        message: e instanceof Error ? e.message : 'Network error',
        status: 0,
      };
      throw error;
    }
  },

  post: async <T = unknown, B = unknown>(
    url: string,
    body: B,
    isFormData = false
  ): Promise<T> => {
    try {
      const token = getAccessToken();
      const headers: HeadersInit = {};

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      if (!isFormData) {
        headers['Content-Type'] = 'application/json';
      }

      const res = await fetch(getApiUrl(url), {
        method: 'POST',
        headers,
        body: isFormData ? (body as unknown as FormData) : JSON.stringify(body),
      });

      if (!res.ok) {
        const error = await parseError(res);
        throw error;
      }

      return await res.json();
    } catch (e) {
      if (e && typeof e === 'object' && 'status' in e) {
        throw e;
      }
      const error: ApiError = {
        message: e instanceof Error ? e.message : 'Network error',
        status: 0,
      };
      throw error;
    }
  },

  patch: async <T = unknown, B = unknown>(url: string, body: B): Promise<T> => {
    try {
      const token = getAccessToken();
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch(getApiUrl(url), {
        method: 'PATCH',
        headers,
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const error = await parseError(res);
        throw error;
      }

      return await res.json();
    } catch (e) {
      if (e && typeof e === 'object' && 'status' in e) {
        throw e;
      }
      const error: ApiError = {
        message: e instanceof Error ? e.message : 'Network error',
        status: 0,
      };
      throw error;
    }
  },

  delete: async <T = unknown>(url: string): Promise<T> => {
    try {
      const token = getAccessToken();
      const headers: HeadersInit = {};

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch(getApiUrl(url), {
        method: 'DELETE',
        headers,
      });

      if (!res.ok) {
        const error = await parseError(res);
        throw error;
      }

      // DELETE might return empty response
      if (res.status === 204 || res.headers.get('content-length') === '0') {
        return {} as T;
      }

      return await res.json();
    } catch (e) {
      if (e && typeof e === 'object' && 'status' in e) {
        throw e;
      }
      const error: ApiError = {
        message: e instanceof Error ? e.message : 'Network error',
        status: 0,
      };
      throw error;
    }
  },
};

// Helper function to handle paginated responses
const getPaginatedResults = <T>(response: { results: T[] } | T[]): Promise<T[]> => {
  if (Array.isArray(response)) {
    return Promise.resolve(response);
  }
  if (response && Array.isArray(response.results)) {
    return Promise.resolve(response.results);
  }
  return Promise.resolve([]);
};

// Partial Bot for create/update operations
export type BotCreateInput = Omit<
  Bot,
  'id' | 'createdAt' | 'conversationsCount' | 'documentsCount'
> & {
  id?: string;
};

export const api = {
  bots: {
    list: async (): Promise<Bot[]> => {
      const response = await client.get<any>('bots/');
      // Handle paginated response: {count, results, next, previous}
      // Or direct array response
      if (Array.isArray(response)) {
        return response;
      }
      if (response && Array.isArray(response.results)) {
        return response.results;
      }
      // Fallback: return empty array
      return [];
    },

    get: async (id: string): Promise<Bot> => {
      return client.get<Bot>(`bots/${id}/`);
    },

    save: (bot: BotCreateInput): Promise<Bot> => {
      const isUpdate = !!bot.id;
      const url = isUpdate ? `bots/${bot.id}/` : 'bots/';
      const method = isUpdate ? client.patch : client.post;

      // Remove id for both create and update (id comes from URL for update)
      const { id, ...botData } = bot;
      // Clean up undefined values
      const payload = Object.fromEntries(
        Object.entries(botData).filter(([_, v]) => v !== undefined)
      );

      return method<Bot, typeof payload>(url, payload);
    },

    delete: (id: string): Promise<void> =>
      client.delete<void>(`bots/${id}/`).then(() => undefined),

    getUIConfig: async (id: string): Promise<UIConfig> => {
      return client.get<UIConfig>(`bots/${id}/ui-config/`);
    },

    updateUIConfig: (id: string, config: Partial<UIConfig>): Promise<UIConfig> => {
      return client.post<UIConfig, Partial<UIConfig>>(`bots/${id}/ui-config/`, config);
    },

    getKeyboard: async (id: string, keyboardName: string): Promise<{ keyboard_name: string; config: InlineKeyboardButton[][] }> => {
      return client.get<{ keyboard_name: string; config: InlineKeyboardButton[][] }>(`bots/${id}/keyboards/${keyboardName}/`);
    },

    testTelegramConnection: async (id: string): Promise<{
      success: boolean;
      bot_info: {
        id: number;
        username: string;
        first_name: string;
        is_bot: boolean;
        can_join_groups?: boolean;
        can_read_all_group_messages?: boolean;
        supports_inline_queries?: boolean;
      } | null;
      error: string | null;
      notification_sent?: boolean;
      notification_error?: string | null;
      has_telegram_id?: boolean;
      telegram_id?: string | null;
    }> => {
      return client.get<{
        success: boolean;
        bot_info: any;
        error: string | null;
        notification_sent?: boolean;
        notification_error?: string | null;
        has_telegram_id?: boolean;
      }>(`bots/${id}/test-telegram-connection/`);
    },

    getBotStatus: async (id: string): Promise<{
      is_running: boolean;
      last_heartbeat: string | null;
      error: string | null;
    }> => {
      return client.get<{
        is_running: boolean;
        last_heartbeat: string | null;
        error: string | null;
      }>(`bots/${id}/bot-status/`);
    },

    restartBot: async (id: string): Promise<{
      success: boolean;
      message: string;
    }> => {
      return client.post<{
        success: boolean;
        message: string;
      }>(`bots/${id}/restart-bot/`, {});
    },

    getAPIKeys: async (id: string): Promise<Array<{
      id: string;
      name: string;
      key_prefix: string;
      is_active: boolean;
      last_used_at: string | null;
      created_at: string;
      expires_at: string | null;
    }>> => {
      return client.get<Array<{
        id: string;
        name: string;
        key_prefix_display: string;
        is_active: boolean;
        last_used_at: string | null;
        created_at: string;
        expires_at: string | null;
      }>>(`bots/${id}/api-keys/`);
    },

    createAPIKey: async (id: string, name: string, expiresAt?: string): Promise<{
      id: string;
      name: string;
      key: string;
      key_prefix: string;
      created_at: string;
      expires_at: string | null;
      warning: string;
    }> => {
      return client.post<{
        id: string;
        name: string;
        key: string;
        key_prefix: string;
        created_at: string;
        expires_at: string | null;
        warning: string;
      }>(`bots/${id}/api-keys/`, {
        name,
        expires_at: expiresAt || null,
      });
    },

    deleteAPIKey: async (botId: string, apiKeyId: string): Promise<void> => {
      return client.delete<void>(`bots/${botId}/api-keys/${apiKeyId}/`).then(() => undefined);
    },
  },

  stats: {
    dashboard: async (period: string): Promise<KPI[]> => {
      const data = await client.get<any[]>(`stats/?period=${encodeURIComponent(period)}`);
      // Import icon mapper here to avoid circular dependencies
      const { mapKPIData } = await import('../utils/iconMapper');
      return data.map(mapKPIData);
    },

    chart: (period: string): Promise<Array<{ name: string; value: number }>> =>
      client.get<Array<{ name: string; value: number }>>(
        `stats/chart/?period=${encodeURIComponent(period)}`
      ),

    activity: (): Promise<
      Array<{
        id: number | string;
        title: string;
        description: string;
        time: string;
        user: string;
        icon: LucideIcon;
        status: 'success' | 'warning' | 'info' | string;
      }>
    > =>
      client.get<
        Array<{
          id: number | string;
          title: string;
          description: string;
          time: string;
          user: string;
          icon: LucideIcon;
          status: 'success' | 'warning' | 'info' | string;
        }>
      >('stats/activity/'),
  },

  users: {
    list: (botId: string): Promise<TelegramUser[]> =>
      client.get<TelegramUser[]>(`bots/${botId}/users/`),

    updateStatus: async (userId: string, status: UpdateUserStatusPayload): Promise<void> => {
      await client.post<void, UpdateUserStatusPayload>(`users/${userId}/status/`, status);
    },
  },

  knowledge: {
    documents: (botId: string): Promise<Document[]> =>
      client.get<Document[]>(`bots/${botId}/documents/`),

    upload: async (file: File, botId: string): Promise<Document> => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', file.name);

      return client.post<Document, FormData>(`bots/${botId}/documents/`, formData, true);
    },

    deleteDocument: (id: string): Promise<void> =>
      client.delete<void>(`documents/${id}/`).then(() => undefined),

    snippets: async (botId: string): Promise<TextSnippet[]> => {
      // Backend expects bot_id as query parameter
      const response = await client.get<{ results: TextSnippet[] } | TextSnippet[]>(`snippets/?bot_id=${botId}`);
      return getPaginatedResults(response);
    },

    saveSnippet: (snippet: SaveSnippetPayload): Promise<TextSnippet> => {
      const isUpdate = !!snippet.id;
      const url = isUpdate ? `snippets/${snippet.id}/` : 'snippets/';
      const method = isUpdate ? client.patch : client.post;

      // Extract id and botId separately
      const { id, botId, ...restData } = snippet;

      // Build payload: convert botId to bot (UUID) for backend
      const payload: any = {
        ...restData,
        // Convert botId to bot for backend (it expects bot UUID field)
        bot: botId,
      };

      // Remove id from payload (it's in URL for updates)
      // Clean up undefined values
      const cleanPayload = Object.fromEntries(
        Object.entries(payload).filter(([_, v]) => v !== undefined)
      );

      return method<TextSnippet, typeof cleanPayload>(url, cleanPayload);
    },

    deleteSnippet: (id: string): Promise<void> =>
      client.delete<void>(`snippets/${id}/`).then(() => undefined),
  },

  chat: {
    sessions: (botId: string): Promise<ChatSession[]> =>
      client.get<ChatSession[]>(`bots/${botId}/sessions/`),

    messages: (sessionId: string): Promise<ChatMessage[]> =>
      client.get<ChatMessage[]>(`sessions/${sessionId}/messages/`),

    transcribeAudio: async (audioFile: File, languageCode?: string): Promise<{ text: string; confidence: number; language_code: string }> => {
      const formData = new FormData();
      formData.append('audio_file', audioFile);
      if (languageCode) {
        formData.append('language_code', languageCode);
      }

      // Detect audio format from file extension
      const fileName = audioFile.name.toLowerCase();
      let audioFormat: string | undefined;
      if (fileName.endsWith('.wav')) audioFormat = 'wav';
      else if (fileName.endsWith('.mp3')) audioFormat = 'mp3';
      else if (fileName.endsWith('.flac')) audioFormat = 'flac';
      else if (fileName.endsWith('.webm')) audioFormat = 'webm';
      else if (fileName.endsWith('.ogg')) audioFormat = 'ogg';

      if (audioFormat) {
        formData.append('audio_format', audioFormat);
      }

      return client.post<{ text: string; confidence: number; language_code: string }, FormData>('chat/transcribe/', formData, true);
    },

    processFile: async (file: File, ocrLanguages?: string[]): Promise<{ text: string; pages: number; file_type: string; file_name: string }> => {
      const formData = new FormData();
      formData.append('file', file);
      if (ocrLanguages && ocrLanguages.length > 0) {
        formData.append('ocr_languages', ocrLanguages.join(','));
      }

      return client.post<{ text: string; pages: number; file_type: string; file_name: string }, FormData>('chat/process-file/', formData, true);
    },

    generateResponse: async (
      botId: string,
      prompt: string,
      systemInstruction: string,
      history: { role: 'user' | 'model'; content: string }[],
      thinkingBudget?: number,
      temperature?: number
    ): Promise<{ text: string; groundingChunks?: any[] }> => {
      const payload = {
        bot_id: botId,
        prompt,
        system_instruction: systemInstruction,
        history,
        ...(thinkingBudget !== undefined && { thinking_budget: thinkingBudget }),
        ...(temperature !== undefined && { temperature }),
      };

      return client.post<{ text: string; groundingChunks?: any[] }, typeof payload>('chat/generate/', payload);
    },
  },

  ai: {
    improveInstruction: async (instruction: string, botId?: string): Promise<{
      text: string;
      usage?: { input_tokens: number; output_tokens: number };
      limit_reached?: boolean;
      message?: string;
      error?: string;
    }> => {
      return client.post('ai/improve-instruction/', { instruction, bot_id: botId });
    },

    generateContent: async (title: string, botId?: string): Promise<{
      text: string;
      usage?: { input_tokens: number; output_tokens: number };
      limit_reached?: boolean;
      message?: string;
      error?: string;
    }> => {
      return client.post('ai/generate-content/', { title, bot_id: botId });
    },

    getUsageLimits: async (): Promise<{
      limits: Array<{
        feature: string;
        name: string;
        can_use: boolean;
        message: string;
        max_uses?: number;
        period?: string;
        is_unlimited?: boolean;
      }>;
      plan: string;
    }> => {
      return client.get('ai/usage-limits/');
    },

    getModels: async (): Promise<{
      models: Array<{
        id: string;
        provider: string;
        provider_display: string;
        name: string;
        display_name: string;
        model_id: string;
        capability: string;
        supports_thinking: boolean;
        supports_vision: boolean;
        is_default: boolean;
      }>;
    }> => {
      return client.get('ai/models/');
    },
  },

  userApiKeys: {
    list: (): Promise<Array<{
      id: string;
      name: string;
      provider: string;
      key: string;
      created: string;
    }>> => client.get<Array<{
      id: string;
      name: string;
      provider: string;
      key: string;
      created: string;
    }>>('auth/api-keys/'),

    create: (name: string, provider: string, key: string): Promise<{
      id: string;
      name: string;
      provider: string;
      key: string;
      created: string;
    }> => client.post<{
      id: string;
      name: string;
      provider: string;
      key: string;
      created: string;
    }>('auth/api-keys/', { name, provider, key }),

    delete: (id: string): Promise<void> =>
      client.delete<void>(`auth/api-keys/${id}/`).then(() => undefined),
  },

  subscription: {
    usage: (): Promise<unknown> =>
      client.get<unknown>('subscription/'),
  },
};

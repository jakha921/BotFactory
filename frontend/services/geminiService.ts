import { GoogleGenAI, Type } from '@google/genai';

// Get API key from Vite environment variables
// Supports both import.meta.env (Vite client) and process.env (Vite config fallback)
const apiKey =
  import.meta.env.VITE_GEMINI_API_KEY ||
  (typeof process !== 'undefined' ? process.env.GEMINI_API_KEY : '') ||
  '';

export const createGeminiClient = () => {
  if (!apiKey) {
    console.error('Gemini API Key is missing');
  }
  return new GoogleGenAI({ apiKey });
};

// Gemini API Configuration Types
interface GeminiConfig {
  systemInstruction: string;
  tools: Array<{ googleSearch?: Record<string, never> }>;
  thinkingConfig?: { thinkingBudget: number };
  maxOutputTokens?: undefined;
}

interface GeminiResponse {
  text: string;
  groundingChunks?: Array<{
    web?: {
      title?: string;
      uri?: string;
    };
  }>;
}

export const generateBotResponse = async (
  modelName: string,
  prompt: string,
  systemInstruction: string = 'You are a helpful AI assistant.',
  history: { role: 'user' | 'model'; content: string }[] = [],
  thinkingBudget?: number
): Promise<GeminiResponse> => {
  try {
    const ai = createGeminiClient();

    // Ensure systemInstruction is not empty
    const finalSystemInstruction = systemInstruction?.trim() || 'You are a helpful AI assistant.';
    
    console.log('[GeminiService] Generating response:', {
      model: modelName,
      systemInstructionLength: finalSystemInstruction.length,
      systemInstructionPreview: finalSystemInstruction.substring(0, 200) + '...',
      promptLength: prompt.length,
      historyLength: history.length,
      thinkingBudget,
    });

    const config: GeminiConfig = {
      systemInstruction: finalSystemInstruction,
      tools: [{ googleSearch: {} }],
    };

    // Apply thinking config if budget is provided
    // CRITICAL: maxOutputTokens must NOT be set when using thinkingConfig
    if (thinkingBudget && thinkingBudget > 0) {
      config.thinkingConfig = { thinkingBudget };
      // Ensure maxOutputTokens is undefined to prevent API errors
      config.maxOutputTokens = undefined;
    }

    const chat = ai.chats.create({
      model: modelName,
      config,
      history: history.map((h) => ({
        role: h.role,
        parts: [{ text: h.content }],
      })),
    });

    const result = await chat.sendMessage({ message: prompt });
    
    console.log('[GeminiService] Response received:', {
      textLength: result.text?.length || 0,
      hasGroundingChunks: !!result.candidates?.[0]?.groundingMetadata?.groundingChunks,
    });

    // Extract grounding metadata if available
    const groundingChunks = result.candidates?.[0]?.groundingMetadata
      ?.groundingChunks as GeminiResponse['groundingChunks'];

    return {
      text: result.text || '',
      groundingChunks,
    };
  } catch (error) {
    console.error('Gemini API Error:', error);
    throw error;
  }
};

// Function to create a bot avatar/description based on name
export const generateBotMeta = async (botName: string) => {
  try {
    const ai = createGeminiClient();
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: `Generate a short, catchy description (max 10 words) and a suggested icon name (from Lucide React) for a bot named "${botName}". Return JSON.`,
      config: {
        responseMimeType: 'application/json',
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            description: { type: Type.STRING },
            iconName: { type: Type.STRING },
          },
        },
      },
    });
    return JSON.parse(response.text || '{}');
  } catch (e) {
    return { description: 'A helpful AI bot', iconName: 'Bot' };
  }
};

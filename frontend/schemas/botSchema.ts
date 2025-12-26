import { z } from 'zod';
import { BotStatus } from '../types';

/**
 * Zod schema for Bot validation
 * Used for form validation and type-safe data handling
 */
export const botSchema = z.object({
  id: z.string().optional(),
  name: z
    .string()
    .min(1, 'Bot name is required')
    .max(100, 'Bot name must be less than 100 characters')
    .trim(),
  description: z
    .string()
    .max(500, 'Description must be less than 500 characters')
    .trim()
    .optional()
    .default(''),
  status: z.nativeEnum(BotStatus).default(BotStatus.DRAFT),
  model: z.string().min(1, 'Model is required').default('gemini-2.5-flash'),
  provider: z.enum(['gemini', 'openai', 'anthropic']).default('gemini'),
  temperature: z
    .number()
    .min(0, 'Temperature must be between 0 and 2')
    .max(2, 'Temperature must be between 0 and 2')
    .default(0.7),
  systemInstruction: z
    .string()
    .min(1, 'System instruction is required')
    .max(10000, 'System instruction is too long')
    .trim(),
  thinkingBudget: z.number().int().min(0).max(32768).optional(),
  telegramToken: z
    .string()
    .optional()
    .refine(
      (val) => {
        // Allow empty string or undefined
        if (!val || val === '') return true;
        // If provided, must match Telegram token format
        return /^\d+:[A-Za-z0-9_-]+$/.test(val);
      },
      { message: 'Invalid Telegram bot token format. Expected format: 123456789:ABC...' }
    )
    .or(z.literal('')),
  avatar: z.string().max(200, 'Avatar URL is too long').optional().or(z.literal('')),
  createdAt: z.string().optional(),
  conversationsCount: z.number().optional(),
  documentsCount: z.number().optional(),
});

/**
 * Type inferred from bot schema
 */
export type BotFormData = z.infer<typeof botSchema>;

/**
 * Partial bot schema for updates
 */
export const botUpdateSchema = botSchema
  .partial()
  .required({ name: true, systemInstruction: true });

/**
 * Validate bot data
 * @param data - Bot data to validate
 * @returns Validation result with success flag and data/errors
 */
export const validateBot = (
  data: unknown
): { success: boolean; data?: BotFormData; errors?: z.ZodError } => {
  const result = botSchema.safeParse(data);

  if (result.success) {
    return { success: true, data: result.data };
  }

  return { success: false, errors: result.error };
};

/**
 * Get field errors from Zod error
 * @param error - Zod error object
 * @returns Object with field names as keys and error messages as values
 */
export const getFieldErrors = (error: z.ZodError): Record<string, string> => {
  const fieldErrors: Record<string, string> = {};

  error.issues.forEach((err) => {
    const path = err.path.join('.');
    fieldErrors[path] = err.message;
  });

  return fieldErrors;
};

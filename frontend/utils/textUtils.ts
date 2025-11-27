/**
 * Text utility functions for cleaning and formatting text.
 */

/**
 * Remove markdown formatting symbols from text.
 * Removes: **, __, *, _, `, #, [], (), etc.
 */
export function removeMarkdown(text: string): string {
  if (!text) return text;

  // Remove markdown bold and italic
  text = text.replace(/\*\*([^*]+)\*\*/g, '$1'); // **text**
  text = text.replace(/\*([^*]+)\*/g, '$1'); // *text*
  text = text.replace(/__([^_]+)__/g, '$1'); // __text__
  text = text.replace(/_([^_]+)_/g, '$1'); // _text_
  
  // Remove markdown code
  text = text.replace(/`([^`]+)`/g, '$1'); // `code`
  text = text.replace(/```[\s\S]*?```/g, ''); // ```code block```
  
  // Remove markdown headers
  text = text.replace(/^#{1,6}\s+/gm, ''); // # Header
  
  // Remove markdown links
  text = text.replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1'); // [text](url)
  
  // Remove markdown lists
  text = text.replace(/^\s*[-*+]\s+/gm, ''); // - item
  text = text.replace(/^\s*\d+\.\s+/gm, ''); // 1. item
  
  // Remove markdown quotes
  text = text.replace(/^>\s+/gm, ''); // > quote
  
  // Clean up extra spaces and newlines
  text = text.replace(/\n{3,}/g, '\n\n'); // Max 2 newlines
  text = text.replace(/[ \t]+/g, ' '); // Multiple spaces to one
  
  return text.trim();
}

/**
 * Clean text from various formatting artifacts.
 */
export function cleanText(text: string): string {
  if (!text) return text;
  
  // First remove markdown
  text = removeMarkdown(text);
  
  // Remove other common artifacts
  text = text.replace(/[^\S\n]+/g, ' '); // Multiple spaces to one
  text = text.replace(/\n{3,}/g, '\n\n'); // Max 2 consecutive newlines
  
  return text.trim();
}


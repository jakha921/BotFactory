import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Mic,
  Paperclip,
  Bot,
  User as UserIcon,
  Sparkles,
  Brain,
  X,
  File as FileIcon,
  Image as ImageIcon,
  Mic as MicIcon,
  StopCircle,
  Trash2,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { ChatMessage, ChatAttachment, Document, TextSnippet } from '../types';
// import { generateBotResponse } from '../services/geminiService'; // Now using backend API instead
import { useChatStore } from '../store/useChatStore';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';
import { cn } from '../utils';
import { toast } from 'sonner';
import { cleanText } from '../utils/textUtils';

// Helper function to convert AudioBuffer to WAV blob (pure JavaScript, no FFmpeg needed)
function audioBufferToWav(buffer: AudioBuffer): Blob {
  const length = buffer.length;
  const numberOfChannels = buffer.numberOfChannels;
  const sampleRate = buffer.sampleRate;
  const arrayBuffer = new ArrayBuffer(44 + length * numberOfChannels * 2);
  const view = new DataView(arrayBuffer);

  // WAV header
  const writeString = (offset: number, string: string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  let offset = 0;
  writeString(offset, 'RIFF'); offset += 4;
  view.setUint32(offset, 36 + length * numberOfChannels * 2, true); offset += 4;
  writeString(offset, 'WAVE'); offset += 4;
  writeString(offset, 'fmt '); offset += 4;
  view.setUint32(offset, 16, true); offset += 4; // Sub-chunk size
  view.setUint16(offset, 1, true); offset += 2; // Audio format (PCM)
  view.setUint16(offset, numberOfChannels, true); offset += 2;
  view.setUint32(offset, sampleRate, true); offset += 4;
  view.setUint32(offset, sampleRate * numberOfChannels * 2, true); offset += 4;
  view.setUint16(offset, numberOfChannels * 2, true); offset += 2;
  view.setUint16(offset, 16, true); offset += 2; // Bits per sample
  writeString(offset, 'data'); offset += 4;
  view.setUint32(offset, length * numberOfChannels * 2, true); offset += 4;

  // Convert float samples to 16-bit PCM
  for (let i = 0; i < length; i++) {
    for (let channel = 0; channel < numberOfChannels; channel++) {
      const sample = Math.max(-1, Math.min(1, buffer.getChannelData(channel)[i]));
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
      offset += 2;
    }
  }

  return new Blob([arrayBuffer], { type: 'audio/wav' });
}

export const BotChat: React.FC = () => {
  console.log('[BotChat] Component rendered');
  const { messages, addMessage, clearMessages } = useChatStore();
  const { selectedBotId } = useAppStore();

  // Bot state - load full bot data from API
  const [selectedBot, setSelectedBot] = useState<Bot | null>(null);
  const [isLoadingBot, setIsLoadingBot] = useState(false);

  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isThinkingMode, setIsThinkingMode] = useState(false);

  // Knowledge Base State
  const [knowledgeBase, setKnowledgeBase] = useState<{
    documents: Document[];
    snippets: TextSnippet[];
  }>({ documents: [], snippets: [] });
  const [isLoadingKnowledge, setIsLoadingKnowledge] = useState(false);

  // Attachments State
  const [pendingAttachments, setPendingAttachments] = useState<ChatAttachment[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Audio Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  // Use any for the timer ref to avoid NodeJS namespace issues in browser environment
  const recordingTimerRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Load full bot data from API when selectedBotId changes
  useEffect(() => {
    if (selectedBotId) {
      loadBotData(selectedBotId);
    } else {
      setSelectedBot(null);
      setKnowledgeBase({ documents: [], snippets: [] });
    }
  }, [selectedBotId]);

  // Load knowledge base when bot is loaded
  useEffect(() => {
    if (selectedBotId && selectedBot) {
      loadKnowledgeBase(selectedBotId);
    } else {
      setKnowledgeBase({ documents: [], snippets: [] });
    }
  }, [selectedBotId, selectedBot]);

  const loadBotData = async (botId: string) => {
    setIsLoadingBot(true);
    try {
      const bot = await api.bots.get(botId);
      setSelectedBot(bot);
      console.log('[BotChat] Bot loaded:', {
        id: bot.id,
        name: bot.name,
        model: bot.model,
        hasSystemInstruction: !!bot.systemInstruction,
        systemInstructionLength: bot.systemInstruction?.length || 0,
        thinkingBudget: bot.thinkingBudget,
      });
    } catch (error) {
      console.error('[BotChat] Failed to load bot:', error);
      toast.error('Failed to load bot data');
      setSelectedBot(null);
    } finally {
      setIsLoadingBot(false);
    }
  };

  const loadKnowledgeBase = async (botId: string) => {
    setIsLoadingKnowledge(true);
    try {
      const [documents, snippets] = await Promise.all([
        api.knowledge.documents(botId).catch(() => []),
        api.knowledge.snippets(botId).catch(() => []),
      ]);
      setKnowledgeBase({ documents, snippets });
      console.log('[BotChat] Knowledge base loaded:', { documents: documents.length, snippets: snippets.length });
    } catch (error) {
      console.error('[BotChat] Failed to load knowledge base:', error);
      toast.error('Failed to load knowledge base');
    } finally {
      setIsLoadingKnowledge(false);
    }
  };

  // Cleanup timer
  useEffect(() => {
    return () => {
      if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
    };
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      const type = file.type.startsWith('image/') ? 'image' : 'file';

      // Store file in attachment for later processing
      const newAttachment: ChatAttachment = {
        id: Date.now().toString(),
        type,
        name: file.name,
        url: URL.createObjectURL(file), // Blob URL for preview/display
        size: (file.size / 1024).toFixed(0) + 'KB',
        file: file, // Store File object for processing
      };

      setPendingAttachments((prev) => [...prev, newAttachment]);
      toast.success(`File "${file.name}" added. Will be processed when you send the message.`);
    }
    // Reset input
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeAttachment = (id: string) => {
    setPendingAttachments((prev) => prev.filter((a) => a.id !== id));
  };

  const toggleRecording = () => {
    if (isRecording) {
      // Stop Recording
      stopRecording();
    } else {
      // Start Recording
      startRecording();
    }
  };

  const startRecording = async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Initialize MediaRecorder with WAV format (doesn't require FFmpeg on backend)
      // Try different MIME types in order of preference
      let mimeType = 'audio/webm;codecs=opus'; // Default fallback
      if (MediaRecorder.isTypeSupported('audio/webm')) {
        mimeType = 'audio/webm';
      } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
        mimeType = 'audio/ogg;codecs=opus';
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4';
      }

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: mimeType
      });

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Collect audio chunks
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // When recording stops, create audio file
      mediaRecorder.onstop = async () => {
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());

        try {
          // Convert webm to wav using Web Audio API (no FFmpeg needed on backend)
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const arrayBuffer = await audioBlob.arrayBuffer();
          const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
          const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

          // Convert AudioBuffer to WAV blob
          const wavBlob = audioBufferToWav(audioBuffer);

          // Create audio file in WAV format
          const audioFile = new File([wavBlob], `voice-message-${Date.now()}.wav`, {
            type: 'audio/wav',
          });

          // Create attachment
          const audioAttachment: ChatAttachment = {
            id: Date.now().toString(),
            type: 'audio',
            name: 'Voice Message',
            url: URL.createObjectURL(wavBlob),
            size: `${(wavBlob.size / 1024).toFixed(0)}KB`,
          };

          // Send audio for transcription (now in WAV format, works without FFmpeg)
          handleSendWithAudio(audioAttachment, audioFile);
        } catch (error: any) {
          console.error('[BotChat] Failed to convert audio to WAV:', error);
          toast.error('Ошибка обработки аудио. Попробуйте еще раз.');

          // Fallback: send as webm (will try Google Speech API if available)
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const audioFile = new File([audioBlob], `voice-message-${Date.now()}.webm`, {
            type: 'audio/webm',
          });

          const audioAttachment: ChatAttachment = {
            id: Date.now().toString(),
            type: 'audio',
            name: 'Voice Message',
            url: URL.createObjectURL(audioBlob),
            size: `${(audioBlob.size / 1024).toFixed(0)}KB`,
          };

          handleSendWithAudio(audioAttachment, audioFile);
        }
      };

      // Start recording
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);

    } catch (error) {
      console.error('[BotChat] Failed to start recording:', error);
      toast.error('Failed to access microphone. Please grant microphone permissions.');
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }

    setIsRecording(false);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const handleSendWithAudio = async (audioAttachment: ChatAttachment, audioFile: File) => {
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: '[Audio Message]',
      timestamp: new Date(),
      attachments: [audioAttachment],
    };
    addMessage(userMsg);
    setIsTyping(true);

    try {
      // Get bot configuration
      if (!selectedBot) {
        throw new Error('No bot selected. Please select a bot first.');
      }

      // Transcribe audio using backend API
      console.log('[BotChat] Transcribing audio...', {
        fileName: audioFile.name,
        fileSize: audioFile.size,
        fileType: audioFile.type,
      });

      // Try with different language codes if first attempt fails
      let transcriptionResult = await api.chat.transcribeAudio(audioFile, 'uz-UZ');

      // If Uzbek fails, try Russian
      if (transcriptionResult.error || !transcriptionResult.text) {
        console.log('[BotChat] Uzbek transcription failed, trying Russian...');
        transcriptionResult = await api.chat.transcribeAudio(audioFile, 'ru-RU');
      }

      // If Russian fails, try English
      if (transcriptionResult.error || !transcriptionResult.text) {
        console.log('[BotChat] Russian transcription failed, trying English...');
        transcriptionResult = await api.chat.transcribeAudio(audioFile, 'en-US');
      }

      if (transcriptionResult.error || !transcriptionResult.text) {
        const errorMsg = transcriptionResult.error || 'Failed to transcribe audio';
        console.error('[BotChat] All transcription attempts failed:', errorMsg);
        throw new Error(errorMsg);
      }

      const transcribedText = transcriptionResult.text;
      console.log('[BotChat] Audio transcribed successfully:', {
        text: transcribedText.substring(0, 100) + '...',
        confidence: transcriptionResult.confidence,
        language: transcriptionResult.language_code,
      });

      // Update user message with transcribed text
      userMsg.content = transcribedText;

      // Now send transcribed text to bot (similar to handleSend)
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      history.push({ role: 'user', content: transcribedText }); // Add current message to history

      const modelName = selectedBot.model || 'gemini-2.5-flash';
      const thinkingBudget = selectedBot.thinkingBudget || (isThinkingMode ? 32768 : undefined);

      // Build system instruction
      let baseSystemInstruction = selectedBot.systemInstruction?.trim() || '';
      if (!baseSystemInstruction || baseSystemInstruction.length < 10) {
        baseSystemInstruction = 'You are a helpful AI assistant created on Bot Factory.';
      }

      let systemInstruction = baseSystemInstruction;

      // Include knowledge base
      if (knowledgeBase.snippets.length > 0 || knowledgeBase.documents.length > 0) {
        const knowledgeContext: string[] = [];

        if (knowledgeBase.snippets.length > 0) {
          knowledgeContext.push('\n\n## 📚 Knowledge Base - Reference Information:');
          knowledgeContext.push('When answering questions, use the following information as your primary source:');
          knowledgeBase.snippets.forEach((snippet) => {
            knowledgeContext.push(`\n### ${snippet.title}`);
            knowledgeContext.push(snippet.content);
          });
        }

        if (knowledgeBase.documents.length > 0) {
          const readyDocs = knowledgeBase.documents.filter((doc) => doc.status === 'ready');
          if (readyDocs.length > 0) {
            knowledgeContext.push('\n\n## 📄 Available Knowledge Documents:');
            readyDocs.forEach((doc) => {
              knowledgeContext.push(`- ${doc.name} (${doc.type})`);
            });
          }
        }

        systemInstruction = `${baseSystemInstruction}\n\n${knowledgeContext.join('\n')}`;
      }

      // Call backend API to generate response (instead of direct Gemini call)
      console.log('[BotChat] Generating response via backend API...');
      const response = await api.chat.generateResponse(
        selectedBot.id,
        transcribedText,
        systemInstruction,
        history.slice(0, -1), // History without current message
        thinkingBudget,
        selectedBot.temperature
      );

      // Clean markdown formatting from bot response
      const cleanedText = cleanText(response.text || "I'm sorry, I couldn't generate a response.");

      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'model',
        content: cleanedText,
        timestamp: new Date(),
        isThinking: isThinkingMode,
      };

      addMessage(botMsg);

      // Add Search Grounding info if available
      if (response.groundingChunks?.length) {
        const sourcesMsg: ChatMessage = {
          id: (Date.now() + 2).toString(),
          role: 'model',
          content:
            `Sources found: \n` +
            response.groundingChunks.map((c: any) => `- ${c.web?.title}: ${c.web?.uri}`).join('\n'),
          timestamp: new Date(),
        };
        addMessage(sourcesMsg);
      }
    } catch (error: any) {
      console.error('[BotChat] Error processing audio:', error);
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'model',
        content: error.message || 'Sorry, I encountered an error processing the audio message.',
        timestamp: new Date(),
      };
      addMessage(errorMsg);
      toast.error(error.message || 'Failed to process audio message');
    } finally {
      setIsTyping(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() && pendingAttachments.length === 0) return;

    // Process file attachments first to extract text
    let processedContent = input;
    const fileContents: string[] = [];

    if (pendingAttachments.length > 0) {
      setIsTyping(true);
      toast.info('Processing attachments...');

      try {
        // Process files that have File objects stored
        const filePromises = pendingAttachments
          .filter((attachment) => attachment.file && (attachment.type === 'image' || attachment.type === 'file'))
          .map(async (attachment) => {
            if (!attachment.file) return;

            try {
              console.log(`[BotChat] Processing file: ${attachment.name}`);
              const result = await api.chat.processFile(attachment.file);

              if (result.text && !result.error) {
                fileContents.push(`\n\n[File: ${attachment.name}]\n${result.text}`);
                console.log(`[BotChat] File processed successfully: ${attachment.name} (${result.text.length} chars)`);
              } else if (result.error) {
                console.warn(`[BotChat] File processing error for ${attachment.name}:`, result.error);
                fileContents.push(`\n\n[File: ${attachment.name} - Error: ${result.error}]`);
              }
            } catch (error: any) {
              console.error(`[BotChat] Failed to process attachment ${attachment.name}:`, error);
              fileContents.push(`\n\n[File: ${attachment.name} - Could not process: ${error.message || 'Unknown error'}]`);
            }
          });

        await Promise.all(filePromises);

        // Combine original input with file contents
        if (fileContents.length > 0) {
          processedContent = input + (input ? '\n\n' : '') + fileContents.join('\n\n');
          console.log('[BotChat] Combined content with files:', {
            originalLength: input.length,
            filesCount: fileContents.length,
            combinedLength: processedContent.length,
          });
        }
      } catch (error: any) {
        console.error('[BotChat] Error processing files:', error);
        toast.error('Some files could not be processed');
      }
    }

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: processedContent,
      timestamp: new Date(),
      attachments: [...pendingAttachments],
    };

    addMessage(userMsg);
    setInput('');
    setPendingAttachments([]);
    setIsTyping(true);

    try {
      // Get bot configuration
      if (!selectedBot) {
        throw new Error('No bot selected. Please select a bot first.');
      }

      // Construct history for context
      const history = messages.map((m) => ({ role: m.role, content: m.content }));

      // Use bot settings: model, temperature, thinkingBudget
      const modelName = selectedBot.model || 'gemini-2.5-flash';
      const thinkingBudget = selectedBot.thinkingBudget || (isThinkingMode ? 32768 : undefined);

      // Build system instruction - START with bot's instruction (this is the core behavior)
      let baseSystemInstruction = selectedBot.systemInstruction?.trim() || '';

      // Validate system instruction exists
      if (!baseSystemInstruction || baseSystemInstruction.length < 10) {
        console.warn('[BotChat] Warning: Bot has no or very short systemInstruction. Using default.');
        baseSystemInstruction = 'You are a helpful AI assistant created on Bot Factory.';
      }

      console.log('[BotChat] Base system instruction:', {
        length: baseSystemInstruction.length,
        preview: baseSystemInstruction.substring(0, 150) + '...',
      });

      // Build final system instruction with knowledge base
      let systemInstruction = baseSystemInstruction;

      // Include knowledge base in system instruction if available
      if (knowledgeBase.snippets.length > 0 || knowledgeBase.documents.length > 0) {
        const knowledgeContext: string[] = [];

        // Add snippets to context (these contain actual knowledge)
        if (knowledgeBase.snippets.length > 0) {
          knowledgeContext.push('\n\n## 📚 Knowledge Base - Reference Information:');
          knowledgeContext.push('When answering questions, use the following information as your primary source:');
          knowledgeBase.snippets.forEach((snippet) => {
            knowledgeContext.push(`\n### ${snippet.title}`);
            knowledgeContext.push(snippet.content);
            if (snippet.tags && snippet.tags.length > 0) {
              knowledgeContext.push(`Tags: ${snippet.tags.join(', ')}`);
            }
          });
        }

        // Add document summaries to context (metadata only)
        if (knowledgeBase.documents.length > 0) {
          const readyDocs = knowledgeBase.documents.filter((doc) => doc.status === 'ready');
          if (readyDocs.length > 0) {
            knowledgeContext.push('\n\n## 📄 Available Knowledge Documents:');
            readyDocs.forEach((doc) => {
              knowledgeContext.push(`- ${doc.name} (${doc.type})`);
            });
            knowledgeContext.push('\nNote: Use information from snippets above when available. Documents are listed for reference.');
          }
        }

        // Combine base instruction with knowledge base
        systemInstruction = `${baseSystemInstruction}\n\n${knowledgeContext.join('\n')}`;
      }

      console.log('[BotChat] Final system instruction:', {
        botId: selectedBot.id,
        botName: selectedBot.name,
        model: modelName,
        thinkingBudget,
        baseInstructionLength: baseSystemInstruction.length,
        finalInstructionLength: systemInstruction.length,
        hasKnowledgeBase: knowledgeBase.snippets.length > 0 || knowledgeBase.documents.length > 0,
        knowledgeSnippets: knowledgeBase.snippets.length,
        knowledgeDocuments: knowledgeBase.documents.length,
        systemInstructionFirst300: systemInstruction.substring(0, 300) + '...',
      });

      // Call backend API to generate response (instead of direct Gemini call)
      console.log('[BotChat] Generating response via backend API...');
      const response = await api.chat.generateResponse(
        selectedBot.id,
        processedContent || input || 'Sent an attachment',
        systemInstruction,
        history,
        thinkingBudget,
        selectedBot.temperature
      );

      // Clean markdown formatting from bot response
      const cleanedText = cleanText(response.text || "I'm sorry, I couldn't generate a response.");

      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'model',
        content: cleanedText,
        timestamp: new Date(),
        isThinking: isThinkingMode,
      };

      addMessage(botMsg);

      // Add Search Grounding info if available
      if (response.groundingChunks?.length) {
        const sourcesMsg: ChatMessage = {
          id: (Date.now() + 2).toString(),
          role: 'model',
          content:
            `Sources found: \n` +
            response.groundingChunks.map((c: any) => `- ${c.web?.title}: ${c.web?.uri}`).join('\n'),
          timestamp: new Date(),
        };
        addMessage(sourcesMsg);
      }
    } catch (error) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'model',
        content: 'Sorry, I encountered an error connecting to Gemini.',
        timestamp: new Date(),
      };
      addMessage(errorMsg);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearChat = () => {
    if (window.confirm('Are you sure you want to clear the chat history?')) {
      clearMessages();
    }
  };

  // Show message if no bot is selected
  if (!selectedBotId) {
    return (
      <div className="h-[calc(100vh-140px)] flex flex-col max-w-4xl mx-auto items-center justify-center">
        <div className="text-center space-y-4">
          <Bot className="w-16 h-16 text-gray-300 mx-auto" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">No Bot Selected</h2>
          <p className="text-gray-500 max-w-md">
            Please select a bot from the header dropdown to start chatting and test its configuration.
          </p>
        </div>
      </div>
    );
  }

  // Show loading state while bot data is being loaded
  if (isLoadingBot || !selectedBot) {
    return (
      <div className="h-[calc(100vh-140px)] flex flex-col max-w-4xl mx-auto items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto" />
          <p className="text-gray-500">Loading bot configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-140px)] flex flex-col max-w-4xl mx-auto">
      {/* Chat Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Bot className="w-6 h-6 text-primary" />
            {selectedBot ? selectedBot.name : 'No Bot Selected'}
            {isThinkingMode && selectedBot?.thinkingBudget && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300">
                Thinking Mode
              </span>
            )}
          </h2>
          <p className="text-sm text-gray-500">
            {selectedBot
              ? `Testing ${selectedBot.name} (${selectedBot.model}) configuration in real-time.`
              : 'Please select a bot from the header to start chatting.'}
            {knowledgeBase.snippets.length > 0 || knowledgeBase.documents.length > 0 ? (
              <span className="ml-2 text-xs text-green-600 dark:text-green-400">
                • Knowledge base active ({knowledgeBase.snippets.length} snippets, {knowledgeBase.documents.length} documents)
              </span>
            ) : null}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {selectedBot.thinkingBudget && selectedBot.thinkingBudget > 0 && (
            <button
              onClick={() => setIsThinkingMode(!isThinkingMode)}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 border',
                isThinkingMode
                  ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 border-purple-200 dark:border-purple-800'
                  : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
              )}
            >
              <Brain className={cn('w-4 h-4', isThinkingMode && 'animate-pulse')} />
              <span>Thinking Mode</span>
            </button>
          )}

          <button
            onClick={handleClearChat}
            className="p-2 rounded-full hover:bg-red-50 dark:hover:bg-red-900/20 text-gray-400 hover:text-red-500 transition-colors"
            title="Clear Chat"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <Card className="flex-1 overflow-hidden flex flex-col border-0 shadow-xl ring-1 ring-black/5 dark:ring-white/5">
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-white dark:bg-gray-900">
          {messages.length === 0 && (
            <div className="h-full flex items-center justify-center text-gray-400 text-sm italic">
              Start a conversation with your bot...
            </div>
          )}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                'flex gap-4 max-w-[85%]',
                msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''
              )}
            >
              <div
                className={cn(
                  'w-8 h-8 rounded-full flex items-center justify-center shrink-0',
                  msg.role === 'user'
                    ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900'
                    : msg.isThinking
                      ? 'bg-purple-600 text-white'
                      : 'bg-primary text-white'
                )}
              >
                {msg.role === 'user' ? (
                  <UserIcon className="w-5 h-5" />
                ) : msg.isThinking ? (
                  <Brain className="w-5 h-5" />
                ) : (
                  <Sparkles className="w-5 h-5" />
                )}
              </div>

              <div
                className={cn(
                  'p-4 rounded-2xl text-sm leading-relaxed shadow-sm whitespace-pre-wrap min-w-[120px]',
                  msg.role === 'user'
                    ? 'bg-primary text-white rounded-tr-none'
                    : cn(
                      'text-gray-900 dark:text-gray-100 rounded-tl-none border',
                      msg.isThinking
                        ? 'bg-purple-50 dark:bg-purple-900/20 border-purple-100 dark:border-purple-800/50'
                        : 'bg-gray-100 dark:bg-gray-800 border-transparent'
                    )
                )}
              >
                {/* Render Attachments */}
                {msg.attachments &&
                  msg.attachments.map((att) => (
                    <div
                      key={att.id}
                      className="mb-2 p-2 rounded-lg bg-black/10 dark:bg-white/10 flex items-center gap-2"
                    >
                      {att.type === 'audio' ? (
                        <>
                          <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                            <MicIcon className="w-4 h-4" />
                          </div>
                          <div className="h-1 w-20 bg-white/30 rounded-full overflow-hidden relative">
                            <div className="absolute left-0 top-0 bottom-0 w-1/2 bg-white/80" />
                          </div>
                          <span className="text-xs opacity-80">0:05</span>
                        </>
                      ) : att.type === 'image' ? (
                        <div className="flex items-center gap-2">
                          <ImageIcon className="w-4 h-4" />
                          <span className="text-xs underline truncate max-w-[150px]">
                            {att.name}
                          </span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <FileIcon className="w-4 h-4" />
                          <span className="text-xs underline truncate max-w-[150px]">
                            {att.name}
                          </span>
                        </div>
                      )}
                    </div>
                  ))}

                {msg.content}
                <div
                  className={cn(
                    'text-[10px] mt-2 opacity-70 text-right flex items-center justify-end gap-1',
                    msg.role === 'user' ? 'text-primary-100' : 'text-gray-500 dark:text-gray-400'
                  )}
                >
                  {msg.isThinking && (
                    <span className="text-purple-500 font-medium">Deep Thinking</span>
                  )}
                  <span>
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex gap-4 max-w-[85%]">
              <div
                className={cn(
                  'w-8 h-8 rounded-full text-white flex items-center justify-center shrink-0',
                  isThinkingMode ? 'bg-purple-600' : 'bg-primary'
                )}
              >
                {isThinkingMode ? (
                  <Brain className="w-5 h-5 animate-pulse" />
                ) : (
                  <Sparkles className="w-5 h-5" />
                )}
              </div>
              <div className="p-4 rounded-2xl rounded-tl-none bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 flex items-center gap-1">
                <span
                  className={cn(
                    'w-2 h-2 rounded-full animate-bounce',
                    isThinkingMode ? 'bg-purple-400' : 'bg-gray-400'
                  )}
                  style={{ animationDelay: '0ms' }}
                />
                <span
                  className={cn(
                    'w-2 h-2 rounded-full animate-bounce',
                    isThinkingMode ? 'bg-purple-400' : 'bg-gray-400'
                  )}
                  style={{ animationDelay: '150ms' }}
                />
                <span
                  className={cn(
                    'w-2 h-2 rounded-full animate-bounce',
                    isThinkingMode ? 'bg-purple-400' : 'bg-gray-400'
                  )}
                  style={{ animationDelay: '300ms' }}
                />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-gray-50 dark:bg-gray-900/50 border-t border-black/5 dark:border-white/5">
          {/* Pending Attachments */}
          {pendingAttachments.length > 0 && (
            <div className="flex gap-2 mb-3 overflow-x-auto pb-1">
              {pendingAttachments.map((att) => (
                <div
                  key={att.id}
                  className="flex items-center gap-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-2 pr-1 shadow-sm animate-in fade-in zoom-in-95 duration-200"
                >
                  <div className="w-8 h-8 rounded bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-gray-500">
                    {att.type === 'image' ? (
                      <ImageIcon className="w-4 h-4" />
                    ) : (
                      <FileIcon className="w-4 h-4" />
                    )}
                  </div>
                  <div className="text-xs">
                    <div className="font-medium truncate max-w-[100px] text-gray-900 dark:text-white">
                      {att.name}
                    </div>
                    <div className="text-gray-400">{att.size}</div>
                  </div>
                  <button
                    onClick={() => removeAttachment(att.id)}
                    className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full text-gray-400 hover:text-red-500"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="relative flex items-end gap-2">
            <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileSelect} />
            <Button
              variant="icon"
              size="md"
              className="mb-1 text-gray-500 hover:text-primary"
              onClick={() => fileInputRef.current?.click()}
            >
              <Paperclip className="w-5 h-5" />
            </Button>

            <div className="flex-1 relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={isThinkingMode ? 'Ask a complex question...' : 'Message Gemini...'}
                className={cn(
                  'w-full resize-none max-h-32 py-3 px-4 rounded-xl border focus:ring-2 focus:border-transparent outline-none text-sm custom-scrollbar transition-colors',
                  'bg-white dark:bg-white/5 border-black/10 dark:border-white/10 text-gray-900 dark:text-gray-100',
                  isThinkingMode
                    ? 'border-purple-200 dark:border-purple-800 focus:ring-purple-500'
                    : 'focus:ring-primary'
                )}
                rows={1}
                style={{ minHeight: '44px' }}
              />
            </div>

            {input.trim() || pendingAttachments.length > 0 ? (
              <Button
                onClick={handleSend}
                disabled={isTyping}
                className={cn(
                  'mb-1 rounded-xl',
                  isThinkingMode ? 'bg-purple-600 hover:bg-purple-700' : 'bg-primary'
                )}
                variant="primary"
              >
                <Send className="w-4 h-4" />
              </Button>
            ) : (
              <Button
                onClick={toggleRecording}
                className={cn(
                  'mb-1 rounded-xl transition-all duration-300',
                  isRecording
                    ? 'bg-red-500 hover:bg-red-600 w-24'
                    : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300'
                )}
                variant="ghost"
              >
                {isRecording ? (
                  <div className="flex items-center gap-2 text-white">
                    <StopCircle className="w-4 h-4 animate-pulse" />
                    <span className="text-xs font-mono">{formatTime(recordingTime)}</span>
                  </div>
                ) : (
                  <Mic className="w-5 h-5" />
                )}
              </Button>
            )}
          </div>
          <p className="text-xs text-center text-gray-400 mt-2">
            AI responses can be inaccurate. Double check important info.
          </p>
        </div>
      </Card>
    </div>
  );
};

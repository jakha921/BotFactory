import React, { useState, useEffect } from 'react';
import {
  Save,
  ArrowLeft,
  Bot,
  Box,
  Settings2,
  Code2,
  Webhook,
  Brain,
  Sparkles,
  Loader2,
  Key,
  Plus,
  Trash2,
  Copy,
  Check,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Textarea } from '../components/ui/Textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Tabs } from '../components/ui/Tabs';
import { Label } from '../components/ui/Label';
import { Bot as BotType, BotStatus, UIConfig, InlineKeyboardButton } from '../types';
import { api } from '../services/api';
import { generateBotResponse } from '../services/geminiService';
import { validateBot, getFieldErrors } from '../schemas/botSchema';
import { KeyboardEditor } from '../components/ui/KeyboardEditor';
import { FormEditor } from '../components/ui/FormEditor';
import { useAppStore } from '../store/useAppStore';
import { KnowledgeSettings } from './KnowledgeSettings';

interface BotSettingsProps {
  botId: string | null;
  onBack: () => void;
}

const TABS = [
  { id: 'general', label: 'General' },
  { id: 'model', label: 'Model & AI' },
  { id: 'knowledge', label: 'Knowledge Base' },
  { id: 'integrations', label: 'Integrations' },
  { id: 'ui', label: 'UI & Buttons' },
];

export const BotSettings: React.FC<BotSettingsProps> = ({ botId, onBack }) => {
  console.log('[BotSettings] Component rendered', { botId });
  const { setBots } = useAppStore();
  const [activeTab, setActiveTab] = useState('general');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isSavingUIConfig, setIsSavingUIConfig] = useState(false);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [isImproving, setIsImproving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  // Bot status state
  const [botStatus, setBotStatus] = useState<{
    is_running: boolean;
    last_heartbeat: string | null;
  } | null>(null);
  const [isLoadingStatus, setIsLoadingStatus] = useState(false);
  const [isRestarting, setIsRestarting] = useState(false);
  
  // API Keys State
  const [apiKeys, setApiKeys] = useState<Array<{
    id: string;
    name: string;
    key_prefix: string;
    is_active: boolean;
    last_used_at: string | null;
    created_at: string;
    expires_at: string | null;
  }>>([]);
  const [isLoadingAPIKeys, setIsLoadingAPIKeys] = useState(false);
  const [isCreatingAPIKey, setIsCreatingAPIKey] = useState(false);
  const [newAPIKeyName, setNewAPIKeyName] = useState('');
  const [newAPIKey, setNewAPIKey] = useState<string | null>(null);
  const [copiedKeyId, setCopiedKeyId] = useState<string | null>(null);
  
  // UI Config State
  const [uiConfig, setUIConfig] = useState<UIConfig>({
    inline_keyboards: {},
    forms: {},
    welcome_message: '',
    help_message: '',
    default_inline_keyboard: [],
  });

  // Form State
  const [formData, setFormData] = useState<Partial<BotType>>({
    name: '',
    description: '',
    model: 'gemini-2.5-flash',
    provider: 'gemini',
    temperature: 0.7,
    thinkingBudget: 0,
    systemInstruction: '',
    telegramToken: '',
    status: BotStatus.DRAFT,
  });

  // Load bot status periodically
  useEffect(() => {
    if (!botId || botId === 'new') {
      setBotStatus(null);
      return;
    }
    
    const loadStatus = async () => {
      try {
        setIsLoadingStatus(true);
        const status = await api.bots.getBotStatus(botId);
        setBotStatus(status);
      } catch (error) {
        console.error('[BotSettings] Failed to load bot status:', error);
      } finally {
        setIsLoadingStatus(false);
      }
    };
    
    // Load immediately
    loadStatus();
    
    // Then reload every 30 seconds
    const interval = setInterval(loadStatus, 30000);
    
    return () => clearInterval(interval);
  }, [botId]);
  
  useEffect(() => {
    if (botId && botId !== 'new') {
      setIsLoading(true);
      Promise.all([
        api.bots.get(botId),
        api.bots.getUIConfig(botId).catch(() => ({
          inline_keyboards: {},
          forms: {},
          welcome_message: '',
          help_message: '',
          default_inline_keyboard: [],
        })),
        api.bots.getAPIKeys(botId).catch(() => []),
      ])
        .then(([bot, config, keys]) => {
          if (bot) {
            setFormData(bot);
            setUIConfig({
              inline_keyboards: config.inline_keyboards || {},
              forms: config.forms || {},
              welcome_message: config.welcome_message || bot.welcomeMessage || '',
              help_message: config.help_message || bot.helpMessage || '',
              default_inline_keyboard: config.default_inline_keyboard || bot.defaultInlineKeyboard || [],
            });
            setApiKeys(keys || []);
          }
        })
        .catch((error) => {
          console.error('[BotSettings] Failed to load bot:', error);
          toast.error('Failed to load bot. Please try again.');
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      // Reset form for new bot
      setFormData({
        name: '',
        description: '',
        model: 'gemini-2.5-flash',
        provider: 'gemini',
        temperature: 0.7,
        thinkingBudget: 0,
        systemInstruction: '',
        telegramToken: '',
        status: BotStatus.DRAFT,
      });
      setUIConfig({
        inline_keyboards: {},
        forms: {},
        welcome_message: '',
        help_message: '',
        default_inline_keyboard: [],
      });
      setApiKeys([]);
    }
  }, [botId]);
  
  // Load API keys when integrations tab is active
  useEffect(() => {
    if (activeTab === 'integrations' && botId && botId !== 'new') {
      loadAPIKeys();
    }
  }, [activeTab, botId]);
  
  const loadAPIKeys = async () => {
    if (!botId || botId === 'new') return;
    setIsLoadingAPIKeys(true);
    try {
      const keys = await api.bots.getAPIKeys(botId);
      setApiKeys(keys);
    } catch (error: any) {
      console.error('[BotSettings] Failed to load API keys:', error);
      toast.error('Failed to load API keys');
    } finally {
      setIsLoadingAPIKeys(false);
    }
  };
  
  const handleCreateAPIKey = async () => {
    if (!botId || botId === 'new') {
      toast.error('Please save the bot first');
      return;
    }
    if (!newAPIKeyName.trim()) {
      toast.error('Please enter a name for the API key');
      return;
    }
    
    setIsCreatingAPIKey(true);
    try {
      const result = await api.bots.createAPIKey(botId, newAPIKeyName);
      setNewAPIKey(result.key);
      setNewAPIKeyName('');
      await loadAPIKeys();
      toast.success('API key created successfully');
    } catch (error: any) {
      console.error('[BotSettings] Failed to create API key:', error);
      toast.error(error?.message || 'Failed to create API key');
    } finally {
      setIsCreatingAPIKey(false);
    }
  };
  
  const handleDeleteAPIKey = async (apiKeyId: string) => {
    if (!botId || botId === 'new') return;
    if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
      return;
    }
    
    try {
      await api.bots.deleteAPIKey(botId, apiKeyId);
      await loadAPIKeys();
      toast.success('API key deleted successfully');
    } catch (error: any) {
      console.error('[BotSettings] Failed to delete API key:', error);
      toast.error(error?.message || 'Failed to delete API key');
    }
  };
  
  const handleCopyAPIKey = (key: string, keyId: string) => {
    navigator.clipboard.writeText(key);
    setCopiedKeyId(keyId);
    toast.success('API key copied to clipboard');
    setTimeout(() => setCopiedKeyId(null), 2000);
  };

  const handleChange = (field: keyof BotType, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error on change
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }));
    }
  };

  const handleImproveInstruction = async () => {
    if (!formData.systemInstruction) return;
    setIsImproving(true);
    try {
      const prompt = `Rewrite the following system instructions for an AI bot to be more professional, concise, and robust. Keep the core intent and behavior, but improve clarity and effectiveness: \n\n${formData.systemInstruction}`;
      const response = await generateBotResponse(
        'gemini-2.5-flash',
        prompt,
        'You are an expert prompt engineer specializing in LLM system instructions.'
      );
      if (response.text) {
        handleChange('systemInstruction', response.text);
        toast.success('System instruction improved successfully');
      }
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to improve instruction';
      toast.error(errorMessage);
    } finally {
      setIsImproving(false);
    }
  };

  const handleSaveUIConfig = async () => {
    if (!botId || botId === 'new') {
      toast.error('Please save the bot first before configuring UI');
      return;
    }
    
    setIsSavingUIConfig(true);
    try {
      await api.bots.updateUIConfig(botId, uiConfig);
      toast.success('UI configuration saved successfully');
    } catch (error: any) {
      console.error('[BotSettings] Failed to save UI config:', error);
      const errorMessage = error?.message || 'Failed to save UI configuration';
      toast.error(errorMessage);
    } finally {
      setIsSavingUIConfig(false);
    }
  };

  const handleTestTelegramConnection = async () => {
    if (!botId || botId === 'new') {
      toast.error('Please save the bot first before testing connection');
      return;
    }
    
    if (!formData.telegramToken) {
      toast.error('Please enter a Telegram token first');
      return;
    }
    
    setIsTestingConnection(true);
    try {
      const result = await api.bots.testTelegramConnection(botId);
      
      if (result.success && result.bot_info) {
        let message = `Connection successful! Bot: @${result.bot_info.username} (${result.bot_info.first_name})`;
        
        console.log('[BotSettings] Connection test result:', {
          has_telegram_id: result.has_telegram_id,
          notification_sent: result.notification_sent,
          notification_error: result.notification_error,
          telegram_id: result.telegram_id,
        });
        
        // Check if notification was sent or if user needs to add telegram_id
        if (result.has_telegram_id) {
          if (result.notification_sent) {
            message += '\nNotification sent to your Telegram!';
            toast.success(message, { duration: 6000 });
          } else if (result.notification_error) {
            // Show error about notification
            toast.success(message, { duration: 5000 });
            setTimeout(() => {
              toast.error(
                `Could not send notification: ${result.notification_error}`,
                { duration: 10000 }
              );
            }, 500);
          } else {
            // This shouldn't happen, but handle it anyway
            toast.success(message, { duration: 5000 });
          }
        } else {
          // Show hint about adding telegram_id ONLY if user doesn't have it
          toast.success(message, { duration: 5000 });
          setTimeout(() => {
            toast.info(
              'Tip: Add your Telegram ID in your profile settings to receive notifications when testing bot connections.',
              { duration: 8000 }
            );
          }, 1000);
        }
        
        console.log('[BotSettings] Telegram connection test successful:', result.bot_info);
      } else {
        toast.error(`Connection failed: ${result.error || 'Unknown error'}`);
        console.error('[BotSettings] Telegram connection test failed:', result.error);
      }
    } catch (error: any) {
      console.error('[BotSettings] Failed to test Telegram connection:', error);
      const errorMessage = error?.message || error?.error || 'Failed to test Telegram connection';
      toast.error(`Connection failed: ${errorMessage}`);
    } finally {
      setIsTestingConnection(false);
    }
  };
  
  const handleRestartBot = async () => {
    if (!botId || botId === 'new') {
      toast.error('Please save the bot first before restarting');
      return;
    }
    
    setIsRestarting(true);
    try {
      const result = await api.bots.restartBot(botId);
      if (result.success) {
        toast.success(result.message || 'Bot restart signal sent');
        // Reload status after a delay
        setTimeout(async () => {
          try {
            const status = await api.bots.getBotStatus(botId);
            setBotStatus(status);
          } catch (error) {
            console.error('[BotSettings] Failed to reload bot status:', error);
          }
        }, 2000);
      } else {
        toast.error(result.message || 'Failed to restart bot');
      }
    } catch (error: any) {
      console.error('[BotSettings] Failed to restart bot:', error);
      toast.error(error?.message || 'Failed to restart bot');
    } finally {
      setIsRestarting(false);
    }
  };

  const handleSave = async () => {
    // Validate using Zod schema
    const validation = validateBot(formData);

    if (!validation.success && validation.errors) {
      const fieldErrors = getFieldErrors(validation.errors);
      setErrors(fieldErrors);
      // Switch to general tab if validation fails
      setActiveTab('general');
      toast.error('Please fix the errors in the form');
      return;
    }

    if (!validation.data) {
      toast.error('Validation failed');
      return;
    }

    setIsSaving(true);
    try {
      const botData: any = {
        ...validation.data,
      };
      
      // Only include id for updates
      if (botId && botId !== 'new') {
        botData.id = botId;
      }
      
      await api.bots.save(botData);
      toast.success(botId === 'new' ? 'Bot created successfully' : 'Bot updated successfully');
      console.log('[BotSettings] Bot saved, calling onBack');
      
      // Update store to refresh bot list for BotSelector
      try {
        const updatedBots = await api.bots.list();
        setBots(updatedBots);
        console.log('[BotSettings] Bot list refreshed in store:', updatedBots.length, 'bots');
      } catch (e) {
        console.error('[BotSettings] Failed to refresh bot list:', e);
      }
      
      onBack();
    } catch (error: any) {
      console.error('[BotSettings] Save error:', error);
      const errorMessage = error?.message || error?.details?.message || 'Failed to save bot';
      toast.error(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 sticky top-0 z-20 bg-gray-50/95 dark:bg-gray-950/95 backdrop-blur-sm py-2 border-b border-transparent sm:border-none">
        <div className="flex items-center gap-2">
          <Button variant="icon" size="md" onClick={onBack}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {botId === 'new' ? 'Create New Bot' : `Edit ${formData.name}`}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Configure your AI agent's behavior and connections.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={onBack}>
            Cancel
          </Button>
          <Button onClick={handleSave} isLoading={isSaving} icon={<Save className="w-4 h-4" />}>
            Save Changes
          </Button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex justify-center">
        <Tabs tabs={TABS} activeTab={activeTab} onChange={setActiveTab} />
      </div>

      {/* Content Areas */}
      <div className="space-y-6">
        {/* GENERAL TAB */}
        {activeTab === 'general' && (
          <Card className="border-black/5 dark:border-white/5 animate-in fade-in slide-in-from-left-4 duration-300">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="w-5 h-5 text-primary" />
                Basic Information
              </CardTitle>
              <CardDescription>The public identity of your bot.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2">
                <Input
                  label="Bot Name"
                  placeholder="e.g. Customer Support Agent"
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  error={errors.name}
                  required
                />
                <div className="space-y-1.5">
                  <Label>Status</Label>
                  <select
                    className="block w-full rounded-lg border px-3 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/20 bg-white dark:bg-white/5 border-black/10 dark:border-white/10 text-gray-900 dark:text-gray-100 sm:text-sm"
                    value={formData.status}
                    onChange={(e) => handleChange('status', e.target.value)}
                  >
                    <option value={BotStatus.ACTIVE}>Active</option>
                    <option value={BotStatus.PAUSED}>Paused</option>
                    <option value={BotStatus.DRAFT}>Draft</option>
                  </select>
                </div>
              </div>

              <Textarea
                label="Description"
                placeholder="Describe what this bot does..."
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                rows={3}
                helperText="Visible to team members only."
              />

              <div>
                <Label>Avatar</Label>
                <div className="flex items-center gap-4 mt-2">
                  <div className="w-16 h-16 rounded-2xl bg-indigo-50 dark:bg-indigo-900/20 border-2 border-dashed border-indigo-200 dark:border-indigo-800 flex items-center justify-center">
                    <Bot className="w-8 h-8 text-indigo-500" />
                  </div>
                  <div className="space-y-2">
                    <Button variant="secondary" size="sm">
                      Upload Image
                    </Button>
                    <p className="text-xs text-gray-500">Recommended: 512x512px PNG or JPG</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* KNOWLEDGE TAB */}
        {activeTab === 'knowledge' && botId && botId !== 'new' && (
          <KnowledgeSettings botId={botId} />
        )}

        {/* MODEL TAB */}
        {activeTab === 'model' && (
          <div className="space-y-6 animate-in fade-in slide-in-from-left-4 duration-300">
            <Card className="border-black/5 dark:border-white/5">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Box className="w-5 h-5 text-purple-500" />
                  Model Configuration
                </CardTitle>
                <CardDescription>Choose the brain behind your bot.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-6 md:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label>AI Provider</Label>
                    <select
                      className="block w-full rounded-lg border px-3 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/20 bg-white dark:bg-white/5 border-black/10 dark:border-white/10 text-gray-900 dark:text-gray-100 sm:text-sm"
                      value={formData.provider}
                      onChange={(e) => handleChange('provider', e.target.value)}
                    >
                      <option value="gemini">Google Gemini</option>
                      <option value="openai">OpenAI (GPT-4)</option>
                      <option value="anthropic">Anthropic (Claude)</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <Label>Model Version</Label>
                    <select
                      className="block w-full rounded-lg border px-3 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/20 bg-white dark:bg-white/5 border-black/10 dark:border-white/10 text-gray-900 dark:text-gray-100 sm:text-sm"
                      value={formData.model}
                      onChange={(e) => handleChange('model', e.target.value)}
                    >
                      <option value="gemini-2.5-flash">Gemini 2.5 Flash (Fastest)</option>
                      <option value="gemini-3-pro-preview">Gemini 3.0 Pro (Reasoning)</option>
                      <option value="gemini-2.5-flash-lite">Gemini 2.5 Flash Lite</option>
                    </select>
                  </div>
                </div>

                {/* Thinking Budget Control - Only for Supported Models */}
                {formData.model?.includes('gemini-3-pro') && (
                  <div className="space-y-3 p-4 bg-purple-50 dark:bg-purple-900/10 border border-purple-100 dark:border-purple-900/30 rounded-lg animate-in zoom-in-95">
                    <div className="flex justify-between items-center">
                      <Label className="flex items-center gap-2 text-purple-900 dark:text-purple-200 mb-0">
                        <Brain className="w-4 h-4" />
                        Thinking Budget
                      </Label>
                      <span className="text-sm font-mono text-purple-700 dark:text-purple-300">
                        {formData.thinkingBudget || 0} tokens
                      </span>
                    </div>
                    <p className="text-xs text-purple-600 dark:text-purple-400">
                      Allocate tokens for advanced reasoning. Max 32,768 for Gemini 3.0 Pro.
                    </p>
                    <input
                      type="range"
                      min="0"
                      max="32768"
                      step="1024"
                      value={formData.thinkingBudget || 0}
                      onChange={(e) => handleChange('thinkingBudget', parseInt(e.target.value))}
                      className="w-full h-2 bg-purple-200 dark:bg-purple-800 rounded-lg appearance-none cursor-pointer accent-purple-600"
                    />
                    <div className="flex justify-between text-xs text-purple-400 dark:text-purple-500">
                      <span>Off (Fast)</span>
                      <span>16k</span>
                      <span>32k (Deep Thought)</span>
                    </div>
                  </div>
                )}

                <div className="space-y-3">
                  <div className="flex justify-between">
                    <Label>Creativity (Temperature): {formData.temperature}</Label>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={formData.temperature}
                    onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
                    className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Precise</span>
                    <span>Balanced</span>
                    <span>Creative</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-black/5 dark:border-white/5">
              <CardHeader className="flex flex-row items-start justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Code2 className="w-5 h-5 text-emerald-500" />
                    System Instructions
                  </CardTitle>
                  <CardDescription>
                    Define how the bot should behave and what it knows.
                  </CardDescription>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleImproveInstruction}
                  disabled={isImproving || !formData.systemInstruction}
                  isLoading={isImproving}
                  icon={<Sparkles className="w-3.5 h-3.5 text-purple-500" />}
                  className="h-8"
                >
                  Improve with AI
                </Button>
              </CardHeader>
              <CardContent>
                <Textarea
                  value={formData.systemInstruction}
                  onChange={(e) => handleChange('systemInstruction', e.target.value)}
                  className="font-mono text-sm h-64"
                  placeholder="You are a helpful assistant..."
                />
              </CardContent>
            </Card>
          </div>
        )}

        {/* UI & BUTTONS TAB */}
        {activeTab === 'ui' && (
          <div className="space-y-6 animate-in fade-in slide-in-from-left-4 duration-300">
            <Card className="border-black/5 dark:border-white/5">
              <CardHeader>
                <CardTitle>Messages</CardTitle>
                <CardDescription>Configure welcome and help messages for your Telegram bot.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  label="Welcome Message"
                  value={uiConfig.welcome_message || ''}
                  onChange={(e) =>
                    setUIConfig({ ...uiConfig, welcome_message: e.target.value })
                  }
                  placeholder="👋 Привет! Я ваш AI помощник..."
                  rows={4}
                  helperText="Shown when user sends /start command"
                />
                <Textarea
                  label="Help Message"
                  value={uiConfig.help_message || ''}
                  onChange={(e) =>
                    setUIConfig({ ...uiConfig, help_message: e.target.value })
                  }
                  placeholder="ℹ️ Помощь по использованию бота..."
                  rows={4}
                  helperText="Shown when user sends /help command"
                />
              </CardContent>
            </Card>

            <Card className="border-black/5 dark:border-white/5">
              <CardHeader>
                <CardTitle>Inline Keyboards</CardTitle>
                <CardDescription>Create custom inline keyboards with buttons for your bot. You can create multiple named keyboards and reference them by name.</CardDescription>
              </CardHeader>
              <CardContent>
                <KeyboardEditor
                  keyboards={{
                    ...(uiConfig.inline_keyboards || {}),
                    ...(uiConfig.default_inline_keyboard && uiConfig.default_inline_keyboard.length > 0
                      ? { default: uiConfig.default_inline_keyboard }
                      : {}),
                  }}
                  onChange={(keyboards) => {
                    const { default: defaultKeyboard, ...otherKeyboards } = keyboards;
                    setUIConfig({
                      ...uiConfig,
                      inline_keyboards: otherKeyboards,
                      default_inline_keyboard: defaultKeyboard || [],
                    });
                  }}
                />
                <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <p className="text-sm text-blue-700 dark:text-blue-400">
                    <strong>Tip:</strong> Keyboard named "main_menu" will be used for /start command. Keyboard named "default" will be used as fallback.
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-black/5 dark:border-white/5">
              <CardHeader>
                <CardTitle>Forms</CardTitle>
                <CardDescription>Create multi-step forms for collecting user input.</CardDescription>
              </CardHeader>
              <CardContent>
                <FormEditor
                  forms={uiConfig.forms || {}}
                  onChange={(forms) => setUIConfig({ ...uiConfig, forms })}
                />
              </CardContent>
            </Card>

            <div className="flex justify-end">
              <Button
                onClick={handleSaveUIConfig}
                isLoading={isSavingUIConfig}
                icon={<Save className="w-4 h-4" />}
              >
                Save UI Configuration
              </Button>
            </div>
          </div>
        )}

        {/* INTEGRATIONS TAB */}
        {activeTab === 'integrations' && (
          <div className="space-y-6 animate-in fade-in slide-in-from-left-4 duration-300">
          <Card className="border-black/5 dark:border-white/5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Webhook className="w-5 h-5 text-blue-500" />
                Telegram Integration
              </CardTitle>
              <CardDescription>Connect your bot to Telegram.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <h4 className="text-sm font-medium text-blue-800 dark:text-blue-300 mb-2">
                  How to get a token?
                </h4>
                <ol className="list-decimal list-inside text-sm text-blue-700 dark:text-blue-400 space-y-1">
                  <li>Open @BotFather in Telegram</li>
                  <li>Send command /newbot</li>
                  <li>Follow instructions to name your bot</li>
                  <li>Copy the API Token provided</li>
                </ol>
              </div>

              <Input
                label="Bot Token"
                type="password"
                placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
                value={formData.telegramToken}
                onChange={(e) => handleChange('telegramToken', e.target.value)}
                helperText="We encrypt this token securely."
              />

              {/* Bot Status Section */}
              {botId && botId !== 'new' && (
                <div className="space-y-4 pt-4 border-t border-black/5 dark:border-white/5">
                  <div>
                    <Label className="text-sm font-medium mb-2 block">Bot Status</Label>
                    {isLoadingStatus ? (
                      <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Loading status...
                      </div>
                    ) : botStatus ? (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <div
                            className={`w-2 h-2 rounded-full ${
                              botStatus.is_running
                                ? 'bg-green-500 animate-pulse'
                                : 'bg-gray-400'
                            }`}
                          />
                          <span className="text-sm font-medium">
                            {botStatus.is_running ? 'Running' : 'Stopped'}
                          </span>
                        </div>
                        {botStatus.last_heartbeat && (
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            Last activity: {new Date(botStatus.last_heartbeat).toLocaleString()}
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Status unavailable
                      </p>
                    )}
                  </div>

                  <div className="flex gap-2 flex-wrap">
                    <Button 
                      variant="secondary" 
                      className="flex-1 sm:flex-none"
                      onClick={handleTestTelegramConnection}
                      isLoading={isTestingConnection}
                      disabled={isTestingConnection || !formData.telegramToken}
                    >
                      {isTestingConnection ? 'Testing...' : 'Test Connection'}
                    </Button>
                    {formData.status === BotStatus.ACTIVE && botStatus?.is_running && (
                      <Button 
                        variant="secondary" 
                        className="flex-1 sm:flex-none"
                        onClick={handleRestartBot}
                        isLoading={isRestarting}
                        disabled={isRestarting || !botId || botId === 'new'}
                      >
                        {isRestarting ? 'Restarting...' : 'Restart Bot'}
                      </Button>
                    )}
                  </div>
                </div>
              )}

              {(!botId || botId === 'new') && (
                <div className="pt-4">
                  <Button 
                    variant="secondary" 
                    className="w-full sm:w-auto"
                    onClick={handleTestTelegramConnection}
                    isLoading={isTestingConnection}
                    disabled={isTestingConnection || !formData.telegramToken}
                  >
                    {isTestingConnection ? 'Testing...' : 'Test Connection'}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
          
          {/* Public API Keys Section */}
          {botId && botId !== 'new' && (
            <Card className="border-black/5 dark:border-white/5">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Key className="w-5 h-5 text-purple-500" />
                  Public API Keys
                </CardTitle>
                <CardDescription>
                  Create API keys for external services to access this bot.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* New API Key Creation */}
                {newAPIKey && (
                  <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 space-y-3">
                    <div className="flex items-center gap-2">
                      <Check className="w-5 h-5 text-green-600 dark:text-green-400" />
                      <h4 className="font-medium text-green-800 dark:text-green-300">
                        API Key Created Successfully!
                      </h4>
                    </div>
                    <div className="space-y-2">
                      <p className="text-sm text-green-700 dark:text-green-400">
                        Save this key securely. It will not be shown again.
                      </p>
                      <div className="flex items-center gap-2">
                        <code className="flex-1 px-3 py-2 bg-white dark:bg-gray-800 border border-green-300 dark:border-green-700 rounded text-sm font-mono break-all">
                          {newAPIKey}
                        </code>
                        <Button
                          variant="secondary"
                          size="sm"
                          icon={copiedKeyId === 'new' ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                          onClick={() => handleCopyAPIKey(newAPIKey, 'new')}
                        >
                          Copy
                        </Button>
                      </div>
                    </div>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setNewAPIKey(null)}
                    >
                      Close
                    </Button>
                  </div>
                )}
                
                {/* Create New Key Form */}
                {!newAPIKey && (
                  <div className="flex gap-2">
                    <Input
                      placeholder="API Key Name (e.g., Production, Development)"
                      value={newAPIKeyName}
                      onChange={(e) => setNewAPIKeyName(e.target.value)}
                      className="flex-1"
                    />
                    <Button
                      onClick={handleCreateAPIKey}
                      isLoading={isCreatingAPIKey}
                      disabled={!newAPIKeyName.trim() || isCreatingAPIKey}
                      icon={<Plus className="w-4 h-4" />}
                    >
                      Create Key
                    </Button>
                  </div>
                )}
                
                {/* API Keys List */}
                {isLoadingAPIKeys ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                  </div>
                ) : apiKeys.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    <Key className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>No API keys created yet</p>
                    <p className="text-sm mt-1">Create one to allow external services to access this bot</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {apiKeys.map((key) => (
                      <div
                        key={key.id}
                        className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900/50 border border-black/5 dark:border-white/5 rounded-lg"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{key.name}</span>
                            {key.is_active ? (
                              <span className="px-2 py-0.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded">
                                Active
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded">
                                Inactive
                              </span>
                            )}
                          </div>
                          <div className="mt-1 flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                            <code className="font-mono">{key.key_prefix}...</code>
                            <span>Created: {new Date(key.created_at).toLocaleDateString()}</span>
                            {key.last_used_at && (
                              <span>Last used: {new Date(key.last_used_at).toLocaleDateString()}</span>
                            )}
                          </div>
                        </div>
                        <Button
                          variant="icon"
                          size="sm"
                          onClick={() => handleDeleteAPIKey(key.id)}
                          className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* API Usage Info */}
                <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <p className="text-sm text-blue-700 dark:text-blue-400">
                    <strong>Usage:</strong> Include the API key in the <code className="px-1 py-0.5 bg-blue-100 dark:bg-blue-900/30 rounded">X-API-Key</code> header when making requests to <code className="px-1 py-0.5 bg-blue-100 dark:bg-blue-900/30 rounded">/api/v1/public/chat/</code>
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
          </div>
        )}
      </div>
    </div>
  );
};

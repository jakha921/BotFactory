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
  Terminal,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Textarea } from '../components/ui/Textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Tabs } from '../components/ui/Tabs';
import { Label } from '../components/ui/Label';
import {
  Bot as BotType,
  BotStatus,
  DeliveryMode,
  UIConfig,
  InlineKeyboardButton,
  BotCommand,
  ResponseType,
} from '../types';
import { api } from '../services/api';
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
  { id: 'commands', label: 'Commands' },
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

  // Webhook State
  const [webhookInfo, setWebhookInfo] = useState<{
    delivery_mode: DeliveryMode;
    webhook_url: string | null;
    has_custom_url: boolean;
    webhook_secret_set: boolean;
    telegram_webhook_info: {
      url: string;
      has_custom_certificate: boolean;
      pending_update_count: number;
      last_error_date: number | null;
      last_error_message: string | null;
      max_connections: number | null;
      allowed_updates: string[] | null;
    } | null;
  } | null>(null);
  const [isLoadingWebhook, setIsLoadingWebhook] = useState(false);
  const [isSettingWebhook, setIsSettingWebhook] = useState(false);
  const [isDeletingWebhook, setIsDeletingWebhook] = useState(false);

  // UI Config State
  const [uiConfig, setUIConfig] = useState<UIConfig>({
    inline_keyboards: {},
    forms: {},
    welcome_message: '',
    help_message: '',
    default_inline_keyboard: [],
  });

  // Commands State
  const [commands, setCommands] = useState<BotCommand[]>([]);
  const [isLoadingCommands, setIsLoadingCommands] = useState(false);
  const [isSavingCommand, setIsSavingCommand] = useState(false);
  const [editingCommand, setEditingCommand] = useState<Partial<BotCommand> | null>(null);

  // AI Models State
  const [aiModels, setAiModels] = useState<Array<{
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
  }>>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(false);

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
    rag_enabled: true,
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
        rag_enabled: true,
      });
      setUIConfig({
        inline_keyboards: {},
        forms: {},
        welcome_message: '',
        help_message: '',
        default_inline_keyboard: [],
      });
      setApiKeys([]);
      setCommands([]);
    }
  }, [botId]);

  // Load API keys when integrations tab is active
  useEffect(() => {
    if (activeTab === 'integrations' && botId && botId !== 'new') {
      loadAPIKeys();
      loadWebhookInfo();
    }
  }, [activeTab, botId]);

  // Load commands when commands tab is active
  useEffect(() => {
    if (activeTab === 'commands' && botId && botId !== 'new') {
      loadCommands();
    }
  }, [activeTab, botId]);

  // Load AI models on mount
  useEffect(() => {
    const loadModels = async () => {
      try {
        setIsLoadingModels(true);
        const response = await api.ai.getModels();
        setAiModels(response.models || []);
      } catch (error) {
        console.error('[BotSettings] Failed to load AI models:', error);
        // Non-critical error, continue without models list
      } finally {
        setIsLoadingModels(false);
      }
    };
    loadModels();
  }, []);

  // Update model when provider changes
  useEffect(() => {
    if (!aiModels.length) return;

    const providerModels = aiModels.filter(m => m.provider === formData.provider);
    if (providerModels.length > 0) {
      // Check if current model is valid for the new provider
      const currentModelValid = providerModels.some(m => m.model_id === formData.model);
      if (!currentModelValid) {
        // Set to default model for this provider, or first available
        const defaultModel = providerModels.find(m => m.is_default) || providerModels[0];
        handleChange('model', defaultModel.model_id);
      }
    }
  }, [formData.provider, aiModels]);

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

  // Webhook functions
  const loadWebhookInfo = async () => {
    if (!botId || botId === 'new') return;
    setIsLoadingWebhook(true);
    try {
      const info = await api.bots.getWebhookInfo(botId);
      setWebhookInfo(info);
    } catch (error: any) {
      console.error('[BotSettings] Failed to load webhook info:', error);
      toast.error(error?.message || 'Failed to load webhook info');
    } finally {
      setIsLoadingWebhook(false);
    }
  };

  const handleSetWebhook = async () => {
    if (!botId || botId === 'new') {
      toast.error('Please save the bot first');
      return;
    }

    setIsSettingWebhook(true);
    try {
      const result = await api.bots.setWebhook(botId);
      if (result.success) {
        toast.success(`Webhook mode enabled. URL: ${result.webhook_url}`);
        await loadWebhookInfo();
      } else {
        toast.error(result.error || 'Failed to enable webhook mode');
      }
    } catch (error: any) {
      console.error('[BotSettings] Failed to set webhook:', error);
      toast.error(error?.message || 'Failed to enable webhook mode');
    } finally {
      setIsSettingWebhook(false);
    }
  };

  const handleDeleteWebhook = async () => {
    if (!botId || botId === 'new') {
      toast.error('Please save the bot first');
      return;
    }

    if (!confirm('Are you sure you want to disable webhook mode? The bot will switch to polling mode.')) {
      return;
    }

    setIsDeletingWebhook(true);
    try {
      const result = await api.bots.deleteWebhook(botId);
      if (result.success) {
        toast.success(result.message || 'Webhook mode disabled. Bot will use polling mode.');
        await loadWebhookInfo();
        // Also update local bot state
        handleChange('deliveryMode', DeliveryMode.POLLING);
      } else {
        toast.error('Failed to disable webhook mode');
      }
    } catch (error: any) {
      console.error('[BotSettings] Failed to delete webhook:', error);
      toast.error(error?.message || 'Failed to disable webhook mode');
    } finally {
      setIsDeletingWebhook(false);
    }
  };

  const loadCommands = async () => {
    if (!botId || botId === 'new') return;
    setIsLoadingCommands(true);
    try {
      const cmds = await api.commands.list(botId);
      setCommands(cmds);
    } catch (error: any) {
      console.error('[BotSettings] Failed to load commands:', error);
      toast.error(error?.message || 'Failed to load commands');
    } finally {
      setIsLoadingCommands(false);
    }
  };

  const handleSaveCommand = async () => {
    if (!botId || botId === 'new') {
      toast.error('Please save the bot first');
      return;
    }

    if (!editingCommand?.name || !editingCommand.name.trim()) {
      toast.error('Command name is required');
      return;
    }

    // Remove / prefix if present
    const commandName = editingCommand.name.replace(/^\//, '');

    if (!/^[a-z0-9_]+$/.test(commandName)) {
      toast.error('Command name must contain only lowercase letters, numbers, and underscores');
      return;
    }

    setIsSavingCommand(true);
    try {
      const commandData = {
        ...editingCommand,
        name: commandName,
        bot: botId,
      };

      if (editingCommand.id) {
        await api.commands.update(editingCommand.id, commandData);
        toast.success('Command updated successfully');
      } else {
        await api.commands.create(commandData as any);
        toast.success('Command created successfully');
      }

      setEditingCommand(null);
      await loadCommands();
    } catch (error: any) {
      console.error('[BotSettings] Failed to save command:', error);
      toast.error(error?.message || 'Failed to save command');
    } finally {
      setIsSavingCommand(false);
    }
  };

  const handleDeleteCommand = async (commandId: string) => {
    if (!confirm('Are you sure you want to delete this command?')) {
      return;
    }

    try {
      await api.commands.delete(commandId);
      await loadCommands();
      toast.success('Command deleted successfully');
    } catch (error: any) {
      console.error('[BotSettings] Failed to delete command:', error);
      toast.error(error?.message || 'Failed to delete command');
    }
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
      // Use backend API instead of direct Gemini call
      const response = await api.ai.improveInstruction(
        formData.systemInstruction,
        botId || undefined
      );

      if (response.limit_reached) {
        toast.error(`AI limit reached: ${response.message}`);
        return;
      }

      if (response.text) {
        handleChange('systemInstruction', response.text);
        toast.success('System instruction improved successfully');
      }
    } catch (error: any) {
      if (error?.status === 429) {
        toast.error(`AI limit reached: ${error.message}`);
      } else {
        const errorMessage = error?.message || 'Failed to improve instruction';
        toast.error(errorMessage);
      }
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
          <div className="space-y-6 animate-in fade-in slide-in-from-left-4 duration-300">
            {/* RAG Settings */}
            <Card className="border-black/5 dark:border-white/5">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-emerald-500" />
                  RAG Settings
                </CardTitle>
                <CardDescription>
                  Configure how your bot uses the knowledge base for responses.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900/50 border border-black/5 dark:border-white/5 rounded-lg">
                  <div className="flex-1">
                    <Label htmlFor="rag-enabled" className="text-base font-medium">
                      Enable Knowledge Base (RAG)
                    </Label>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      When enabled, your bot will search uploaded documents and text snippets to provide more accurate, context-aware responses.
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      id="rag-enabled"
                      className="sr-only peer"
                      checked={formData.rag_enabled ?? true}
                      onChange={(e) => handleChange('rag_enabled', e.target.checked)}
                    />
                    <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>

                {formData.rag_enabled !== false && (
                  <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                    <p className="text-sm text-blue-700 dark:text-blue-400">
                      <strong>Active:</strong> Your bot will use uploaded documents and text snippets to enhance responses.
                    </p>
                  </div>
                )}

                {formData.rag_enabled === false && (
                  <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                    <p className="text-sm text-amber-700 dark:text-amber-400">
                      <strong>Disabled:</strong> Your bot will rely only on its training data and system instructions.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            <KnowledgeSettings botId={botId} />
          </div>
        )}

        {/* COMMANDS TAB */}
        {activeTab === 'commands' && (
          <div className="space-y-6 animate-in fade-in slide-in-from-left-4 duration-300">
            <Card className="border-black/5 dark:border-white/5">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Terminal className="w-5 h-5 text-purple-500" />
                      Bot Commands
                    </CardTitle>
                    <CardDescription>
                      Configure dynamic bot commands that users can trigger.
                    </CardDescription>
                  </div>
                  <Button
                    onClick={() => setEditingCommand({
                      name: '',
                      description: '',
                      response_type: ResponseType.TEXT,
                      text_response: '',
                      ai_prompt_override: '',
                      form_id: '',
                      menu_config: [],
                      is_active: true,
                      priority: 0,
                    })}
                    icon={<Plus className="w-4 h-4" />}
                    disabled={!botId || botId === 'new'}
                  >
                    Add Command
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {isLoadingCommands ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                  </div>
                ) : commands.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    <Terminal className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>No commands configured yet</p>
                    <p className="text-sm mt-1">Create commands to let users interact with your bot</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {commands.map((command) => (
                      <div
                        key={command.id}
                        className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900/50 border border-black/5 dark:border-white/5 rounded-lg hover:border-purple-200 dark:hover:border-purple-800 transition-colors"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <code className="px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded text-sm font-mono">
                              /{command.name}
                            </code>
                            {command.is_active ? (
                              <span className="px-2 py-0.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded">
                                Active
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded">
                                Inactive
                              </span>
                            )}
                            <span className="px-2 py-0.5 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded capitalize">
                              {command.response_type}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {command.description || 'No description'}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="icon"
                            size="sm"
                            onClick={() => setEditingCommand(command)}
                            className="text-gray-600 dark:text-gray-400 hover:text-primary"
                          >
                            <Settings2 className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="icon"
                            size="sm"
                            onClick={() => handleDeleteCommand(command.id)}
                            className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Edit Command Modal */}
            {editingCommand && (
              <Card className="border-purple-200 dark:border-purple-800">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{editingCommand.id ? 'Edit Command' : 'New Command'}</span>
                    <Button
                      variant="icon"
                      size="sm"
                      onClick={() => setEditingCommand(null)}
                    >
                      ✕
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <Input
                      label="Command Name"
                      placeholder="e.g., start, help, about"
                      value={editingCommand.name?.replace(/^\//, '') || ''}
                      onChange={(e) => setEditingCommand({ ...editingCommand, name: e.target.value })}
                      helperText="Without / prefix. Use lowercase letters, numbers, and underscores only."
                      required
                    />
                    <Input
                      label="Priority"
                      type="number"
                      placeholder="0"
                      value={editingCommand.priority || 0}
                      onChange={(e) => setEditingCommand({ ...editingCommand, priority: parseInt(e.target.value) || 0 })}
                      helperText="Higher priority commands are shown first"
                    />
                  </div>

                  <Textarea
                    label="Description"
                    placeholder="Brief description of what this command does"
                    value={editingCommand.description || ''}
                    onChange={(e) => setEditingCommand({ ...editingCommand, description: e.target.value })}
                    rows={2}
                  />

                  <div className="space-y-1.5">
                    <Label>Response Type</Label>
                    <select
                      className="block w-full rounded-lg border px-3 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/20 bg-white dark:bg-white/5 border-black/10 dark:border-white/10 text-gray-900 dark:text-gray-100 sm:text-sm"
                      value={editingCommand.response_type || ResponseType.TEXT}
                      onChange={(e) => setEditingCommand({ ...editingCommand, response_type: e.target.value as ResponseType })}
                    >
                      <option value={ResponseType.TEXT}>Text - Static message</option>
                      <option value={ResponseType.AI}>AI - AI-generated response</option>
                      <option value={ResponseType.FORM}>Form - Multi-step form</option>
                      <option value={ResponseType.MENU}>Menu - Inline keyboard</option>
                    </select>
                  </div>

                  {editingCommand.response_type === ResponseType.TEXT && (
                    <Textarea
                      label="Text Response"
                      placeholder="The message to send when this command is triggered"
                      value={editingCommand.text_response || ''}
                      onChange={(e) => setEditingCommand({ ...editingCommand, text_response: e.target.value })}
                      rows={4}
                      helperText="Supports plain text. Markdown formatting is available."
                    />
                  )}

                  {editingCommand.response_type === ResponseType.AI && (
                    <Textarea
                      label="AI Prompt Override"
                      placeholder="Override the default system instruction for this command"
                      value={editingCommand.ai_prompt_override || ''}
                      onChange={(e) => setEditingCommand({ ...editingCommand, ai_prompt_override: e.target.value })}
                      rows={4}
                      helperText="Leave empty to use the bot's default system instruction"
                    />
                  )}

                  {editingCommand.response_type === ResponseType.FORM && (
                    <Input
                      label="Form ID"
                      placeholder="e.g., feedback_form, survey"
                      value={editingCommand.form_id || ''}
                      onChange={(e) => setEditingCommand({ ...editingCommand, form_id: e.target.value })}
                      helperText="The form identifier to trigger"
                    />
                  )}

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="command-active"
                      checked={editingCommand.is_active ?? true}
                      onChange={(e) => setEditingCommand({ ...editingCommand, is_active: e.target.checked })}
                      className="rounded border-gray-300 text-primary focus:ring-primary"
                    />
                    <Label htmlFor="command-active" className="cursor-pointer">
                      Active (command is available to users)
                    </Label>
                  </div>

                  <div className="flex justify-end gap-2 pt-4 border-t border-black/5 dark:border-white/5">
                    <Button
                      variant="secondary"
                      onClick={() => setEditingCommand(null)}
                      disabled={isSavingCommand}
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleSaveCommand}
                      isLoading={isSavingCommand}
                      icon={<Save className="w-4 h-4" />}
                    >
                      {editingCommand.id ? 'Save Changes' : 'Create Command'}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
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
                    {isLoadingModels ? (
                      <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 py-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Loading models...
                      </div>
                    ) : (
                      <select
                        className="block w-full rounded-lg border px-3 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/20 bg-white dark:bg-white/5 border-black/10 dark:border-white/10 text-gray-900 dark:text-gray-100 sm:text-sm"
                        value={formData.model}
                        onChange={(e) => handleChange('model', e.target.value)}
                      >
                        {(() => {
                          const providerModels = aiModels.filter(m => m.provider === formData.provider);
                          if (providerModels.length === 0) {
                            return (
                              <option value={formData.model} disabled>
                                {formData.model || 'Select a model'}
                              </option>
                            );
                          }
                          return providerModels.map((model) => (
                            <option key={model.model_id} value={model.model_id}>
                              {model.display_name} {model.supports_thinking && '🧠'} {model.supports_vision && '👁️'}
                            </option>
                          ));
                        })()}
                      </select>
                    )}
                  </div>
                </div>

                {/* Model Info Display */}
                {(() => {
                  const selectedModel = aiModels.find(m => m.model_id === formData.model);
                  if (!selectedModel) return null;

                  // Get model cost info from factory
                  const modelCostInfo = (() => {
                    if (selectedModel.provider === 'gemini') {
                      const geminiModels = {
                        'gemini-2.5-flash': { input: 0.000075, output: 0.0003 },
                        'gemini-2.5-flash-lite': { input: 0.0000375, output: 0.00015 },
                        'gemini-3-pro-preview': { input: 0.000125, output: 0.0005 },
                        'gemini-1.5-pro': { input: 0.00175, output: 0.0021 },
                        'gemini-1.5-flash': { input: 0.000075, output: 0.00015 },
                      };
                      return geminiModels[selectedModel.model_id as keyof typeof geminiModels];
                    } else if (selectedModel.provider === 'openai') {
                      const openaiModels = {
                        'gpt-4o': { input: 0.0025, output: 0.01 },
                        'gpt-4o-mini': { input: 0.00015, output: 0.0006 },
                        'gpt-4-turbo': { input: 0.01, output: 0.03 },
                        'gpt-4': { input: 0.03, output: 0.06 },
                        'gpt-3.5-turbo': { input: 0.0005, output: 0.0015 },
                      };
                      return openaiModels[selectedModel.model_id as keyof typeof openaiModels];
                    } else if (selectedModel.provider === 'anthropic') {
                      const anthropicModels = {
                        'claude-4-opus-20250114': { input: 0.015, output: 0.075 },
                        'claude-3.5-sonnet-20241022': { input: 0.003, output: 0.015 },
                        'claude-3.5-sonnet-20240620': { input: 0.003, output: 0.015 },
                        'claude-3-haiku-20240307': { input: 0.00025, output: 0.00125 },
                        'claude-3-opus-20240229': { input: 0.015, output: 0.075 },
                      };
                      return anthropicModels[selectedModel.model_id as keyof typeof anthropicModels];
                    }
                    return null;
                  })();

                  return (
                    <div className="p-4 bg-gray-50 dark:bg-gray-900/50 border border-black/5 dark:border-white/5 rounded-lg space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          {selectedModel.display_name}
                        </span>
                        <div className="flex items-center gap-2">
                          {selectedModel.supports_thinking && (
                            <span className="px-2 py-0.5 text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full flex items-center gap-1">
                              <Brain className="w-3 h-3" />
                              Thinking
                            </span>
                          )}
                          {selectedModel.supports_vision && (
                            <span className="px-2 py-0.5 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full">
                              Vision
                            </span>
                          )}
                        </div>
                      </div>
                      {modelCostInfo && (
                        <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                          <div className="flex justify-between">
                            <span>Input:</span>
                            <span className="font-mono">${modelCostInfo.input.toFixed(5)}/1K tokens</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Output:</span>
                            <span className="font-mono">${modelCostInfo.output.toFixed(5)}/1K tokens</span>
                          </div>
                          <div className="pt-1 border-t border-black/5 dark:border-white/5 mt-2">
                            <span className="text-gray-500">
                              Est. cost per 1K tokens: ${((modelCostInfo.input + modelCostInfo.output) / 2).toFixed(5)}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })()}

                {/* Thinking Budget Control - Only for Supported Models */}
                {(() => {
                  const selectedModel = aiModels.find(m => m.model_id === formData.model);
                  return selectedModel?.supports_thinking;
                })() && (
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
                      Allocate tokens for advanced reasoning. Higher values enable deeper reasoning but increase response time.
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
                              className={`w-2 h-2 rounded-full ${botStatus.is_running
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

            {/* Webhook Management Section */}
            {botId && botId !== 'new' && (
              <Card className="border-black/5 dark:border-white/5">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Terminal className="w-5 h-5 text-orange-500" />
                    Webhook Settings
                  </CardTitle>
                  <CardDescription>
                    Configure how your bot receives messages from Telegram.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {isLoadingWebhook ? (
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Loading webhook info...
                    </div>
                  ) : webhookInfo ? (
                    <>
                      {/* Current Mode Display */}
                      <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900/50 border border-black/5 dark:border-white/5 rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            webhookInfo.delivery_mode === 'webhook'
                              ? 'bg-green-100 dark:bg-green-900/30'
                              : 'bg-blue-100 dark:bg-blue-900/30'
                          }`}>
                            {webhookInfo.delivery_mode === 'webhook' ? (
                              <Webhook className="w-5 h-5 text-green-600 dark:text-green-400" />
                            ) : (
                              <Terminal className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                            )}
                          </div>
                          <div>
                            <div className="font-medium text-gray-900 dark:text-gray-100">
                              {webhookInfo.delivery_mode === 'webhook' ? 'Webhook Mode' : 'Polling Mode'}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                              {webhookInfo.delivery_mode === 'webhook'
                                ? 'Messages delivered via webhook'
                                : 'Bot service polls for updates'
                              }
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          {formData.status === BotStatus.ACTIVE && (
                            <>
                              {webhookInfo.delivery_mode === 'webhook' ? (
                                <Button
                                  variant="secondary"
                                  size="sm"
                                  onClick={handleDeleteWebhook}
                                  isLoading={isDeletingWebhook}
                                  disabled={isDeletingWebhook}
                                >
                                  Switch to Polling
                                </Button>
                              ) : (
                                <Button
                                  variant="primary"
                                  size="sm"
                                  onClick={handleSetWebhook}
                                  isLoading={isSettingWebhook}
                                  disabled={isSettingWebhook}
                                >
                                  Enable Webhook
                                </Button>
                              )}
                            </>
                          )}
                        </div>
                      </div>

                      {/* Webhook URL Info */}
                      {webhookInfo.delivery_mode === 'webhook' && (
                        <div className="space-y-4">
                          <div>
                            <Label>Webhook URL</Label>
                            <div className="mt-1.5 p-3 bg-gray-100 dark:bg-gray-800 border border-black/10 dark:border-white/10 rounded-lg">
                              <code className="text-xs break-all">
                                {webhookInfo.webhook_url || 'Using default URL'}
                              </code>
                            </div>
                          </div>

                          {webhookInfo.telegram_webhook_info && (
                            <div className="p-4 bg-gray-50 dark:bg-gray-900/50 border border-black/5 dark:border-white/5 rounded-lg space-y-2">
                              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                Telegram Webhook Status
                              </h4>
                              <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                                <div className="flex justify-between">
                                  <span>Status:</span>
                                  <span className={webhookInfo.telegram_webhook_info.url ? 'text-green-600 dark:text-green-400' : 'text-gray-500'}>
                                    {webhookInfo.telegram_webhook_info.url ? 'Connected' : 'Not connected'}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Pending updates:</span>
                                  <span className={webhookInfo.telegram_webhook_info.pending_update_count > 0 ? 'text-amber-600 dark:text-amber-400' : 'text-gray-500'}>
                                    {webhookInfo.telegram_webhook_info.pending_update_count}
                                  </span>
                                </div>
                                {webhookInfo.telegram_webhook_info.last_error_message && (
                                  <div className="text-red-600 dark:text-red-400">
                                    Error: {webhookInfo.telegram_webhook_info.last_error_message}
                                  </div>
                                )}
                              </div>
                            </div>
                          )}

                          {webhookInfo.has_custom_url && (
                            <div className="p-3 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg">
                              <p className="text-sm text-purple-700 dark:text-purple-400">
                                <strong>Custom URL:</strong> This bot uses a custom webhook URL.
                              </p>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Polling Mode Info */}
                      {webhookInfo.delivery_mode === 'polling' && (
                        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                          <p className="text-sm text-blue-700 dark:text-blue-400">
                            <strong>Polling Mode:</strong> Bot service polls Telegram for updates.
                            Requires the bot service to be running. Use this for development or
                            if webhook mode is not available.
                          </p>
                        </div>
                      )}

                      {/* Info Card */}
                      <div className="p-4 bg-gray-50 dark:bg-gray-900/50 border border-black/5 dark:border-white/5 rounded-lg">
                        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                          Webhook vs Polling
                        </h4>
                        <div className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
                          <p>• <strong>Webhook:</strong> Instant message delivery, better for production, requires HTTPS</p>
                          <p>• <strong>Polling:</strong> Bot polls for updates, works everywhere, uses more resources</p>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-4 text-gray-500 dark:text-gray-400">
                      Unable to load webhook information
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

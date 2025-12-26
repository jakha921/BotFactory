import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import {
  User,
  Mail,
  Key,
  Bell,
  Shield,
  Save,
  Copy,
  Plus,
  Trash2,
  Loader2,
  Check,
  Smartphone,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Switch } from '../components/ui/Switch';
import { Label } from '../components/ui/Label';
import { useThemeStore } from '../store/useThemeStore';
import { useAppStore } from '../store/useAppStore';
import { useAuthStore } from '../store/useAuthStore';
import { cn } from '../utils';
import { motion, AnimatePresence } from 'framer-motion';

type SettingsTab = 'profile' | 'api_keys' | 'security' | 'notifications';

export const Settings: React.FC = () => {
  console.log('[Settings] Component rendered');
  const { theme, setTheme } = useThemeStore();
  const { apiKeys, addApiKey, deleteApiKey } = useAppStore();
  const { user, updateUser } = useAuthStore();

  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  // Local State for Profile Form
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    telegramId: user?.telegramId ? String(user.telegramId) : '',
  });

  // Mock Notification Preferences
  const [notificationPrefs, setNotificationPrefs] = useState({
    email: true,
    push: false,
    weeklyDigest: true,
  });

  // API Key Form State
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyValue, setNewKeyValue] = useState('');
  const [isAddingKey, setIsAddingKey] = useState(false);

  // Security State
  const [passwords, setPasswords] = useState({ current: '', new: '', confirm: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [twoFactor, setTwoFactor] = useState(false);

  // Update formData when user changes
  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || '',
        email: user.email || '',
        telegramId: user.telegramId ? String(user.telegramId) : '',
      });
    }
  }, [user]);

  const handleSave = async () => {
    setIsLoading(true);
    setIsSuccess(false);

    try {
      // Update user profile (including telegramId)
      await updateUser({
        name: formData.name,
        email: formData.email,
        telegramId: formData.telegramId || undefined,
      });

      setIsSuccess(true);
      setTimeout(() => setIsSuccess(false), 2000);
    } catch (error: any) {
      console.error('[Settings] Failed to save profile:', error);
      toast.error(error?.message || 'Failed to save profile');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleNotification = (key: keyof typeof notificationPrefs) => {
    setNotificationPrefs((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleCopyKey = (text: string) => {
    navigator.clipboard.writeText(text);
    // Simple toast/alert replacement
    const el = document.createElement('div');
    el.textContent = 'Copied to clipboard';
    el.className =
      'fixed bottom-4 right-4 bg-gray-800 text-white px-4 py-2 rounded-lg text-sm z-50 animate-in fade-in slide-in-from-bottom-2';
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 2000);
  };

  const handleDeleteKey = (id: string) => {
    if (confirm('Are you sure? This action cannot be undone.')) {
      deleteApiKey(id);
    }
  };

  const handleCreateKey = () => {
    if (!newKeyName || !newKeyValue) return;

    const newKey = {
      id: Date.now().toString(),
      name: newKeyName,
      key: newKeyValue,
      provider: 'openai' as const, // Default or add selector
      created: new Date().toLocaleDateString('en-CA'),
    };
    addApiKey(newKey);
    setNewKeyName('');
    setNewKeyValue('');
    setIsAddingKey(false);
  };

  const maskKey = (key: string) => {
    if (key.length <= 8) return '********';
    return `${key.substring(0, 3)}...${key.substring(key.length - 4)}`;
  };

  const NavButton = ({
    tab,
    icon: Icon,
    label,
  }: {
    tab: SettingsTab;
    icon: any;
    label: string;
  }) => (
    <button
      onClick={() => setActiveTab(tab)}
      className={cn(
        'w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors relative',
        activeTab === tab
          ? 'text-primary dark:text-primary-light'
          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-white/5'
      )}
    >
      {activeTab === tab && (
        <motion.div
          layoutId="settingsTab"
          className="absolute inset-0 bg-primary/10 dark:bg-primary/20 rounded-lg"
        />
      )}
      <span className="relative z-10 flex items-center gap-3">
        <Icon className="w-4 h-4" /> {label}
      </span>
    </button>
  );

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Account Settings</h1>
          <p className="text-gray-500 dark:text-gray-400">Manage your profile and preferences.</p>
        </div>
        <Button
          onClick={handleSave}
          disabled={isLoading}
          className={cn('min-w-[140px]', isSuccess && 'bg-emerald-500 hover:bg-emerald-600')}
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : isSuccess ? (
            <Check className="w-4 h-4 mr-2" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          {isLoading ? 'Saving...' : isSuccess ? 'Saved!' : 'Save Changes'}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Navigation Sidebar */}
        <div className="lg:col-span-1 space-y-1">
          <nav className="space-y-1">
            <NavButton tab="profile" icon={User} label="Profile" />
            <NavButton tab="api_keys" icon={Key} label="API Keys" />
            <NavButton tab="security" icon={Shield} label="Security" />
            <NavButton tab="notifications" icon={Bell} label="Notifications" />
          </nav>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          <AnimatePresence mode="wait">
            {activeTab === 'profile' && (
              <motion.div
                key="profile"
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.2 }}
                className="space-y-6"
              >
                <Card className="border-black/5 dark:border-white/5">
                  <CardHeader>
                    <CardTitle>Profile Information</CardTitle>
                    <CardDescription>Update your personal details.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="flex items-center gap-6">
                      <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-gray-200 to-gray-100 dark:from-gray-700 dark:to-gray-600 border-2 border-white dark:border-gray-800 shadow-sm flex items-center justify-center text-2xl font-bold text-gray-500 dark:text-gray-300">
                        {formData.name.substring(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <Button variant="secondary" size="sm">
                          Change Avatar
                        </Button>
                        <p className="text-xs text-gray-500 mt-2">
                          JPG, GIF or PNG. Max size of 800K.
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <Input
                        label="Full Name"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      />
                      <Input
                        label="Email Address"
                        value={formData.email}
                        startIcon={<Mail className="w-4 h-4" />}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      />
                    </div>

                    <Input
                      label="Telegram User ID"
                      type="number"
                      placeholder="e.g. 256841597"
                      value={formData.telegramId}
                      onChange={(e) => setFormData({ ...formData, telegramId: e.target.value })}
                      helperText="Your Telegram User ID. Add this to receive notifications when testing bot connections. You can get your ID from @userinfobot in Telegram."
                      startIcon={<Smartphone className="w-4 h-4" />}
                    />
                  </CardContent>
                </Card>

                <Card className="border-black/5 dark:border-white/5">
                  <CardHeader>
                    <CardTitle>Appearance</CardTitle>
                    <CardDescription>Customize the look and feel.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <Label className="mb-0">Theme Preference</Label>
                      <div className="flex gap-2 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
                        <button
                          onClick={() => setTheme('light')}
                          className={cn(
                            'px-3 py-1.5 text-sm rounded-md transition-colors',
                            theme === 'light'
                              ? 'bg-white shadow-sm text-gray-900'
                              : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
                          )}
                        >
                          Light
                        </button>
                        <button
                          onClick={() => setTheme('dark')}
                          className={cn(
                            'px-3 py-1.5 text-sm rounded-md transition-colors',
                            theme === 'dark'
                              ? 'bg-gray-700 shadow-sm text-white'
                              : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
                          )}
                        >
                          Dark
                        </button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {activeTab === 'api_keys' && (
              <motion.div
                key="api_keys"
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.2 }}
              >
                <Card className="border-black/5 dark:border-white/5">
                  <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                      <CardTitle>Global API Keys</CardTitle>
                      <CardDescription>
                        Securely manage keys for Gemini, OpenAI, and Anthropic.
                      </CardDescription>
                    </div>
                    {!isAddingKey && (
                      <Button
                        size="sm"
                        variant="secondary"
                        icon={<Plus className="w-4 h-4" />}
                        onClick={() => setIsAddingKey(true)}
                      >
                        Create New Key
                      </Button>
                    )}
                  </CardHeader>
                  <CardContent>
                    {isAddingKey && (
                      <div className="mb-6 p-4 bg-gray-50 dark:bg-white/5 rounded-xl border border-black/5 dark:border-white/5 animate-in fade-in slide-in-from-top-2">
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                          Add New Key
                        </h4>
                        <div className="grid gap-4">
                          <Input
                            placeholder="Key Name (e.g. Production Gemini)"
                            value={newKeyName}
                            onChange={(e) => setNewKeyName(e.target.value)}
                            autoFocus
                          />
                          <Input
                            type="password"
                            placeholder="sk-..."
                            value={newKeyValue}
                            onChange={(e) => setNewKeyValue(e.target.value)}
                          />
                          <div className="flex justify-end gap-2">
                            <Button variant="ghost" size="sm" onClick={() => setIsAddingKey(false)}>
                              Cancel
                            </Button>
                            <Button
                              size="sm"
                              onClick={handleCreateKey}
                              disabled={!newKeyName || !newKeyValue}
                            >
                              Save Key
                            </Button>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="space-y-4">
                      {apiKeys.length === 0 && !isAddingKey && (
                        <div className="text-center py-8 text-gray-500">
                          No API keys found. Add one to get started.
                        </div>
                      )}
                      {apiKeys.map((key) => (
                        <div
                          key={key.id}
                          className="flex items-center justify-between p-4 bg-gray-50 dark:bg-white/5 rounded-xl border border-black/5 dark:border-white/5 hover:border-primary/30 transition-colors group"
                        >
                          <div className="flex items-center gap-4">
                            <div className="p-2.5 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-black/5 dark:border-white/5">
                              <Key className="w-5 h-5 text-gray-500" />
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-gray-900 dark:text-white">
                                {key.name}
                              </p>
                              <div className="flex items-center gap-2 mt-0.5">
                                <code className="text-xs font-mono text-gray-500 bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded">
                                  {maskKey(key.key)}
                                </code>
                                <span className="text-xs text-gray-400">
                                  • Created {key.created}
                                </span>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button
                              variant="icon"
                              size="md"
                              title="Copy"
                              onClick={() => handleCopyKey(key.key)}
                            >
                              <Copy className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="icon"
                              size="md"
                              className="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                              onClick={() => handleDeleteKey(key.id)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {activeTab === 'security' && (
              <motion.div
                key="security"
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.2 }}
                className="space-y-6"
              >
                <Card className="border-black/5 dark:border-white/5">
                  <CardHeader>
                    <CardTitle>Password</CardTitle>
                    <CardDescription>Change your account password.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="relative">
                      <Input
                        label="Current Password"
                        type={showPassword ? 'text' : 'password'}
                        value={passwords.current}
                        onChange={(e) => setPasswords({ ...passwords, current: e.target.value })}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <Input
                        label="New Password"
                        type={showPassword ? 'text' : 'password'}
                        value={passwords.new}
                        onChange={(e) => setPasswords({ ...passwords, new: e.target.value })}
                      />
                      <Input
                        label="Confirm Password"
                        type={showPassword ? 'text' : 'password'}
                        value={passwords.confirm}
                        onChange={(e) => setPasswords({ ...passwords, confirm: e.target.value })}
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="showPass"
                        checked={showPassword}
                        onChange={(e) => setShowPassword(e.target.checked)}
                        className="rounded border-gray-300 text-primary focus:ring-primary"
                      />
                      <Label htmlFor="showPass" className="mb-0 cursor-pointer">
                        Show Passwords
                      </Label>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-black/5 dark:border-white/5">
                  <CardHeader>
                    <CardTitle>Two-Factor Authentication</CardTitle>
                    <CardDescription>
                      Add an extra layer of security to your account.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-white/5 rounded-xl border border-black/5 dark:border-white/5">
                      <div className="flex items-center gap-4">
                        <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full text-blue-600 dark:text-blue-400">
                          <Shield className="w-6 h-6" />
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900 dark:text-white">
                            Authenticator App
                          </p>
                          <p className="text-sm text-gray-500">
                            Use an app like Google Authenticator to generate verification codes.
                          </p>
                        </div>
                      </div>
                      <Switch checked={twoFactor} onCheckedChange={setTwoFactor} />
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {activeTab === 'notifications' && (
              <motion.div
                key="notifications"
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.2 }}
              >
                <Card className="border-black/5 dark:border-white/5">
                  <CardHeader>
                    <CardTitle>Notifications</CardTitle>
                    <CardDescription>Control how we communicate with you.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm text-gray-900 dark:text-white">
                          Email Alerts
                        </p>
                        <p className="text-xs text-gray-500">
                          Receive updates about your bot's status.
                        </p>
                      </div>
                      <Switch
                        checked={notificationPrefs.email}
                        onCheckedChange={() => toggleNotification('email')}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm text-gray-900 dark:text-white">
                          Push Notifications
                        </p>
                        <p className="text-xs text-gray-500">
                          Get real-time alerts in your browser.
                        </p>
                      </div>
                      <Switch
                        checked={notificationPrefs.push}
                        onCheckedChange={() => toggleNotification('push')}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm text-gray-900 dark:text-white">
                          Weekly Digest
                        </p>
                        <p className="text-xs text-gray-500">Summary of your bot's performance.</p>
                      </div>
                      <Switch
                        checked={notificationPrefs.weeklyDigest}
                        onCheckedChange={() => toggleNotification('weeklyDigest')}
                      />
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}

          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

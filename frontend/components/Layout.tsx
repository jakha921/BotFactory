import React, { useEffect, useState } from 'react';
import {
  LayoutDashboard,
  Bot,
  MessageSquare,
  Settings,
  CreditCard,
  Users,
  Menu,
  X,
  Bell,
  LogOut,
  Moon,
  Sun,
  ChevronRight,
  Library,
  Activity,
  BarChart3,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../utils';
import { Button } from './ui/Button';
import { View, User, Notification } from '../types';
import { useThemeStore } from '../store/useThemeStore';
import { useAppStore } from '../store/useAppStore';
import { BotSelector } from './BotSelector';

interface LayoutProps {
  children: React.ReactNode;
  currentView: View;
  onNavigate: (view: View) => void;
  user: User;
  onLogout: () => void;
  botContext?: string | null;
}

// Breadcrumbs Component
const Breadcrumbs: React.FC<{ view: View; botContext?: string | null }> = ({
  view,
  botContext,
}) => {
  const getBreadcrumbs = (view: View, context?: string | null) => {
    const map: Record<string, string[]> = {
      dashboard: ['Overview'],
      bots: ['Bots'],
      'bot-chat': ['Bots', 'Chat Preview'],
      'bot-settings': ['Bots', context === 'new' ? 'Create New' : 'Settings'],
      knowledge: ['Knowledge Base'],
      settings: ['Settings'],
      subscription: ['Subscription'],
      users: ['Team', 'Users'],
      monitoring: ['Monitoring', 'Chat Logs'],
      analytics: ['Analytics'],
    };

    // Override for simpler breadcrumbs on top-level items
    if (view === 'bots' && !context) return ['Bots'];
    if (view === 'settings') return ['Settings'];
    if (view === 'subscription') return ['Subscription'];

    return map[view] || ['Dashboard'];
  };

  const crumbs = getBreadcrumbs(view, botContext);

  return (
    <nav className="flex items-center text-sm text-gray-500 dark:text-gray-400">
      <span className="hover:text-gray-900 dark:hover:text-gray-200 transition-colors cursor-pointer">
        Home
      </span>
      {crumbs.map((crumb, idx) => (
        <React.Fragment key={crumb}>
          <ChevronRight className="w-4 h-4 mx-1 text-gray-400" />
          <span
            className={cn(
              'transition-colors',
              idx === crumbs.length - 1
                ? 'font-medium text-gray-900 dark:text-gray-200'
                : 'hover:text-gray-900 dark:hover:text-gray-200 cursor-pointer'
            )}
          >
            {crumb}
          </span>
        </React.Fragment>
      ))}
    </nav>
  );
};

const MOCK_NOTIFICATIONS: Notification[] = [
  {
    id: '1',
    title: 'Bot Limit Reached',
    description: 'You have used 3/5 bots on your Pro plan.',
    time: '2m ago',
    read: false,
    type: 'warning',
  },
  {
    id: '2',
    title: 'New Subscriber',
    description: 'User @alexj joined Bot Customer Support.',
    time: '1h ago',
    read: false,
    type: 'success',
  },
  {
    id: '3',
    title: 'System Update',
    description: 'Gemini 2.5 Flash is now available.',
    time: '1d ago',
    read: true,
    type: 'info',
  },
];

export const Layout: React.FC<LayoutProps> = ({
  children,
  currentView,
  onNavigate,
  user,
  onLogout,
  botContext,
}) => {
  const { theme, toggleTheme, isSidebarOpen, toggleSidebar, setSidebarOpen, initializeTheme } =
    useThemeStore();
  const { selectedBotId, setSelectedBotId } = useAppStore();
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>(MOCK_NOTIFICATIONS);

  // Initialize theme on mount
  useEffect(() => {
    initializeTheme();
  }, []);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'bots', label: 'My Bots', icon: Bot },
    { id: 'monitoring', label: 'Monitoring', icon: Activity },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'knowledge', label: 'Knowledge Base', icon: Library },
    { id: 'bot-chat', label: 'Bot Chat', icon: MessageSquare },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'subscription', label: 'Subscription', icon: CreditCard },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  // Define views where BotSelector should be hidden
  const hideBotSelectorViews = ['subscription', 'settings', 'bots'];
  const showBotSelector = !hideBotSelectorViews.includes(currentView);

  return (
    <div className="min-h-screen bg-gray-50/50 dark:bg-gray-950 flex font-sans text-gray-900 dark:text-gray-100">
      {/* Mobile Sidebar Backdrop */}
      <AnimatePresence>
        {isSidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-gray-900/30 backdrop-blur-sm z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl border-r border-black/5 dark:border-white/5 flex flex-col shadow-xl lg:shadow-none lg:static h-screen'
        )}
        animate={{
          width: isSidebarOpen ? 256 : 0,
          x: isSidebarOpen ? 0 : 0,
        }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        style={{
          width: 256,
          x: 0,
        }}
      >
        {/* Mobile Logic Override for Motion */}
        <div
          className={cn(
            'flex flex-col h-full w-64 transition-transform duration-300 ease-in-out lg:transform-none',
            isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:hidden'
          )}
        >
          {/* Logo Area */}
          <div className="h-14 flex items-center px-4 border-b border-black/5 dark:border-white/5 shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-primary to-primary-dark rounded-lg shadow-sm flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <span className="font-semibold text-gray-900 dark:text-white tracking-tight">
                Bot Factory
              </span>
            </div>
            <Button
              variant="icon"
              size="md"
              className="ml-auto lg:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="w-5 h-5" />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto custom-scrollbar">
            {navItems.map((item) => {
              const Icon = item.icon;
              // 'bots' is active even when in 'bot-settings'
              const isActive =
                currentView === item.id || (item.id === 'bots' && currentView === 'bot-settings');
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    console.log('[Layout] Navigation clicked:', {
                      from: currentView,
                      to: item.id,
                      selectedBotId,
                    });

                    // CRITICAL FIX: If we are in 'new' bot creation mode and navigate away,
                    // we must reset the selection to null to prevent crashing pages like Knowledge/Monitoring
                    // which expect a valid bot ID.
                    if (selectedBotId === 'new') {
                      console.log('[Layout] Resetting selectedBotId from "new" to null');
                      setSelectedBotId(null);
                    }

                    // Existing safety cleanup for top-level views
                    if (
                      ['dashboard', 'bots', 'users', 'subscription', 'settings', 'analytics'].includes(item.id)
                    ) {
                      console.log('[Layout] Resetting selectedBotId for top-level view:', item.id);
                      setSelectedBotId(null);
                    }

                    onNavigate(item.id as View);
                    if (window.innerWidth < 1024) setSidebarOpen(false);
                  }}
                  className={cn(
                    'w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-all duration-200 group relative',
                    isActive
                      ? 'text-primary dark:text-primary-light bg-primary/5 dark:bg-primary/10'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100/80 dark:hover:bg-white/5 hover:text-gray-900 dark:hover:text-gray-200'
                  )}
                >
                  {isActive && (
                    <motion.div
                      layoutId="activeNavIndicator"
                      className="absolute left-0 w-1 h-5 bg-primary rounded-r-full"
                    />
                  )}
                  <Icon
                    className={cn(
                      'mr-3 h-4.5 w-4.5 flex-shrink-0 transition-colors',
                      isActive
                        ? 'text-primary dark:text-primary-light'
                        : 'text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300'
                    )}
                  />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Footer / User Profile */}
          <div className="p-4 border-t border-black/5 dark:border-white/5 bg-gray-50/50 dark:bg-gray-900/50">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-gray-200 to-gray-100 dark:from-gray-700 dark:to-gray-600 p-0.5 ring-1 ring-gray-200 dark:ring-white/10">
                <div className="w-full h-full rounded-full bg-white dark:bg-gray-800 flex items-center justify-center text-xs font-bold text-gray-700 dark:text-gray-200">
                  {user.name.substring(0, 2).toUpperCase()}
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {user.name}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {user.plan || 'Free'} Plan
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <Button
                variant="secondary"
                size="sm"
                className="justify-center w-full"
                onClick={toggleTheme}
              >
                {theme === 'dark' ? (
                  <Sun className="w-4 h-4 mr-2" />
                ) : (
                  <Moon className="w-4 h-4 mr-2" />
                )}
                {theme === 'dark' ? 'Light' : 'Dark'}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="justify-center w-full text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                onClick={onLogout}
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </motion.aside>

      {/* Main Content Wrapper */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        {/* Header - Glassmorphism */}
        <header className="h-14 bg-white/70 dark:bg-gray-900/70 backdrop-blur-xl border-b border-black/5 dark:border-white/5 flex items-center justify-between px-4 lg:px-8 sticky top-0 z-30">
          <div className="flex items-center gap-4">
            <Button variant="icon" size="md" className="lg:hidden" onClick={toggleSidebar}>
              <Menu className="w-5 h-5" />
            </Button>

            <div className="hidden md:block">
              <Breadcrumbs view={currentView} botContext={botContext} />
            </div>
          </div>

          <div className="flex items-center gap-3 relative">
            {/* Bot Selector - Visible on mobile (icon only handled by component) */}
            {showBotSelector && (
              <div className="mr-2">
                <BotSelector onCreateNew={() => onNavigate('bot-settings')} />
              </div>
            )}

            <div className="h-6 w-px bg-black/5 dark:bg-white/5 mx-1" />

            <Button
              variant="icon"
              size="md"
              className="relative"
              onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-2 right-2.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white dark:border-gray-900" />
              )}
            </Button>

            {/* Notifications Popover */}
            <AnimatePresence>
              {isNotificationsOpen && (
                <>
                  <div
                    className="fixed inset-0 z-30"
                    onClick={() => setIsNotificationsOpen(false)}
                  />
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className="absolute right-0 top-full mt-2 w-80 bg-white/90 dark:bg-gray-900/90 backdrop-blur-xl rounded-xl shadow-xl border border-black/5 dark:border-white/5 z-40 overflow-hidden ring-1 ring-black/5"
                  >
                    <div className="px-4 py-3 border-b border-black/5 dark:border-white/5 bg-gray-50/50 dark:bg-white/5 flex justify-between items-center">
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                        Notifications
                      </h3>
                      {unreadCount > 0 && (
                        <button
                          onClick={markAllAsRead}
                          className="text-xs text-primary hover:text-primary-dark font-medium"
                        >
                          Mark all read
                        </button>
                      )}
                    </div>
                    <div className="max-h-[300px] overflow-y-auto custom-scrollbar">
                      {notifications.length === 0 ? (
                        <div className="p-4 text-center text-xs text-gray-500">
                          No notifications
                        </div>
                      ) : (
                        notifications.map((notification) => (
                          <div
                            key={notification.id}
                            className={cn(
                              'px-4 py-3 border-b border-black/5 dark:border-white/5 last:border-0 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer flex gap-3',
                              !notification.read && 'bg-blue-50/50 dark:bg-blue-900/10'
                            )}
                          >
                            <div
                              className={cn(
                                'w-2 h-2 mt-1.5 rounded-full shrink-0',
                                notification.type === 'warning'
                                  ? 'bg-amber-500'
                                  : notification.type === 'success'
                                    ? 'bg-emerald-500'
                                    : 'bg-blue-500'
                              )}
                            />
                            <div>
                              <p className="text-sm font-medium text-gray-900 dark:text-white">
                                {notification.title}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                {notification.description}
                              </p>
                              <p className="text-[10px] text-gray-400 mt-1">{notification.time}</p>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-gray-50/50 dark:bg-gray-950 p-4 lg:p-8 relative custom-scrollbar">
          <div key={currentView} className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

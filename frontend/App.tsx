import React, { useState, useEffect } from 'react';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { ForgotPassword } from './pages/ForgotPassword';
import { Dashboard } from './pages/Dashboard';
import { Bots } from './pages/Bots';
import { BotChat } from './pages/BotChat';
import { BotSettings } from './pages/BotSettings';
import { ManageKnowledge } from './pages/ManageKnowledge';
import { Users } from './pages/Users';
import { Monitoring } from './pages/Monitoring';
import { Analytics } from './pages/Analytics';
import { Subscription } from './pages/Subscription';
import { Settings } from './pages/Settings';
import { Onboarding } from './components/Onboarding';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Toaster } from './components/ui/Toaster';
import { View } from './types';
import { useAppStore } from './store/useAppStore';
import { useAuthStore } from './store/useAuthStore';
import { api } from './services/api';

const App: React.FC = () => {
  const { setBots, selectedBotId, setSelectedBotId } = useAppStore();
  const { isAuthenticated, user, logout, initialize } = useAuthStore();

  // Auth Routing State
  const [authView, setAuthView] = useState<'login' | 'register' | 'forgot-password'>('login');

  // App Routing State
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [currentView, setCurrentView] = useState<View>('dashboard');

  // Initialize auth on mount
  useEffect(() => {
    initialize().catch((error) => {
      console.error('[App] Auth initialization error:', error);
    });
  }, [initialize]);

  // Log view changes
  useEffect(() => {
    console.log('[App] currentView changed:', currentView, 'selectedBotId:', selectedBotId);
  }, [currentView, selectedBotId]);

  // Load Global Data on Login
  useEffect(() => {
    if (isAuthenticated) {
      // Load bots from API
      api.bots
        .list()
        .then((data) => {
          setBots(data);
          setShowOnboarding(true); // Trigger onboarding on successful login
        })
        .catch((error) => {
          console.error('[App] Failed to load bots:', error);
        });
    } else {
      // Clear bots when logged out
      setBots([]);
    }
  }, [isAuthenticated, setBots]);

  // Reset views when logging out
  useEffect(() => {
    if (!isAuthenticated) {
      setCurrentView('dashboard');
      setAuthView('login');
    }
  }, [isAuthenticated]);

  const handleLogout = () => {
    logout();
    setShowOnboarding(false);
  };

  // Handle internal navigation from Bot List
  const handleBotEdit = (botId: string | null) => {
    if (botId) {
      setSelectedBotId(botId);
      setCurrentView('bot-settings');
    } else {
      // Creating new
      setSelectedBotId('new');
      setCurrentView('bot-settings');
    }
  };

  if (!isAuthenticated) {
    switch (authView) {
      case 'register':
        return <Register onNavigate={setAuthView} />;
      case 'forgot-password':
        return <ForgotPassword onNavigate={setAuthView} />;
      case 'login':
      default:
        return <Login onNavigate={setAuthView} />;
    }
  }

  const renderView = () => {
    console.log('[App] renderView called:', { currentView, selectedBotId });

    try {
      let component;

      switch (currentView) {
        case 'dashboard':
          console.log('[App] Rendering Dashboard');
          component = <Dashboard />;
          break;
        case 'bots':
          console.log('[App] Rendering Bots');
          component = <Bots onNavigate={handleBotEdit} />;
          break;
        case 'bot-settings':
          console.log('[App] Rendering BotSettings', { botId: selectedBotId });
          const handleBotSettingsBack = () => {
            console.log('[App] BotSettings onBack called');
            console.log('[App] Current state before back:', { currentView, selectedBotId });
            // Reset selectedBotId when going back to bots list
            setSelectedBotId(null);
            // Use setTimeout to ensure state update happens before navigation
            setTimeout(() => {
              console.log('[App] Navigating to bots after reset');
              setCurrentView('bots');
            }, 0);
          };

          component = <BotSettings botId={selectedBotId} onBack={handleBotSettingsBack} />;
          break;
        case 'bot-chat':
          console.log('[App] Rendering BotChat');
          component = <BotChat />;
          break;
        case 'knowledge':
          console.log('[App] Rendering ManageKnowledge');
          component = <ManageKnowledge />;
          break;
        case 'users':
          console.log('[App] Rendering Users');
          component = <Users onNavigate={setCurrentView} />;
          break;
        case 'monitoring':
          console.log('[App] Rendering Monitoring');
          component = <Monitoring />;
          break;
        case 'analytics':
          console.log('[App] Rendering Analytics');
          component = <Analytics />;
          break;
        case 'subscription':
          console.log('[App] Rendering Subscription');
          component = <Subscription />;
          break;
        case 'settings':
          console.log('[App] Rendering Settings');
          component = <Settings />;
          break;
        default:
          console.log('[App] Rendering default Dashboard');
          component = <Dashboard />;
      }

      console.log('[App] Component created successfully for:', currentView);
      return component;
    } catch (error) {
      console.error('[App] Error rendering view:', error);
      console.error('[App] Error stack:', error instanceof Error ? error.stack : 'No stack trace');
      return (
        <div className="p-8 text-red-600">
          Error rendering {currentView}: {error instanceof Error ? error.message : String(error)}
        </div>
      );
    }
  };

  return (
    <ErrorBoundary>
      <Toaster />
      {showOnboarding && <Onboarding onComplete={() => setShowOnboarding(false)} />}
      <Layout
        currentView={currentView}
        onNavigate={setCurrentView}
        user={user!}
        onLogout={handleLogout}
        botContext={selectedBotId}
      >
        {renderView()}
      </Layout>
    </ErrorBoundary>
  );
};

export default App;

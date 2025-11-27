import React, { useState, useEffect } from 'react';
import {
  Users as UsersIcon,
  Search,
  Filter,
  MoreHorizontal,
  MessageCircle,
  Clock,
  Calendar,
  ArrowRight,
  Bot,
  X,
  ShieldAlert,
  History,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { TelegramUser, View } from '../types';
import { api } from '../services/api';
import { toast } from 'sonner';
import { useAppStore } from '../store/useAppStore';
import { cn, formatDate } from '../utils';
import { EmptyState } from '../components/ui/EmptyState';

interface UsersProps {
  onNavigate: (view: View) => void;
}

export const Users: React.FC<UsersProps> = ({ onNavigate }) => {
  console.log('[Users] Component rendered');
  const { selectedBotId, getSelectedBot, setMonitoringUserId } = useAppStore();
  console.log('[Users] selectedBotId:', selectedBotId);
  const [users, setUsers] = useState<TelegramUser[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'blocked'>('all');
  const [selectedUser, setSelectedUser] = useState<TelegramUser | null>(null);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);

  useEffect(() => {
    if (selectedBotId) {
      loadUsers(selectedBotId);
    } else {
      setUsers([]);
    }
  }, [selectedBotId]);

  // Close menu on outside click - MUST be before early return to follow Rules of Hooks
  useEffect(() => {
    const closeMenu = () => setOpenMenuId(null);
    window.addEventListener('click', closeMenu);
    return () => window.removeEventListener('click', closeMenu);
  }, []);

  const loadUsers = async (botId: string) => {
    setIsLoading(true);
    try {
      const data = await api.users.list(botId);
      setUsers(data);
    } catch (error) {
      console.error('[Users] Failed to load users:', error);
      toast.error('Failed to load users. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const filteredUsers = users.filter((u) => {
    const matchesSearch =
      u.firstName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (u.username && u.username.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = statusFilter === 'all' || u.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Show EmptyState if no bot is selected
  if (!selectedBotId) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center space-y-4">
        <EmptyState
          title="No Bot Selected"
          description="Please select a bot from the header to view its users and manage their access."
          icon={UsersIcon}
        />
      </div>
    );
  }

  const handleBlockUser = async (e: React.MouseEvent, userId: string) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to block this user?')) {
      try {
        await api.users.updateStatus(userId, { status: 'blocked' });
        setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, status: 'blocked' } : u)));
        toast.success('User blocked successfully');
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to block user';
        toast.error(errorMessage);
      } finally {
        setOpenMenuId(null);
      }
    }
  };

  const handleUnblockUser = async (e: React.MouseEvent, userId: string) => {
    e.stopPropagation();
    try {
      await api.users.updateStatus(userId, { status: 'active' });
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, status: 'active' } : u)));
      toast.success('User unblocked successfully');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to unblock user';
      toast.error(errorMessage);
    } finally {
      setOpenMenuId(null);
    }
  };

  const handleViewHistory = (e: React.MouseEvent, userId: string) => {
    e.stopPropagation();
    setMonitoringUserId(userId);
    onNavigate('monitoring');
    setOpenMenuId(null);
  };

  const toggleMenu = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setOpenMenuId(openMenuId === id ? null : id);
  };

  return (
    <div className="flex h-[calc(100vh-140px)] gap-6">
      {/* Main Table Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <UsersIcon className="w-6 h-6 text-primary" />
              Bot Users
            </h1>
            <p className="text-gray-500 dark:text-gray-400">
              People interacting with{' '}
              <span className="font-medium text-gray-900 dark:text-gray-200">
                {getSelectedBot()?.name}
              </span>
            </p>
          </div>
          <div className="flex gap-2 w-full sm:w-auto items-center">
            <div className="flex bg-white dark:bg-gray-800 rounded-lg border border-black/10 dark:border-white/10 p-1">
              <button
                onClick={() => setStatusFilter('all')}
                className={cn(
                  'px-3 py-1.5 text-xs font-medium rounded-md transition-colors',
                  statusFilter === 'all'
                    ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                    : 'text-gray-500 hover:text-gray-900'
                )}
              >
                All
              </button>
              <button
                onClick={() => setStatusFilter('active')}
                className={cn(
                  'px-3 py-1.5 text-xs font-medium rounded-md transition-colors',
                  statusFilter === 'active'
                    ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                    : 'text-gray-500 hover:text-gray-900'
                )}
              >
                Active
              </button>
              <button
                onClick={() => setStatusFilter('blocked')}
                className={cn(
                  'px-3 py-1.5 text-xs font-medium rounded-md transition-colors',
                  statusFilter === 'blocked'
                    ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                    : 'text-gray-500 hover:text-gray-900'
                )}
              >
                Blocked
              </button>
            </div>
            <Input
              placeholder="Search users..."
              startIcon={<Search className="w-4 h-4" />}
              className="w-full sm:w-56"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <Card className="flex-1 border-black/5 dark:border-white/5 flex flex-col overflow-hidden bg-white dark:bg-gray-900">
          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50/50 dark:bg-gray-900/50 border-b border-black/5 dark:border-white/5 sticky top-0 backdrop-blur-sm z-10">
                <tr>
                  <th className="px-6 py-4 font-medium text-gray-500 dark:text-gray-400">User</th>
                  <th className="px-6 py-4 font-medium text-gray-500 dark:text-gray-400">Status</th>
                  <th className="px-6 py-4 font-medium text-gray-500 dark:text-gray-400">
                    Messages
                  </th>
                  <th className="px-6 py-4 font-medium text-gray-500 dark:text-gray-400">
                    Last Active
                  </th>
                  <th className="px-6 py-4 font-medium text-gray-500 dark:text-gray-400 text-right">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/5 dark:divide-white/5">
                {isLoading ? (
                  <tr>
                    <td colSpan={5} className="p-8 text-center text-gray-500">
                      Loading users...
                    </td>
                  </tr>
                ) : filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-12 text-center">
                      <div className="flex flex-col items-center justify-center">
                        <UsersIcon className="w-8 h-8 text-gray-300 mb-2" />
                        <p className="text-gray-500">No users found matching your filters.</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map((user) => (
                    <tr
                      key={user.id}
                      onClick={() => setSelectedUser(user)}
                      className={cn(
                        'group hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer',
                        selectedUser?.id === user.id && 'bg-indigo-50 dark:bg-indigo-900/10',
                        user.status === 'blocked' && 'opacity-60 grayscale'
                      )}
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div
                            className={cn(
                              'w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold',
                              user.status === 'blocked'
                                ? 'bg-gray-200 dark:bg-gray-800 text-gray-500'
                                : 'bg-gradient-to-tr from-blue-100 to-indigo-100 dark:from-blue-900 dark:to-indigo-900 text-indigo-600 dark:text-indigo-300'
                            )}
                          >
                            {user.firstName[0]}
                          </div>
                          <div>
                            <div className="font-medium text-gray-900 dark:text-white">
                              {user.firstName} {user.lastName}
                            </div>
                            <div className="text-xs text-gray-500">
                              {user.username ? `@${user.username}` : `ID: ${user.telegramId}`}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant={user.status === 'active' ? 'success' : 'error'}>
                          {user.status}
                        </Badge>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1.5 text-gray-600 dark:text-gray-300">
                          <MessageCircle className="w-4 h-4 text-gray-400" />
                          {user.messageCount}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-500 dark:text-gray-400">
                        {formatDate(user.lastActive)}
                      </td>
                      <td className="px-6 py-4 text-right relative">
                        <Button
                          variant="icon"
                          size="md"
                          className={cn(
                            'opacity-0 group-hover:opacity-100 transition-opacity',
                            openMenuId === user.id && 'opacity-100'
                          )}
                          onClick={(e) => toggleMenu(e, user.id)}
                        >
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>

                        {/* Action Menu */}
                        <AnimatePresence>
                          {openMenuId === user.id && (
                            <motion.div
                              initial={{ opacity: 0, scale: 0.95 }}
                              animate={{ opacity: 1, scale: 1 }}
                              exit={{ opacity: 0, scale: 0.95 }}
                              className="absolute right-8 top-8 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-black/5 dark:border-white/5 z-50 overflow-hidden py-1"
                            >
                              <button
                                onClick={(e) => handleViewHistory(e, user.id)}
                                className="w-full px-4 py-2 text-sm text-left hover:bg-gray-50 dark:hover:bg-white/5 flex items-center gap-2 text-gray-700 dark:text-gray-200"
                              >
                                <History className="w-4 h-4 text-gray-400" />
                                View Chat History
                              </button>
                              {user.status === 'active' ? (
                                <button
                                  onClick={(e) => handleBlockUser(e, user.id)}
                                  className="w-full px-4 py-2 text-sm text-left hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2 text-red-600 dark:text-red-400"
                                >
                                  <ShieldAlert className="w-4 h-4" />
                                  Block User
                                </button>
                              ) : (
                                <button
                                  onClick={(e) => handleUnblockUser(e, user.id)}
                                  className="w-full px-4 py-2 text-sm text-left hover:bg-emerald-50 dark:hover:bg-emerald-900/20 flex items-center gap-2 text-emerald-600 dark:text-emerald-400"
                                >
                                  <ShieldAlert className="w-4 h-4" />
                                  Unblock User
                                </button>
                              )}
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Details Drawer */}
      <AnimatePresence>
        {selectedUser && (
          <motion.div
            initial={{ x: 400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 400, opacity: 0 }}
            className="w-96 bg-white dark:bg-gray-900 border-l border-black/5 dark:border-white/5 shadow-2xl z-20 flex flex-col"
          >
            <div className="p-6 border-b border-black/5 dark:border-white/5 flex justify-between items-start">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-2xl">
                  {selectedUser.firstName[0]}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                    {selectedUser.firstName} {selectedUser.lastName}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {selectedUser.username ? `@${selectedUser.username}` : 'No username'}
                  </p>
                </div>
              </div>
              <Button variant="icon" size="md" onClick={() => setSelectedUser(null)}>
                <X className="w-5 h-5" />
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-8">
              {/* Stats Grid */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-gray-50 dark:bg-white/5 border border-black/5 dark:border-white/5">
                  <div className="text-gray-500 text-xs mb-1">First Seen</div>
                  <div className="font-medium text-sm flex items-center gap-2">
                    <Calendar className="w-3.5 h-3.5 text-gray-400" />
                    {new Date(selectedUser.firstSeen).toLocaleDateString()}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-gray-50 dark:bg-white/5 border border-black/5 dark:border-white/5">
                  <div className="text-gray-500 text-xs mb-1">Last Active</div>
                  <div className="font-medium text-sm flex items-center gap-2">
                    <Clock className="w-3.5 h-3.5 text-gray-400" />
                    {new Date(selectedUser.lastActive).toLocaleDateString()}
                  </div>
                </div>
              </div>

              {/* User Info */}
              <div>
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                  User Information
                </h4>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm py-2 border-b border-black/5 dark:border-white/5">
                    <span className="text-gray-500">Telegram ID</span>
                    <span className="font-mono text-gray-700 dark:text-gray-300">
                      {selectedUser.telegramId}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm py-2 border-b border-black/5 dark:border-white/5">
                    <span className="text-gray-500">Language</span>
                    <span className="text-gray-700 dark:text-gray-300">English (en)</span>
                  </div>
                  <div className="flex justify-between text-sm py-2 border-b border-black/5 dark:border-white/5">
                    <span className="text-gray-500">Status</span>
                    <Badge variant={selectedUser.status === 'active' ? 'success' : 'error'}>
                      {selectedUser.status}
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="space-y-3">
                <Button
                  className="w-full"
                  icon={<MessageCircle className="w-4 h-4" />}
                  onClick={() => {
                    setMonitoringUserId(selectedUser.id);
                    onNavigate('monitoring');
                  }}
                >
                  View Chat History
                </Button>
                {selectedUser.status === 'active' ? (
                  <Button
                    variant="secondary"
                    className="w-full text-red-600 hover:bg-red-50"
                    onClick={(e) => handleBlockUser(e, selectedUser.id)}
                  >
                    Block User
                  </Button>
                ) : (
                  <Button
                    variant="secondary"
                    className="w-full text-emerald-600 hover:bg-emerald-50"
                    onClick={(e) => handleUnblockUser(e, selectedUser.id)}
                  >
                    Unblock User
                  </Button>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

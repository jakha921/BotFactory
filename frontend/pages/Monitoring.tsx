import React, { useState, useEffect, useRef } from 'react';
import {
  Activity,
  Search,
  Filter,
  AlertCircle,
  User as UserIcon,
  Flag,
  ThumbsDown,
  MessageSquare,
  Sparkles,
  Bot,
  X,
  Wand2,
  BookPlus,
  Save,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Textarea } from '../components/ui/Textarea';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import { EmptyState } from '../components/ui/EmptyState';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';
import { toast } from 'sonner';
import { ChatSession, ChatMessage } from '../types';
import { cn } from '../utils';
import { motion, AnimatePresence } from 'framer-motion';

export const Monitoring: React.FC = () => {
  console.log('[Monitoring] Component rendered');
  const { selectedBotId, getSelectedBot, monitoringUserId, setMonitoringUserId } = useAppStore();
  console.log('[Monitoring] selectedBotId:', selectedBotId);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [filteredSessions, setFilteredSessions] = useState<ChatSession[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [filter, setFilter] = useState<'all' | 'flagged' | 'negative'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Modals State
  const [isImproveModalOpen, setIsImproveModalOpen] = useState(false);
  const [improvementText, setImprovementText] = useState('');

  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [reportData, setReportData] = useState<{ question: string; answer: string; botId: string }>(
    { question: '', answer: '', botId: '' }
  );
  const [isSavingReport, setIsSavingReport] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (selectedBotId) {
      loadSessions(selectedBotId);
    } else {
      setSessions([]);
      setFilteredSessions([]);
    }
  }, [selectedBotId]);

  // Auto-select session if navigating from Users page
  useEffect(() => {
    if (monitoringUserId && sessions.length > 0) {
      const userSession = sessions.find((s) => s.userId === monitoringUserId);
      if (userSession) {
        setSelectedSessionId(userSession.id);
        // Optional: Clear context after consuming it
        // setMonitoringUserId(null);
      }
    }
  }, [monitoringUserId, sessions]);

  useEffect(() => {
    if (selectedSessionId) {
      loadMessages(selectedSessionId);
    }
  }, [selectedSessionId]);

  useEffect(() => {
    let res = sessions;
    if (filter === 'flagged') res = res.filter((s) => s.isFlagged);
    if (filter === 'negative') res = res.filter((s) => s.sentiment === 'negative');
    if (searchTerm) {
      res = res.filter(
        (s) =>
          s.userName.toLowerCase().includes(searchTerm.toLowerCase()) ||
          s.lastMessage.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    setFilteredSessions(res);
  }, [sessions, filter, searchTerm]);

  const loadSessions = async (botId: string) => {
    setIsLoading(true);
    try {
      const data = await api.chat.sessions(botId);
      setSessions(data);
      // Default selection logic: only if no monitoring context
      if (data.length > 0 && !selectedSessionId && !monitoringUserId) {
        setSelectedSessionId(data[0].id);
      }
    } catch (error) {
      console.error('[Monitoring] Failed to load sessions:', error);
      toast.error('Failed to load chat sessions. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadMessages = async (sessionId: string) => {
    try {
      const msgs = await api.chat.messages(sessionId);
      // Convert timestamp strings to Date objects
      const messagesWithDates = msgs.map((msg) => ({
        ...msg,
        timestamp: msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp),
      }));
      setMessages(messagesWithDates);
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (error) {
      console.error('[Monitoring] Failed to load messages:', error);
      toast.error('Failed to load messages. Please try again.');
    }
  };

  const toggleFlagMessage = (msgId: string) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === msgId ? { ...m, isFlagged: !m.isFlagged } : m))
    );
    if (selectedSessionId) {
      setSessions((prev) =>
        prev.map((s) => (s.id === selectedSessionId ? { ...s, isFlagged: true } : s))
      );
    }
  };

  const openImproveModal = () => {
    const currentBot = getSelectedBot();
    const originalInstruction = currentBot?.systemInstruction || '';
    setImprovementText(
      `${originalInstruction}\n\n[ADDED BY AI ANALYTICS]:\n- Ensure specific details about refund processing time (5-7 days) are mentioned.\n- Be more empathetic when user sentiment is negative.`
    );
    setIsImproveModalOpen(true);
  };

  const handleReportToKB = (msgIndex: number) => {
    const botMsg = messages[msgIndex];
    let userMsg = null;
    for (let i = msgIndex - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        userMsg = messages[i];
        break;
      }
    }

    setReportData({
      question: userMsg ? userMsg.content : 'Context unavailable',
      answer: botMsg.content,
      botId: selectedBotId || '',
    });
    setIsReportModalOpen(true);
  };

  const saveReportToKB = async () => {
    if (!selectedBotId) return;
    setIsSavingReport(true);
    try {
      await api.knowledge.saveSnippet({
        botId: selectedBotId!,
        title: `Correction: ${reportData.question.substring(0, 30)}...`,
        content: `Q: ${reportData.question}\n\nA: ${reportData.answer}`,
        tags: ['correction', 'from-monitoring'],
      });
      toast.success('Snippet saved successfully');
      setIsReportModalOpen(false);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSavingReport(false);
    }
  };

  if (!selectedBotId) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center space-y-4">
        <EmptyState
          title="No Bot Selected"
          description="Please select a bot from the header to monitor its conversations and analyze performance."
          icon={Activity}
        />
      </div>
    );
  }

  const selectedSession = sessions.find((s) => s.id === selectedSessionId);

  return (
    <div className="flex h-[calc(100vh-140px)] gap-6 overflow-hidden">
      {/* Left Panel: Session List */}
      <div className="w-80 md:w-96 flex-shrink-0 flex flex-col bg-white/60 dark:bg-gray-900/40 backdrop-blur-xl rounded-2xl border border-black/5 dark:border-white/5 shadow-sm overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-black/5 dark:border-white/5 space-y-3">
          <div className="flex justify-between items-center">
            <h2 className="font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-primary" />
              Conversations
            </h2>
            {monitoringUserId && (
              <Badge
                variant="info"
                className="flex gap-1 items-center cursor-pointer"
                onClick={() => setMonitoringUserId(null)}
              >
                Filter Active <X className="w-3 h-3" />
              </Badge>
            )}
          </div>
          <div className="relative">
            <Search className="absolute left-2.5 top-2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search history..."
              className="w-full h-9 pl-9 pr-4 rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-gray-900 text-sm focus:ring-2 focus:ring-primary/20 outline-none"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            {['all', 'flagged', 'negative'].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f as any)}
                className={cn(
                  'px-3 py-1 rounded-full text-xs font-medium capitalize transition-colors border',
                  filter === f
                    ? 'bg-gray-900 text-white border-gray-900 dark:bg-white dark:text-gray-900'
                    : 'bg-transparent text-gray-500 border-transparent hover:bg-gray-100 dark:hover:bg-white/5'
                )}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
          {isLoading ? (
            // Improved Skeleton Loader
            Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="p-3 rounded-xl mb-2 border border-transparent space-y-2">
                <div className="flex justify-between">
                  <div className="h-4 w-24 bg-gray-200 dark:bg-white/10 rounded animate-pulse" />
                  <div className="h-3 w-12 bg-gray-200 dark:bg-white/10 rounded animate-pulse" />
                </div>
                <div className="h-3 w-full bg-gray-200 dark:bg-white/5 rounded animate-pulse" />
                <div className="h-3 w-1/2 bg-gray-200 dark:bg-white/5 rounded animate-pulse" />
              </div>
            ))
          ) : filteredSessions.length === 0 ? (
            <div className="py-12">
              <EmptyState
                title="No conversations"
                description="No chat history found matching your filters."
                icon={MessageSquare}
              />
            </div>
          ) : (
            filteredSessions.map((session) => (
              <div
                key={session.id}
                onClick={() => setSelectedSessionId(session.id)}
                className={cn(
                  'p-3 rounded-xl cursor-pointer transition-all duration-200 border border-transparent',
                  selectedSessionId === session.id
                    ? 'bg-white dark:bg-white/5 shadow-sm border-black/5 dark:border-white/5'
                    : 'hover:bg-gray-50 dark:hover:bg-white/5',
                  monitoringUserId &&
                  session.userId === monitoringUserId &&
                  selectedSessionId !== session.id &&
                  'bg-blue-50 dark:bg-blue-900/10'
                )}
              >
                <div className="flex justify-between items-start mb-1">
                  <div className="font-semibold text-sm text-gray-900 dark:text-white truncate pr-2">
                    {session.userName}
                  </div>
                  <div className="text-[10px] text-gray-400 whitespace-nowrap">
                    {new Date(session.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mb-2">
                  {session.lastMessage}
                </div>
                <div className="flex items-center gap-2">
                  {session.sentiment === 'negative' && (
                    <span className="inline-flex items-center gap-1 text-[10px] text-red-600 bg-red-50 dark:bg-red-900/20 px-1.5 py-0.5 rounded">
                      <ThumbsDown className="w-3 h-3" /> Negative
                    </span>
                  )}
                  {session.isFlagged && (
                    <span className="inline-flex items-center gap-1 text-[10px] text-amber-600 bg-amber-50 dark:bg-amber-900/20 px-1.5 py-0.5 rounded">
                      <Flag className="w-3 h-3" /> Flagged
                    </span>
                  )}
                  {session.unreadCount ? (
                    <span className="ml-auto w-2 h-2 bg-primary rounded-full" />
                  ) : null}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Right Panel: Chat Viewer */}
      <div className="flex-1 flex flex-col bg-white/60 dark:bg-gray-900/40 backdrop-blur-xl rounded-2xl border border-black/5 dark:border-white/5 shadow-sm overflow-hidden">
        {selectedSession ? (
          <>
            {/* Chat Header */}
            <div className="h-16 border-b border-black/5 dark:border-white/5 flex items-center justify-between px-6 bg-white/40 dark:bg-gray-900/40 backdrop-blur-md">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold shadow-inner">
                  {selectedSession.userName[0]}
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 dark:text-white text-sm">
                    {selectedSession.userName}
                  </h3>
                  <p className="text-xs text-gray-500 flex items-center gap-1">
                    User ID: {selectedSession.userId} •
                    <span
                      className={cn(
                        'font-medium',
                        selectedSession.sentiment === 'positive'
                          ? 'text-emerald-500'
                          : selectedSession.sentiment === 'negative'
                            ? 'text-red-500'
                            : 'text-gray-500'
                      )}
                    >
                      {selectedSession.sentiment.charAt(0).toUpperCase() +
                        selectedSession.sentiment.slice(1)}{' '}
                      Sentiment
                    </span>
                  </p>
                </div>
              </div>
              <Button
                variant="secondary"
                size="sm"
                icon={<Wand2 className="w-4 h-4 text-purple-500" />}
                onClick={openImproveModal}
                className="border-purple-200 dark:border-purple-900/30 hover:bg-purple-50 dark:hover:bg-purple-900/20 text-purple-700 dark:text-purple-300"
              >
                Improve Instruction
              </Button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-white/20 dark:bg-gray-900/20">
              {messages.map((msg, idx) => (
                <div
                  key={msg.id}
                  className={cn(
                    'flex gap-4 max-w-[85%] group',
                    msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''
                  )}
                >
                  <div
                    className={cn(
                      'w-8 h-8 rounded-full flex items-center justify-center shrink-0',
                      msg.role === 'user'
                        ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900'
                        : 'bg-primary text-white'
                    )}
                  >
                    {msg.role === 'user' ? (
                      <UserIcon className="w-5 h-5" />
                    ) : (
                      <Sparkles className="w-5 h-5" />
                    )}
                  </div>

                  <div className="relative">
                    <div
                      className={cn(
                        'p-4 rounded-2xl text-sm leading-relaxed shadow-sm whitespace-pre-wrap border',
                        msg.role === 'user'
                          ? 'bg-primary text-white border-primary rounded-tr-none'
                          : cn(
                            'bg-white dark:bg-gray-800 rounded-tl-none',
                            msg.isFlagged
                              ? 'border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/10'
                              : 'border-black/5 dark:border-white/5'
                          )
                      )}
                    >
                      {msg.content}
                    </div>
                    <div
                      className={cn(
                        'text-[10px] mt-1.5 opacity-60 flex items-center gap-2',
                        msg.role === 'user' ? 'justify-end text-gray-500' : 'text-gray-500'
                      )}
                    >
                      {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}

                      {/* Bot Message Actions */}
                      {msg.role === 'model' && (
                        <>
                          <button
                            onClick={() => toggleFlagMessage(msg.id)}
                            className={cn(
                              'flex items-center gap-1 transition-opacity ml-2',
                              msg.isFlagged
                                ? 'opacity-100 text-amber-600 font-medium'
                                : 'opacity-0 group-hover:opacity-100 hover:text-amber-600'
                            )}
                          >
                            <Flag
                              className="w-3 h-3"
                              fill={msg.isFlagged ? 'currentColor' : 'none'}
                            />
                            {msg.isFlagged ? 'Flagged Incorrect' : 'Flag'}
                          </button>

                          <button
                            onClick={() => handleReportToKB(idx)}
                            className="flex items-center gap-1 transition-opacity opacity-0 group-hover:opacity-100 hover:text-blue-600 ml-2"
                          >
                            <BookPlus className="w-3 h-3" />
                            Add to KB
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-gray-400">
            <MessageSquare className="w-12 h-12 mb-4 opacity-20" />
            <p>Select a conversation to review details.</p>
          </div>
        )}
      </div>

      {/* Improve Instruction Modal */}
      <AnimatePresence>
        {isImproveModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white dark:bg-gray-900 w-full max-w-2xl rounded-2xl shadow-2xl border border-black/5 dark:border-white/5 overflow-hidden flex flex-col max-h-[90vh]"
            >
              <div className="p-6 border-b border-black/5 dark:border-white/5 flex justify-between items-center bg-gray-50/50 dark:bg-gray-900/50">
                <div>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-purple-500" />
                    AI Instruction Optimizer
                  </h3>
                  <p className="text-sm text-gray-500">
                    Refine your bot's system instruction based on flagged chats.
                  </p>
                </div>
                <Button variant="icon" size="md" onClick={() => setIsImproveModalOpen(false)}>
                  <X className="w-5 h-5" />
                </Button>
              </div>

              <div className="p-6 overflow-y-auto space-y-4">
                <div className="bg-amber-50 dark:bg-amber-900/10 border border-amber-100 dark:border-amber-900/30 p-4 rounded-lg text-sm text-amber-800 dark:text-amber-400">
                  <h4 className="font-semibold mb-1 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" /> Analysis
                  </h4>
                  <p>
                    The bot failed to provide specific policy details in the recent conversation.
                    I've drafted an update to include these specifics and adjust the tone.
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Suggested System Instruction
                  </label>
                  <Textarea
                    value={improvementText}
                    onChange={(e) => setImprovementText(e.target.value)}
                    className="h-64 font-mono text-sm"
                  />
                </div>
              </div>

              <div className="p-6 border-t border-black/5 dark:border-white/5 bg-gray-50/50 dark:bg-gray-900/50 flex justify-end gap-3">
                <Button variant="secondary" onClick={() => setIsImproveModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    try {
                      const currentBot = getSelectedBot();
                      if (currentBot) {
                        await api.bots.save({
                          ...currentBot,
                          systemInstruction: improvementText
                        });
                        toast.success('Bot instruction updated successfully');
                      }
                      setIsImproveModalOpen(false);
                    } catch (error: any) {
                      toast.error(error?.message || 'Failed to update instruction');
                    }
                  }}
                >
                  Apply Updates
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Add to Knowledge Base Modal */}
      <AnimatePresence>
        {isReportModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white dark:bg-gray-900 w-full max-w-lg rounded-2xl shadow-2xl border border-black/5 dark:border-white/5 overflow-hidden flex flex-col max-h-[90vh]"
            >
              <div className="p-6 border-b border-black/5 dark:border-white/5 flex justify-between items-center bg-gray-50/50 dark:bg-gray-900/50">
                <div>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <BookPlus className="w-5 h-5 text-blue-500" />
                    Add to Knowledge Base
                  </h3>
                  <p className="text-sm text-gray-500">
                    Save a corrected response to improve future answers.
                  </p>
                </div>
                <Button variant="icon" size="md" onClick={() => setIsReportModalOpen(false)}>
                  <X className="w-5 h-5" />
                </Button>
              </div>

              <div className="p-6 overflow-y-auto space-y-5">
                <div className="space-y-1.5">
                  <Label>User Question (Context)</Label>
                  <div className="p-3 rounded-lg bg-gray-50 dark:bg-white/5 text-sm text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-white/10">
                    {reportData.question}
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label>Correct Answer</Label>
                  <Textarea
                    value={reportData.answer}
                    onChange={(e) => setReportData((prev) => ({ ...prev, answer: e.target.value }))}
                    className="min-h-[150px]"
                    placeholder="Type the correct answer here..."
                  />
                  <p className="text-xs text-gray-500">
                    This will be saved as a text snippet tagged 'correction'.
                  </p>
                </div>
              </div>

              <div className="p-6 border-t border-black/5 dark:border-white/5 bg-gray-50/50 dark:bg-gray-900/50 flex justify-end gap-3">
                <Button variant="secondary" onClick={() => setIsReportModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={saveReportToKB}
                  isLoading={isSavingReport}
                  icon={<Save className="w-4 h-4" />}
                >
                  Save Snippet
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import {
  Plus,
  Search,
  Filter,
  MoreVertical,
  MessageCircle,
  FileText,
  Bot as BotIcon,
  Edit,
  Trash2,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import { Bot, BotStatus } from '../types';
import { api } from '../services/api';
import { toast } from 'sonner';

interface BotsProps {
  onNavigate: (botId: string | null) => void;
}

export const Bots: React.FC<BotsProps> = ({ onNavigate }) => {
  console.log('[Bots] Component rendered');
  const [bots, setBots] = useState<Bot[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadBots();
  }, []);

  const loadBots = async () => {
    setIsLoading(true);
    try {
      const data = await api.bots.list();
      setBots(data);
    } catch (error) {
      console.error('[Bots] Failed to load bots:', error);
      toast.error('Failed to load bots. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this bot?')) {
      try {
        await api.bots.delete(id);
        toast.success('Bot deleted successfully');
        loadBots();
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to delete bot';
        toast.error(errorMessage);
      }
    }
  };

  const filteredBots = bots.filter(
    (b) =>
      b.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      b.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-pulse">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-64 bg-gray-200 dark:bg-gray-800 rounded-xl" />
        ))}
      </div>
    );
  }

  if (bots.length === 0) {
    return (
      <div className="h-[60vh] flex items-center justify-center">
        <EmptyState
          title="No bots created yet"
          description="Create your first AI agent to start automating conversations on Telegram. It takes less than a minute."
          icon={BotIcon}
          action={
            <Button onClick={() => onNavigate(null)} icon={<Plus className="w-4 h-4" />}>
              Create First Bot
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">My Bots</h1>
          <p className="text-gray-500 dark:text-gray-400">Manage and monitor your AI agents.</p>
        </div>
        <Button icon={<Plus className="w-4 h-4" />} onClick={() => onNavigate(null)}>
          Create Bot
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm p-4 rounded-xl shadow-sm border border-black/5 dark:border-white/5">
        <div className="flex-1">
          <Input
            placeholder="Search bots..."
            startIcon={<Search className="w-4 h-4" />}
            className="border-black/10 dark:border-white/10 bg-gray-50/50 dark:bg-gray-900/50 focus:bg-white dark:focus:bg-gray-900 transition-all"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" icon={<Filter className="w-4 h-4" />}>
            Filter
          </Button>
        </div>
      </div>

      {/* Grid */}
      {filteredBots.length === 0 ? (
        <div className="py-12">
          <EmptyState
            title="No matching bots found"
            description={`No bots found matching "${searchTerm}". Try adjusting your search terms.`}
            icon={Search}
            action={
              <Button variant="secondary" onClick={() => setSearchTerm('')}>
                Clear Search
              </Button>
            }
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredBots.map((bot) => (
            <Card
              key={bot.id}
              className="group hover:border-primary/50 hover:shadow-md transition-all duration-300 cursor-pointer relative overflow-hidden border-black/5 dark:border-white/5"
              onClick={() => onNavigate(bot.id)}
            >
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-indigo-50 dark:bg-indigo-900/20 flex items-center justify-center text-primary shadow-inner">
                      <BotIcon className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="font-bold text-gray-900 dark:text-white group-hover:text-primary transition-colors">
                        {bot.name}
                      </h3>
                      <Badge
                        variant={bot.status === BotStatus.ACTIVE ? 'success' : 'warning'}
                        className="mt-1"
                      >
                        {bot.status}
                      </Badge>
                    </div>
                  </div>

                  <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute top-4 right-4 flex gap-1 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-black/5 dark:border-white/10 p-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      onClick={(e) => {
                        e.stopPropagation();
                        onNavigate(bot.id);
                      }}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 text-red-500 hover:text-red-600"
                      onClick={(e) => handleDelete(e, bot.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 line-clamp-2 min-h-[2.5rem]">
                  {bot.description || 'No description provided.'}
                </p>

                <div className="flex items-center gap-4 pt-4 border-t border-black/5 dark:border-white/5">
                  <div className="flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400">
                    <MessageCircle className="w-4 h-4" />
                    <span>{bot.conversationsCount}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400">
                    <FileText className="w-4 h-4" />
                    <span>{bot.documentsCount}</span>
                  </div>
                  <div className="ml-auto text-xs font-mono text-gray-400 bg-gray-50 dark:bg-white/5 px-2 py-1 rounded border border-black/5 dark:border-white/5">
                    {bot.model}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {/* Add New Card */}
          <button
            onClick={() => onNavigate(null)}
            className="flex flex-col items-center justify-center p-6 rounded-xl border-2 border-dashed border-black/10 dark:border-white/10 hover:border-primary hover:bg-indigo-50/50 dark:hover:bg-white/5 transition-all duration-300 group h-full min-h-[200px]"
          >
            <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-white/5 group-hover:bg-indigo-100 dark:group-hover:bg-indigo-500/20 flex items-center justify-center mb-4 transition-colors">
              <Plus className="w-6 h-6 text-gray-400 dark:text-gray-400 group-hover:text-primary" />
            </div>
            <span className="font-medium text-gray-900 dark:text-white">Create New Bot</span>
            <span className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Deploy a new agent in seconds
            </span>
          </button>
        </div>
      )}
    </div>
  );
};

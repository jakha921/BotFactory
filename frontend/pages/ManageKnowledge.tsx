import React, { useState, useEffect, useCallback } from 'react';
import {
  Upload,
  FileText,
  Trash2,
  CheckCircle,
  Loader2,
  File,
  Search,
  Bot,
  Plus,
  Sparkles,
  X,
  Edit3,
  Tag,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Tabs } from '../components/ui/Tabs';
import { Textarea } from '../components/ui/Textarea';
import { Label } from '../components/ui/Label';
import { Document, TextSnippet } from '../types';
import { api } from '../services/api';
import { toast } from 'sonner';
import { generateBotResponse } from '../services/geminiService';
import { cn, formatDate } from '../utils';
import { useAppStore } from '../store/useAppStore';
import { AnimatePresence, motion } from 'framer-motion';

const TABS = [
  { id: 'files', label: 'Files' },
  { id: 'snippets', label: 'Text Snippets' },
];

export const ManageKnowledge: React.FC = () => {
  console.log('[ManageKnowledge] Component rendered');
  const { selectedBotId, getSelectedBot } = useAppStore();
  console.log('[ManageKnowledge] selectedBotId:', selectedBotId, 'getSelectedBot:', getSelectedBot);
  const [activeTab, setActiveTab] = useState('files');

  // Files State
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isDocsLoading, setIsDocsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [isDragging, setIsDragging] = useState(false);

  // Snippets State
  const [snippets, setSnippets] = useState<TextSnippet[]>([]);
  const [isSnippetsLoading, setIsSnippetsLoading] = useState(false);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingSnippet, setEditingSnippet] = useState<Partial<TextSnippet>>({
    title: '',
    content: '',
    tags: [],
  });
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  // --- Data Loading ---
  useEffect(() => {
    if (!selectedBotId) {
      setDocuments([]);
      setSnippets([]);
      return;
    }

    if (activeTab === 'files') {
      loadDocuments(selectedBotId);
    } else {
      loadSnippets(selectedBotId);
    }
  }, [selectedBotId, activeTab]);

  const loadDocuments = async (botId: string) => {
    setIsDocsLoading(true);
    try {
      const data = await api.knowledge.documents(botId);
      setDocuments(data);
    } catch (error) {
      console.error('[ManageKnowledge] Failed to load documents:', error);
      toast.error('Failed to load documents. Please try again.');
    } finally {
      setIsDocsLoading(false);
    }
  };

  const loadSnippets = async (botId: string) => {
    setIsSnippetsLoading(true);
    try {
      const data = await api.knowledge.snippets(botId);
      setSnippets(data);
    } catch (error) {
      console.error('[ManageKnowledge] Failed to load snippets:', error);
      toast.error('Failed to load snippets. Please try again.');
    } finally {
      setIsSnippetsLoading(false);
    }
  };

  const handleSync = async () => {
    if (!selectedBotId) return;
    setIsSyncing(true);

    try {
      // Reload both sources to ensure full sync
      await Promise.all([loadDocuments(selectedBotId), loadSnippets(selectedBotId)]);
    } catch (e) {
      console.error('Sync failed', e);
    } finally {
      // Artificial delay to show the nice loading state if data is instant
      setTimeout(() => setIsSyncing(false), 600);
    }
  };

  // --- Files Handlers ---
  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (selectedBotId) setIsDragging(true);
    },
    [selectedBotId]
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      if (!selectedBotId) return;

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        await processUpload(files[0]);
      }
    },
    [selectedBotId]
  );

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0 && selectedBotId) {
      await processUpload(files[0]);
    }
  };

  const processUpload = async (file: File) => {
    if (!selectedBotId) return;
    try {
      const newDoc = await api.knowledge.upload(file, selectedBotId);
      setDocuments((prev) => [newDoc, ...prev]);
      toast.success('Document uploaded successfully');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to upload document';
      toast.error(errorMessage);
    }
  };

  const handleDeleteDoc = async (id: string) => {
    if (window.confirm('Delete this document?')) {
      try {
        await api.knowledge.deleteDocument(id);
        setDocuments((prev) => prev.filter((d) => d.id !== id));
        toast.success('Document deleted successfully');
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to delete document';
        toast.error(errorMessage);
      }
    }
  };

  // --- Snippets Handlers ---
  const handleEditSnippet = (snippet?: TextSnippet) => {
    if (snippet) {
      setEditingSnippet(snippet);
    } else {
      setEditingSnippet({ title: '', content: '', tags: [], botId: selectedBotId! });
    }
    setIsEditorOpen(true);
  };

  const handleSaveSnippet = async () => {
    if (!selectedBotId || !editingSnippet.title || !editingSnippet.content) {
      toast.error('Please fill in title and content');
      return;
    }
    
    setIsSaving(true);
    try {
      // Process tags: ensure it's an array
      let tagsArray: string[] = [];
      if (editingSnippet.tags) {
        if (Array.isArray(editingSnippet.tags)) {
          tagsArray = editingSnippet.tags.filter(Boolean);
        } else if (typeof editingSnippet.tags === 'string') {
          // Handle comma-separated string
          tagsArray = editingSnippet.tags
            .split(',')
            .map((t) => t.trim())
            .filter(Boolean);
        }
      }
      
      const snippetData = {
        title: editingSnippet.title.trim(),
        content: editingSnippet.content.trim(),
        tags: tagsArray,
        botId: selectedBotId,
        ...(editingSnippet.id && { id: editingSnippet.id }),
      };
      
      console.log('[ManageKnowledge] Saving snippet:', snippetData);
      const saved = await api.knowledge.saveSnippet(snippetData);
      
      if (editingSnippet.id) {
        setSnippets((prev) => prev.map((s) => (s.id === saved.id ? saved : s)));
        toast.success('Snippet updated successfully');
      } else {
        setSnippets((prev) => [saved, ...prev]);
        toast.success('Snippet created successfully');
      }
      setIsEditorOpen(false);
    } catch (error: any) {
      console.error('[ManageKnowledge] Save snippet error:', error);
      const errorMessage = error?.message || error?.details?.message || 'Failed to save snippet';
      toast.error(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteSnippet = async (id: string) => {
    if (window.confirm('Delete this snippet?')) {
      try {
        await api.knowledge.deleteSnippet(id);
        setSnippets((prev) => prev.filter((s) => s.id !== id));
        toast.success('Snippet deleted successfully');
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to delete snippet';
        toast.error(errorMessage);
      }
    }
  };

  const handleGenerateAI = async () => {
    if (!editingSnippet.title) {
      toast.error('Please enter a title first.');
      return;
    }
    setIsGenerating(true);
    try {
      const prompt = `Generate comprehensive content about: ${editingSnippet.title}. Make it informative, well-structured, and suitable for a knowledge base.`;
      const response = await generateBotResponse(
        'gemini-2.5-flash',
        prompt,
        'You are a helpful content generator that creates informative, structured text for knowledge bases.'
      );
      if (response.text) {
        setEditingSnippet((prev) => ({ ...prev, content: response.text }));
        toast.success('Content generated successfully');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate content';
      toast.error(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  // --- Rendering ---

  if (!selectedBotId) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center space-y-4">
        <div className="w-20 h-20 rounded-3xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
          <Bot className="w-10 h-10 text-gray-400" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">No Bot Selected</h2>
        <p className="text-gray-500 max-w-md">
          Please select a bot from the header to manage its knowledge base.
        </p>
      </div>
    );
  }

  const filteredDocs = documents.filter((d) =>
    d.name.toLowerCase().includes(searchTerm.toLowerCase())
  );
  const filteredSnippets = snippets.filter((s) =>
    s.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Knowledge Base</h1>
          <p className="text-gray-500 dark:text-gray-400">
            Manage{' '}
            <span className="font-medium text-gray-900 dark:text-gray-200">
              {getSelectedBot()?.name}'s
            </span>{' '}
            brain.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Tabs tabs={TABS} activeTab={activeTab} onChange={setActiveTab} />
          <Button
            variant="secondary"
            icon={
              isSyncing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <CheckCircle className="w-4 h-4" />
              )
            }
            onClick={handleSync}
            disabled={isSyncing}
          >
            Sync
          </Button>
        </div>
      </div>

      {/* === FILES TAB === */}
      {activeTab === 'files' && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2">
          {/* Upload Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={cn(
              'border-2 border-dashed rounded-xl p-8 md:p-10 transition-all duration-200 text-center cursor-pointer',
              isDragging
                ? 'border-primary bg-primary/5 scale-[1.01] shadow-lg'
                : 'border-black/10 dark:border-white/10 bg-white/50 dark:bg-gray-900/50 hover:bg-gray-50 dark:hover:bg-gray-900 hover:border-primary/50'
            )}
          >
            <div className="flex flex-col items-center gap-4">
              <div
                className={cn(
                  'w-12 h-12 rounded-full flex items-center justify-center transition-colors',
                  isDragging
                    ? 'bg-primary/10 text-primary'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-400'
                )}
              >
                <Upload className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-gray-900 dark:text-white">
                  {isDragging ? 'Drop file now' : 'Upload new document'}
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  PDF, TXT, DOCX (Max 10MB)
                </p>
              </div>
              <div className="relative mt-2">
                <Button size="sm" variant="primary">
                  Select File
                </Button>
                <input
                  type="file"
                  className="absolute inset-0 opacity-0 cursor-pointer"
                  onChange={handleFileSelect}
                  accept=".pdf,.txt,.docx,.md"
                />
              </div>
            </div>
          </div>

          {/* File List */}
          <Card className="border-black/5 dark:border-white/5">
            <CardHeader className="border-b border-black/5 dark:border-white/5 py-3">
              <div className="flex justify-between items-center">
                <CardTitle className="text-sm">Documents ({documents.length})</CardTitle>
                <Input
                  placeholder="Search..."
                  startIcon={<Search className="w-3 h-3" />}
                  className="h-8 w-48 text-xs"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {isDocsLoading ? (
                <div className="p-8 text-center">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto text-primary" />
                </div>
              ) : filteredDocs.length === 0 ? (
                <div className="p-8 text-center text-gray-500 text-sm">No files uploaded yet.</div>
              ) : (
                <div className="divide-y divide-black/5 dark:divide-white/5">
                  {filteredDocs.map((doc) => (
                    <div
                      key={doc.id}
                      className="p-3 px-4 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors group"
                    >
                      <div className="w-8 h-8 rounded bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center shrink-0 text-blue-600 dark:text-blue-400">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {doc.name}
                        </h4>
                        <div className="flex items-center gap-2 text-[10px] text-gray-500">
                          <span className="uppercase">{doc.type}</span> • <span>{doc.size}</span> •{' '}
                          <span>{formatDate(doc.uploadDate)}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {doc.status === 'indexing' ? (
                          <Badge variant="warning" className="h-5 text-[10px]">
                            <Loader2 className="w-2.5 h-2.5 mr-1 animate-spin" /> Indexing
                          </Badge>
                        ) : (
                          <Badge variant="success" className="h-5 text-[10px]">
                            Ready
                          </Badge>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-gray-400 hover:text-red-500"
                          onClick={() => handleDeleteDoc(doc.id)}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* === SNIPPETS TAB === */}
      {activeTab === 'snippets' && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2">
          <div className="flex justify-between items-center">
            <div className="relative">
              <Search className="absolute left-2.5 top-2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search snippets..."
                className="h-9 pl-9 pr-4 rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-gray-900 text-sm focus:ring-2 focus:ring-primary/20 outline-none w-64"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Button onClick={() => handleEditSnippet()} icon={<Plus className="w-4 h-4" />}>
              Add Snippet
            </Button>
          </div>

          {isSnippetsLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : filteredSnippets.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 border-2 border-dashed border-black/10 dark:border-white/10 rounded-xl bg-gray-50/50 dark:bg-gray-900/50">
              <FileText className="w-10 h-10 text-gray-300 mb-3" />
              <p className="text-gray-500 font-medium">No snippets found</p>
              <Button
                variant="ghost"
                size="sm"
                className="mt-2 text-primary"
                onClick={() => handleEditSnippet()}
              >
                Create your first snippet
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredSnippets.map((snippet) => (
                <Card
                  key={snippet.id}
                  className="group hover:shadow-md transition-all border-black/5 dark:border-white/5"
                >
                  <CardContent className="p-5 relative">
                    <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0"
                        onClick={() => handleEditSnippet(snippet)}
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 text-red-500 hover:bg-red-50"
                        onClick={() => handleDeleteSnippet(snippet.id)}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900 dark:text-white truncate flex-1">
                        {snippet.title}
                      </h3>
                      {snippet.tags.includes('correction') && (
                        <span
                          className="w-2 h-2 rounded-full bg-amber-500"
                          title="Correction from Monitoring"
                        />
                      )}
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 line-clamp-3 min-h-[3.75rem]">
                      {snippet.content}
                    </p>
                    <div className="flex items-center gap-2 mt-4 flex-wrap">
                      {snippet.tags.map((tag) => (
                        <span
                          key={tag}
                          className={cn(
                            'text-[10px] px-2 py-0.5 rounded-full flex items-center',
                            tag === 'correction'
                              ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                              : 'bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-300'
                          )}
                        >
                          <Tag className="w-2.5 h-2.5 mr-1 opacity-50" /> {tag}
                        </span>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* === SNIPPET EDITOR MODAL === */}
      <AnimatePresence>
        {isEditorOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-40"
              onClick={() => setIsEditorOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, x: '100%' }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed top-0 right-0 h-full w-full sm:w-[500px] bg-white dark:bg-gray-900 shadow-2xl z-50 border-l border-black/5 dark:border-white/5 flex flex-col"
            >
              <div className="flex items-center justify-between p-6 border-b border-black/5 dark:border-white/5">
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                  {editingSnippet.id ? 'Edit Snippet' : 'Add New Snippet'}
                </h2>
                <Button variant="icon" size="md" onClick={() => setIsEditorOpen(false)}>
                  <X className="w-5 h-5" />
                </Button>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                <Input
                  label="Title"
                  placeholder="e.g. Return Policy"
                  required
                  value={editingSnippet.title}
                  onChange={(e) =>
                    setEditingSnippet((prev) => ({ ...prev, title: e.target.value }))
                  }
                />

                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <Label>Content</Label>
                    <button
                      onClick={handleGenerateAI}
                      disabled={isGenerating}
                      className={cn(
                        'text-xs flex items-center gap-1.5 px-2.5 py-1 rounded-full font-medium transition-all',
                        'bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white',
                        'hover:shadow-md hover:scale-105 active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed'
                      )}
                    >
                      {isGenerating ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <Sparkles className="w-3 h-3" />
                      )}
                      {isGenerating ? 'Generating...' : 'Generate with AI'}
                    </button>
                  </div>
                  <Textarea
                    placeholder="Enter the snippet text here..."
                    rows={10}
                    value={editingSnippet.content}
                    onChange={(e) =>
                      setEditingSnippet((prev) => ({ ...prev, content: e.target.value }))
                    }
                    className={cn(
                      'font-mono text-sm transition-all duration-500',
                      isGenerating && 'opacity-50 blur-[1px]'
                    )}
                  />
                </div>

                <div className="space-y-1.5">
                  <Label>Tags (comma separated)</Label>
                  <Input
                    placeholder="policy, support, billing"
                    value={editingSnippet.tags?.join(', ')}
                    onChange={(e) =>
                      setEditingSnippet((prev) => ({
                        ...prev,
                        tags: e.target.value
                          .split(',')
                          .map((t) => t.trim())
                          .filter(Boolean),
                      }))
                    }
                  />
                </div>
              </div>

              <div className="p-6 border-t border-black/5 dark:border-white/5 bg-gray-50/50 dark:bg-gray-900/50 flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setIsEditorOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSaveSnippet} isLoading={isSaving}>
                  Save Snippet
                </Button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

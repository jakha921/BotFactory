import React, { useState, useEffect } from 'react';
import { Book, Upload, File, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { api } from '../services/api';
import { Document } from '../types';

interface KnowledgeSettingsProps {
  botId: string;
}

export const KnowledgeSettings: React.FC<KnowledgeSettingsProps> = ({ botId }) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const docs = await api.knowledge.documents(botId);
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      toast.error('Failed to fetch documents.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [botId]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setFile(event.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error('Please select a file to upload.');
      return;
    }

    setIsUploading(true);
    try {
      await api.knowledge.upload(file, botId);
      toast.success('Document uploaded successfully.');
      setFile(null);
      fetchDocuments(); // Refresh the list
    } catch (error) {
      console.error('Failed to upload document:', error);
      toast.error('Failed to upload document.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Card className="border-black/5 dark:border-white/5 animate-in fade-in slide-in-from-left-4 duration-300">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Book className="w-5 h-5 text-green-500" />
          Knowledge Base
        </CardTitle>
        <CardDescription>Upload documents to provide context to your bot.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <input type="file" onChange={handleFileChange} />
            <Button onClick={handleUpload} isLoading={isUploading} icon={<Upload className="w-4 h-4" />}>
              Upload
            </Button>
          </div>
          <p className="text-xs text-gray-500">Supported formats: .pdf, .docx, .txt</p>
        </div>

        <div className="space-y-4">
          <h3 className="text-lg font-medium">Uploaded Documents</h3>
          {isLoading ? (
            <div className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Loading documents...</span>
            </div>
          ) : documents.length > 0 ? (
            <ul className="space-y-2">
              {documents.map((doc) => (
                <li key={doc.id} className="flex items-center gap-2 p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                  <File className="w-4 h-4" />
                  <span>{doc.name}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">No documents uploaded yet.</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

import React, { useState, useEffect } from 'react';
import { Book, Upload, File, Loader2, Eye } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { api } from '../services/api';
import { Document } from '../types';
import { ChunkViewer } from '../components/ui/ChunkViewer';

interface KnowledgeSettingsProps {
  botId: string;
}

export const KnowledgeSettings: React.FC<KnowledgeSettingsProps> = ({ botId }) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<{ id: string; name: string } | null>(null);

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
    <div className="space-y-6 animate-in fade-in slide-in-from-left-4 duration-300">
      {/* Upload Card */}
      <Card className="border-black/5 dark:border-white/5">
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
                  <li key={doc.id} className="flex items-center justify-between p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
                    <div className="flex items-center gap-2 flex-1">
                      <File className="w-4 h-4" />
                      <span className="font-medium">{doc.name}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        doc.status === 'ready'
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                          : doc.status === 'indexing'
                          ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                          : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                      }`}>
                        {doc.status}
                      </span>
                    </div>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setSelectedDocument({ id: doc.id, name: doc.name })}
                      icon={<Eye className="w-4 h-4" />}
                    >
                      View Chunks
                    </Button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">No documents uploaded yet.</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Chunk Viewer */}
      {selectedDocument && (
        <ChunkViewer
          documentId={selectedDocument.id}
          documentName={selectedDocument.name}
        />
      )}

      {/* Back button when viewing chunks */}
      {selectedDocument && (
        <Button
          variant="secondary"
          onClick={() => setSelectedDocument(null)}
        >
          ← Back to Documents
        </Button>
      )}
    </div>
  );
};

'use client';

import { useState, useRef } from 'react';
import { uploadDocument } from '@/lib/api';
import { useApp } from '@/contexts/AppContext';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Upload, FileText, X, CheckCircle, AlertCircle } from 'lucide-react';

export function FileUpload() {
  const { selectedCompany, selectedUser } = useApp();
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState<Array<{ name: string; status: 'success' | 'error'; message?: string }>>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0 || !selectedUser) return;

    setUploading(true);
    setProgress(0);
    const results = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      try {
        const result = await uploadDocument(file, selectedCompany?.id, selectedUser.id);
        results.push({ name: file.name, status: 'success' as const });
        setProgress(Math.round(((i + 1) / files.length) * 100));
      } catch (err) {
        results.push({
          name: file.name,
          status: 'error' as const,
          message: err instanceof Error ? err.message : 'Upload failed'
        });
      }
    }

    setUploadedFiles(results);
    setUploading(false);
    setProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const clearResults = () => {
    setUploadedFiles([]);
  };

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-medium flex items-center gap-2">
          <Upload className="w-4 h-4" />
          Upload Documents
        </h3>
        {uploadedFiles.length > 0 && (
          <Button variant="ghost" size="sm" onClick={clearResults}>
            Clear
          </Button>
        )}
      </div>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        multiple
        onChange={handleFileSelect}
        disabled={uploading || !selectedUser}
        className="hidden"
      />
      <Button
        onClick={() => fileInputRef.current?.click()}
        disabled={uploading || !selectedUser}
        className="w-full"
        variant="outline"
      >
        <FileText className="w-4 h-4 mr-2" />
        {uploading ? 'Uploading...' : 'Select PDF Files'}
      </Button>
      {uploading && (
        <div className="mt-3">
          <Progress value={progress} />
          <p className="text-xs text-muted-foreground mt-1">Uploading... {progress}%</p>
        </div>
      )}
      {uploadedFiles.length > 0 && (
        <div className="mt-3 space-y-2">
          {uploadedFiles.map((file, idx) => (
            <div
              key={idx}
              className={`flex items-center gap-2 p-2 rounded-lg ${
                file.status === 'success'
                  ? 'bg-green-50 dark:bg-green-950'
                  : 'bg-red-50 dark:bg-red-950'
              }`}
            >
              {file.status === 'success' ? (
                <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
              ) : (
                <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
              )}
              <div className="flex-1 min-w-0">
                <span className="text-sm font-medium">{file.name}</span>
                {file.message && (
                  <span className="text-xs text-muted-foreground ml-2">{file.message}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      {!selectedUser && (
        <p className="text-xs text-muted-foreground mt-2">Select a user to upload documents</p>
      )}
    </Card>
  );
}

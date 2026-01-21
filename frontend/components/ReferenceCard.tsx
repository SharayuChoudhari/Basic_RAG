'use client';

import { Card } from '@/components/ui/card';
import { FileText } from 'lucide-react';

interface ReferenceCardProps {
  reference: {
    document_id?: string;
    chunk_index?: number;
    content?: string;
    similarity_score?: number;
    metadata?: Record<string, any>;
  };
}

export function ReferenceCard({ reference }: ReferenceCardProps) {
  const filename = reference.metadata?.filename || 'Unknown Document';
  const chunkIndex = reference.chunk_index !== undefined ? reference.chunk_index + 1 : 0;

  return (
    <Card className="p-3 bg-muted/50">
      <div className="flex items-center gap-2">
        <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0" />
        <span className="text-xs font-medium">
          {filename} - Chunk {chunkIndex}
        </span>
      </div>
    </Card>
  );
}

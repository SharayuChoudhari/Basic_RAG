'use client';

import { useState } from 'react';
import { DocumentInfo } from '@/types/api';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileText, Check, X } from 'lucide-react';

interface DocumentSelectorProps {
  documents: DocumentInfo[];
  selectedDocumentIds: string[];
  onSelectionChange: (selectedIds: string[]) => void;
  onClose: () => void;
  onConfirm: () => void;
}

export function DocumentSelector({
  documents,
  selectedDocumentIds,
  onSelectionChange,
  onClose,
  onConfirm,
}: DocumentSelectorProps) {
  const [selectAll, setSelectAll] = useState(false);

  const handleToggleDocument = (documentId: string) => {
    if (selectedDocumentIds.includes(documentId)) {
      onSelectionChange(selectedDocumentIds.filter(id => id !== documentId));
    } else {
      onSelectionChange([...selectedDocumentIds, documentId]);
    }
  };

  const handleSelectAll = () => {
    if (selectAll) {
      onSelectionChange([]);
      setSelectAll(false);
    } else {
      onSelectionChange(documents.map(doc => doc.document_id));
      setSelectAll(true);
    }
  };

  const selectedCount = selectedDocumentIds.length;
  const totalCount = documents.length;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background rounded-lg shadow-lg max-w-2xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div>
            <h2 className="text-lg font-semibold">Select Documents</h2>
            <p className="text-sm text-muted-foreground">
              {selectedCount} of {totalCount} documents selected
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Select All Button */}
        <div className="p-4 border-b">
          <Button
            variant="outline"
            onClick={handleSelectAll}
            className="w-full"
          >
            {selectAll ? (
              <>
                <X className="w-4 h-4 mr-2" />
                Deselect All
              </>
            ) : (
              <>
                <Check className="w-4 h-4 mr-2" />
                Select All ({totalCount})
              </>
            )}
          </Button>
        </div>

        {/* Document List */}
        <ScrollArea className="flex-1">
          <div className="p-4 space-y-2">
            {documents.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                No documents available. Upload some documents first.
              </div>
            ) : (
              documents.map((document) => (
                <div
                  key={document.document_id}
                  className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedDocumentIds.includes(document.document_id)
                      ? 'bg-primary/10 border-primary'
                      : 'hover:bg-muted'
                  }`}
                  onClick={() => handleToggleDocument(document.document_id)}
                >
                  <div className="flex items-center gap-2">
                    <div className={`w-5 h-5 rounded border flex items-center justify-center ${
                      selectedDocumentIds.includes(document.document_id)
                        ? 'bg-primary border-primary text-primary-foreground'
                        : 'border-border'
                    }`}>
                      {selectedDocumentIds.includes(document.document_id) && (
                        <Check className="w-3 h-3" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                        <span className="font-medium truncate">
                          {document.filename}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {document.num_chunks} chunks • {new Date(document.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="p-4 border-t flex justify-between items-center">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={onConfirm}>
            Done ({selectedCount} selected)
          </Button>
        </div>
      </div>
    </div>
  );
}

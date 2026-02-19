'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageSquare, Trash2, Plus, FileText, Pencil } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { Chat } from '@/types/api';
import { DocumentSelector } from './DocumentSelector';

interface ChatSidebarProps {
  selectedChatId: string | null;
  chats: Chat[];
  documents: any[];
  onSelectChat: (chatId: string) => void;
  onNewChat: (selectedDocumentIds?: string[]) => void;
  onDeleteChat: (chatId: string) => void;
  onRenameChat: (chatId: string, newTitle: string) => void;
}

const truncateTitle = (title: string, maxLength: number = 20): string => {
  if (!title) return 'Untitled Chat';
  return title.length > maxLength ? title.slice(0, maxLength) + '...' : title;
};

export function ChatSidebar({
  selectedChatId,
  chats,
  documents,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  onRenameChat,
}: ChatSidebarProps) {
  const [showDocumentSelector, setShowDocumentSelector] = useState(false);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');

  const handleNewChat = () => {
    setShowDocumentSelector(true);
    setSelectedDocumentIds([]);
  };

  const handleConfirmDocumentSelection = () => {
    onNewChat(selectedDocumentIds);
    setShowDocumentSelector(false);
    setSelectedDocumentIds([]);
  };

  const handleStartEdit = (chatId: string, currentTitle: string) => {
    setEditingChatId(chatId);
    setEditingTitle(currentTitle || 'Untitled Chat');
  };

  const handleSaveEdit = (chatId: string) => {
    if (editingTitle.trim()) {
      onRenameChat(chatId, editingTitle.trim());
    }
    setEditingChatId(null);
    setEditingTitle('');
  };

  const handleCancelEdit = () => {
    setEditingChatId(null);
    setEditingTitle('');
  };

  const handleKeyDown = (e: React.KeyboardEvent, chatId: string) => {
    if (e.key === 'Enter') {
      handleSaveEdit(chatId);
    } else if (e.key === 'Escape') {
      handleCancelEdit();
    }
  };

  return (
    <div className="w-full border-r bg-muted/10 flex flex-col flex-1 overflow-hidden">
      <div className="p-4 border-b">
        <Button onClick={handleNewChat} className="w-full" variant="outline">
          <Plus className="w-4 h-4 mr-2" />
          New Chat
        </Button>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {chats.length === 0 ? (
            <div className="text-sm text-muted-foreground p-4 text-center">
              No chats yet
            </div>
          ) : (
            chats.map((chat) => (
              <div
                key={chat.id}
                onClick={() => onSelectChat(chat.id)}
                className={`w-full text-left p-3 rounded-lg transition-colors cursor-pointer ${
                  selectedChatId === chat.id
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-muted'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <MessageSquare className="w-4 h-4 flex-shrink-0" />
                    {editingChatId === chat.id ? (
                      <input
                        type="text"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        onBlur={() => handleSaveEdit(chat.id)}
                        onKeyDown={(e) => handleKeyDown(e, chat.id)}
                        className="bg-background text-foreground px-2 py-1 rounded text-sm w-full"
                        autoFocus
                        onClick={(e) => e.stopPropagation()}
                      />
                    ) : (
                      <span
                        className="font-medium truncate"
                        onDoubleClick={() => handleStartEdit(chat.id, chat.title || 'Untitled Chat')}
                      >
                        {truncateTitle(chat.title || 'Untitled Chat')}
                      </span>
                    )}
                  </div>
                  <div className="flex gap-1 flex-shrink-0">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleStartEdit(chat.id, chat.title || 'Untitled Chat');
                      }}
                    >
                      <Pencil className="w-3 h-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteChat(chat.id);
                      }}
                    >
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
                <div className="text-xs text-muted-foreground">
                  {formatDistanceToNow(new Date(chat.created_at), { addSuffix: true })}
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Document Selector Modal */}
      {showDocumentSelector && (
        <DocumentSelector
          documents={documents}
          selectedDocumentIds={selectedDocumentIds}
          onSelectionChange={setSelectedDocumentIds}
          onClose={() => setShowDocumentSelector(false)}
          onConfirm={handleConfirmDocumentSelection}
        />
      )}
    </div>
  );
}

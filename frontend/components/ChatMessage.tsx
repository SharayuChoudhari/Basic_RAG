'use client';

import { ChatMessage as ChatMessageType } from '@/types/api';
import { Card } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Bot, User } from 'lucide-react';
import { ReferenceCard } from './ReferenceCard';

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const references = message.context_document?.documents || [];
  const hasResponse = !!message.response;

  return (
    <div className="space-y-4">
      {/* User Query Bubble */}
      <div className="flex gap-3 justify-end">
        <div className="max-w-[80%]">
          <Card className="p-4 bg-primary text-primary-foreground">
            <div className="whitespace-pre-wrap break-words">
              {message.chat_query}
            </div>
          </Card>
          <div className="text-xs text-muted-foreground mt-1 text-right">
            {new Date(message.created_at).toLocaleString()}
          </div>
        </div>
        <Avatar className="w-8 h-8 flex-shrink-0">
          <AvatarFallback>
            <User className="w-5 h-5" />
          </AvatarFallback>
        </Avatar>
      </div>

      {/* AI Response Bubble */}
      {hasResponse && (
        <div className="flex gap-3 justify-start">
          <Avatar className="w-8 h-8 flex-shrink-0">
            <AvatarFallback>
              <Bot className="w-5 h-5" />
            </AvatarFallback>
          </Avatar>
          <div className="max-w-[80%]">
            <Card className="p-4 bg-muted">
              <div className="whitespace-pre-wrap break-words">
                {message.response}
              </div>
            </Card>
            {references.length > 0 && (
              <div className="mt-2 space-y-2">
                <div className="text-xs font-medium text-muted-foreground">References:</div>
                {references.map((ref: any, idx: number) => (
                  <ReferenceCard key={idx} reference={ref} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

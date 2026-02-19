'use client';

import { ChatMessage as ChatMessageType } from '@/types/api';
import { Card } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Bot, User, Loader2 } from 'lucide-react';
import { ReferenceCard } from '@/components/ReferenceCard';

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const references = message.context_document?.documents || [];
  const hasResponse = !!message.response;
  const isProcessing = message.status === 'processing';
  const isError = message.status === 'error';

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
      {isProcessing && (
        <div className="flex gap-3 justify-start">
          <Avatar className="w-8 h-8 flex-shrink-0">
            <AvatarFallback>
              <Bot className="w-5 h-5" />
            </AvatarFallback>
          </Avatar>
          <div className="max-w-[80%]">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Processing...</span>
            </div>
          </div>
        </div>
      )}
      {isError && (
        <div className="flex gap-3 justify-start">
          <Avatar className="w-8 h-8 flex-shrink-0">
            <AvatarFallback>
              <Bot className="w-5 h-5" />
            </AvatarFallback>
          </Avatar>
          <div className="max-w-[80%]">
            <div className="text-destructive">
              Failed to generate response. Please try again.
            </div>
          </div>
        </div>
      )}
      {!isProcessing && !isError && hasResponse && (
        <div className="flex gap-3 justify-start">
          <Avatar className="w-8 h-8 flex-shrink-0">
            <AvatarFallback>
              <Bot className="w-5 h-5" />
            </AvatarFallback>
          </Avatar>
          <div className="max-w-[80%]">
            <Card className="p-4">
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

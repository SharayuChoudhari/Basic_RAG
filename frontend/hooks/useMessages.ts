'use client';

import { useState, useEffect } from 'react';
import { fetchMessagesByChat, sendQuery } from '@/lib/api';
import { ChatMessage, ChatQueryResponse } from '@/types/api';

export function useMessages(chatId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    if (!chatId) return;
    setLoading(true);
    try {
      const data = await fetchMessagesByChat(chatId);
      setMessages(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch messages');
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (userId: string, query: string, onFirstMessage?: (query: string) => void) => {
    if (!chatId) throw new Error('No chat selected');
    setSending(true);
    try {
      const isFirstMessage = messages.length === 0;
      
      const response = await sendQuery(userId, chatId, query);
      
      // Add message with both query and response (backend now handles status)
      const newMessage: ChatMessage = {
        id: response.message_id,
        chat_id: response.chat_id,
        chat_query: response.query,
        context_document: { documents: response.context_documents },
        response: response.response,
        created_at: response.created_at,
        status: 'done',  // Backend sets this
      };
      setMessages((prev) => [...prev, newMessage]);
      
      // If this was the first message, trigger auto-rename callback
      if (isFirstMessage && onFirstMessage) {
        onFirstMessage(query);
      }
      
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      throw err;
    } finally {
      setSending(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [chatId]);

  return { messages, loading, sending, error, refresh, sendMessage };
}

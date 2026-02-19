import { useState, useEffect } from 'react';
import { fetchChatsByUser, createChat, deleteChat, renameChat as renameChatApi } from '@/lib/api';
import { Chat } from '@/types/api';

export function useChats(userId: string | null) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    if (!userId) return;
    setLoading(true);
    try {
      const data = await fetchChatsByUser(userId);
      setChats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch chats');
    } finally {
      setLoading(false);
    }
  };

  const createNewChat = async (title?: string, companyId?: string, selectedDocumentIds?: string[]) => {
    if (!userId) throw new Error('No user selected');
    const newChat = await createChat(userId, title, companyId, selectedDocumentIds);
    setChats((prev) => [newChat, ...prev]);
    return newChat;
  };

  const removeChat = async (chatId: string) => {
    await deleteChat(chatId);
    setChats((prev) => prev.filter((c) => c.id !== chatId));
  };

  const renameChat = async (chatId: string, newTitle: string) => {
    const updatedChat = await renameChatApi(chatId, newTitle);
    setChats((prev) => prev.map((c) => (c.id === chatId ? updatedChat : c)));
  };

  const updateChatTitle = (chatId: string, newTitle: string) => {
    setChats((prev) => prev.map((c) => (c.id === chatId ? { ...c, title: newTitle } : c)));
  };

  useEffect(() => {
    refresh();
  }, [userId]);

  return { chats, loading, error, refresh, createNewChat, removeChat, renameChat, updateChatTitle };
}

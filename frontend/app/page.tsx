'use client';

import { useState } from 'react';
import { useCompanies } from '@/hooks/useCompanies';
import { useUsers } from '@/hooks/useUsers';
import { useChats } from '@/hooks/useChats';
import { useMessages } from '@/hooks/useMessages';
import { useDocuments } from '@/hooks/useDocuments';
import { useApp } from '@/contexts/AppContext';
import { useAuth } from '@/contexts/AuthContext';
import { CompanyUserSelector } from '@/components/CompanyUserSelector';
import { ChatSidebar } from '@/components/ChatSidebar';
import { ChatInterface } from '@/components/ChatInterface';
import { FileUpload } from '@/components/FileUpload';

function ChatPage() {
  const { selectedCompany, selectedUser, setSelectedCompany, setSelectedUser } = useApp();
  const { setDemoUser } = useAuth();
  const { companies } = useCompanies();
  const { users } = useUsers(selectedCompany?.id);
  const { chats, createNewChat, removeChat, renameChat } = useChats(selectedUser?.id || null);
  const { documents } = useDocuments(selectedCompany?.id || null);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const { messages, sendMessage, sending } = useMessages(selectedChatId);

  const handleCompanyChange = (companyId: string) => {
    const company = companies.find((c) => c.id === companyId);
    setSelectedCompany(company || null);
    setSelectedUser(null);
    setDemoUser(null);
    setSelectedChatId(null);
  };

  const handleUserChange = (userId: string) => {
    const user = users.find((u) => u.id === userId);
    setSelectedUser(user || null);
    setDemoUser(user || null);
    setSelectedChatId(null);
  };

  const handleNewChat = async (selectedDocumentIds?: string[]) => {
    const newChat = await createNewChat('New Chat', selectedCompany?.id, selectedDocumentIds);
    setSelectedChatId(newChat.id);
  };

  const handleSelectChat = (chatId: string) => {
    setSelectedChatId(chatId);
  };

  const handleSendMessage = async (query: string) => {
    if (!selectedUser) return;
    await sendMessage(selectedUser.id, query, handleFirstMessage);
  };

  const handleFirstMessage = async (query: string) => {
    if (!selectedChatId) return;
    const first7Words = query.split(' ').slice(0, 7).join(' ');
    await renameChat(selectedChatId, first7Words);
  };

  const handleRenameChat = async (chatId: string, newTitle: string) => {
    await renameChat(chatId, newTitle);
  };

  const selectedChat = chats.find((c) => c.id === selectedChatId);

  return (
    <div className="h-screen flex flex-col">
      <header className="border-b bg-background p-4">
        <h1 className="text-2xl font-bold">RAG Chatbot</h1>
      </header>
      <div className="flex-1 flex overflow-hidden">
        <div className="w-80 flex-shrink-0 border-r flex flex-col">
          <CompanyUserSelector />
          <div className="p-4">
            <FileUpload />
          </div>
          <ChatSidebar
            selectedChatId={selectedChatId}
            chats={chats}
            documents={documents}
            onSelectChat={handleSelectChat}
            onNewChat={handleNewChat}
            onDeleteChat={removeChat}
            onRenameChat={handleRenameChat}
          />
        </div>
        <ChatInterface
          chatId={selectedChatId}
          messages={messages}
          sending={sending}
          onSendMessage={handleSendMessage}
        />
      </div>
    </div>
  );
}

export default ChatPage;

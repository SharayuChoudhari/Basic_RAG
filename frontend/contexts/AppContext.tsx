'use client';

import { createContext, useContext, useState, ReactNode } from 'react';
import { Company, User } from '@/types/api';

interface AppContextType {
  selectedCompany: Company | null;
  selectedUser: User | null;
  setSelectedCompany: (company: Company | null) => void;
  setSelectedUser: (user: User | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  return (
    <AppContext.Provider
      value={{
        selectedCompany,
        selectedUser,
        setSelectedCompany,
        setSelectedUser,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within AppProvider');
  return context;
}

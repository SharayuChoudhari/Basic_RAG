'use client';

import { useCompanies } from '@/hooks/useCompanies';
import { useUsers } from '@/hooks/useUsers';
import { useApp } from '@/contexts/AppContext';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card } from '@/components/ui/card';

export function CompanyUserSelector() {
  const { companies, loading: companiesLoading } = useCompanies();
  const { users, loading: usersLoading } = useUsers();
  const { selectedCompany, selectedUser, setSelectedCompany, setSelectedUser } = useApp();

  const handleCompanyChange = (companyId: string) => {
    const company = companies.find((c) => c.id === companyId);
    setSelectedCompany(company || null);
    setSelectedUser(null);
  };

  const handleUserChange = (userId: string) => {
    const user = users.find((u) => u.id === userId);
    setSelectedUser(user || null);
  };

  return (
    <Card className="p-4 mb-4">
      <div className="flex gap-4">
        <div className="flex-1">
          <label className="text-sm font-medium mb-2 block">Select Company</label>
          <Select
            value={selectedCompany?.id || ''}
            onValueChange={handleCompanyChange}
            disabled={companiesLoading}
          >
            <SelectTrigger>
              <SelectValue placeholder={companiesLoading ? 'Loading...' : 'Select a company'} />
            </SelectTrigger>
            <SelectContent>
              {companies.map((company) => (
                <SelectItem key={company.id} value={company.id}>
                  {company.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex-1">
          <label className="text-sm font-medium mb-2 block">Select User</label>
          <Select
            value={selectedUser?.id || ''}
            onValueChange={handleUserChange}
            disabled={!selectedCompany || usersLoading}
          >
            <SelectTrigger>
              <SelectValue
                placeholder={
                  !selectedCompany
                    ? 'Select a company first'
                    : usersLoading
                    ? 'Loading...'
                    : 'Select a user'
                }
              />
            </SelectTrigger>
            <SelectContent>
              {users.map((user) => (
                <SelectItem key={user.id} value={user.id}>
                  {user.name} ({user.email})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </Card>
  );
}

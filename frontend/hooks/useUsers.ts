import { useState, useEffect } from 'react';
import { fetchUsers, fetchUsersByCompany } from '@/lib/api';
import { User } from '@/types/api';

export function useUsers(companyId?: string) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFn = companyId ? () => fetchUsersByCompany(companyId) : fetchUsers;
    fetchFn()
      .then(setUsers)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [companyId]);

  return { users, loading, error };
}

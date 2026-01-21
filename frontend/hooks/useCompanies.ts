import { useState, useEffect } from 'react';
import { fetchCompanies } from '@/lib/api';
import { Company } from '@/types/api';

export function useCompanies() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCompanies()
      .then(setCompanies)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return { companies, loading, error };
}

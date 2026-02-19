import { useState, useEffect } from 'react';
import { fetchDocumentsByCompany } from '@/lib/api';
import { DocumentInfo } from '@/types/api';

export function useDocuments(companyId: string | null) {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    if (!companyId) return;
    setLoading(true);
    try {
      const data = await fetchDocumentsByCompany(companyId);
      setDocuments(data.documents);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch documents');
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [companyId]);

  return { documents, loading, error, refresh };
}

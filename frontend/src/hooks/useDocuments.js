import { useState, useCallback, useEffect } from 'react';
import documentApi from '../api/documentApi';

/**
 * useDocuments hook
 * Manages document list state, upload lifecycle, deletion, and enterprise stats.
 */
export function useDocuments() {
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [vectorCount, setVectorCount] = useState(0);
  const [error, setError] = useState(null);

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [docs, docStats] = await Promise.all([
        documentApi.getDocuments(),
        documentApi.getStats(),
      ]);
      setDocuments(Array.isArray(docs) ? docs : []);
      setStats(docStats || null);
      setVectorCount(docStats?.total_vectors ?? 0);
    } catch (err) {
      setError(err.message || 'Failed to load documents');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const uploadDocument = useCallback(async (file) => {
    setIsUploading(true);
    setUploadProgress(0);
    setUploadSuccess(null);
    setError(null);
    try {
      const result = await documentApi.uploadAndStoreDocument(file, (pct) => {
        setUploadProgress(pct);
      });
      setUploadSuccess(`"${file.name}" indexed — ${result.chunks_stored} chunks stored.`);
      await fetchDocuments(); // Auto-refresh list & stats
      return result;
    } catch (err) {
      setError(err.message || 'Upload failed');
      throw err;
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, [fetchDocuments]);

  const deleteDocument = useCallback(async (documentId) => {
    setError(null);
    try {
      await documentApi.deleteDocument(documentId);
      setDocuments((prev) => prev.filter((d) => d.id !== documentId));
      await fetchDocuments(); // Refresh stats after deletion
    } catch (err) {
      setError(err.message || 'Deletion failed');
    }
  }, [fetchDocuments]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return {
    documents,
    stats,
    isLoading,
    isUploading,
    uploadProgress,
    uploadSuccess,
    vectorCount,
    error,
    fetchDocuments,
    uploadDocument,
    deleteDocument,
  };
}

export default useDocuments;

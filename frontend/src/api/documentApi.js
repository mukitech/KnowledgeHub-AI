import apiClient from './apiClient';

/**
 * Document API Service
 * Interacts with backend document routes without mutating component state directly.
 */
export const documentApi = {
  /**
   * Fetch all uploaded documents from PostgreSQL.
   * @returns {Promise<Array<{ id: number, filename: string, uploaded_at: string }>>}
   */
  async getDocuments() {
    return await apiClient.get('/documents');
  },

  /**
   * Upload a PDF file, extract text, chunk, generate embeddings, and store in Qdrant.
   * @param {File} file - PDF File object to upload
   * @param {Function} [onUploadProgress] - Progress callback (percentage: number) => void
   */
  async uploadAndStoreDocument(file, onUploadProgress) {
    const formData = new FormData();
    formData.append('file', file);

    return await apiClient.post('/documents/test-store', formData, {
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(percentCompleted);
        }
      },
    });
  },

  /**
   * Delete document by ID from both Qdrant and PostgreSQL.
   * @param {number} documentId
   */
  async deleteDocument(documentId) {
    return await apiClient.delete(`/documents/${documentId}`);
  },

  /**
   * Get overall indexed vector count in Qdrant.
   */
  async getVectorCount() {
    return await apiClient.get('/documents/vector-count');
  },

  /**
   * Get aggregate document statistics (total docs, total chunks, total pages, avg chunks, last upload).
   */
  async getStats() {
    return await apiClient.get('/documents/stats');
  },

  /**
   * Return the absolute URL string to stream a PDF document for binary viewing.
   * @param {number} documentId
   * @returns {string}
   */
  getDocumentFileUrl(documentId) {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';
    return `${baseURL}/documents/${documentId}/file`;
  },
};

export default documentApi;

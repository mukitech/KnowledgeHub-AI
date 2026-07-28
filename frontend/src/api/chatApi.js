import apiClient from './apiClient';

/**
 * Chat API Service
 * Coordinates RAG chat completion requests with the FastAPI backend.
 */
export const chatApi = {
  /**
   * Send a query to the backend RAG pipeline.
   * @param {string} sessionId - Unique session identifier for memory tracking
   * @param {string} query - User question string
   * @returns {Promise<{ question: string, answer: string, sources: Array<{ document_id: number, chunk_index: number, score: number }> }>}
   */
  async sendChatMessage(sessionId, query) {
    return await apiClient.post('/chat', {
      session_id: sessionId,
      query,
    });
  },
};

export default chatApi;

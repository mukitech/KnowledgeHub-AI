import { useState, useCallback, useRef } from 'react';
import chatApi from '../api/chatApi';

/**
 * useChat hook
 * Manages chat session identity, message history, and RAG query lifecycle.
 * sessionId is generated once per browser session via native crypto.randomUUID().
 */
export function useChat() {
  const sessionId = useRef(
    sessionStorage.getItem('knowledgehub_session_id') || (() => {
      const id = crypto.randomUUID();
      sessionStorage.setItem('knowledgehub_session_id', id);
      return id;
    })()
  );

  const [messages, setMessages] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = useCallback(async (query) => {
    if (!query || !query.trim()) return;

    const userMessage = { role: 'user', content: query.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setIsThinking(true);
    setError(null);

    try {
      const response = await chatApi.sendChatMessage(sessionId.current, query.trim());
      const aiMessage = {
        role: 'assistant',
        content: response.answer,
        sources: response.sources || [],
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      const errMessage = {
        role: 'assistant',
        content: `⚠️ Error: ${err.message || 'Unable to get a response. Please check the backend.'}`,
        sources: [],
      };
      setMessages((prev) => [...prev, errMessage]);
      setError(err.message);
    } finally {
      setIsThinking(false);
    }
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isThinking,
    error,
    sendMessage,
    clearChat,
  };
}

export default useChat;

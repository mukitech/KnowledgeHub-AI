import React, { useState } from 'react';
import Navbar from './components/Navbar';
import DocumentSidebar from './components/documents/DocumentSidebar';
import ChatBox from './components/chat/ChatBox';
import { useDocuments } from './hooks/useDocuments';
import { useChat } from './hooks/useChat';

function App() {
  const {
    documents, stats, isLoading, isUploading, uploadProgress,
    vectorCount, error, uploadDocument, deleteDocument, fetchDocuments,
  } = useDocuments();

  const { messages, isThinking, sendMessage, clearChat } = useChat();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden font-sans" style={{ background: '#0f0d0a', color: '#d6d3d1' }}>
      {/* Top navbar */}
      <Navbar
        vectorCount={vectorCount}
        isLoading={isLoading}
        onRefresh={fetchDocuments}
        onToggleSidebar={() => setMobileSidebarOpen(v => !v)}
      />

      {/* Main workspace split */}
      <main className="flex-1 flex overflow-hidden relative">
        {/* Knowledge Explorer Sidebar — 30% desktop */}
        <div
          className={`${
            mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          } fixed lg:relative inset-y-0 left-0 z-40 w-[85%] sm:w-[340px] lg:w-[30%] xl:w-[28%] h-full transition-transform duration-250 ease-out`}
        >
          <DocumentSidebar
            documents={documents}
            stats={stats}
            isLoading={isLoading}
            vectorCount={vectorCount}
            onUpload={uploadDocument}
            isUploading={isUploading}
            uploadProgress={uploadProgress}
            onDelete={deleteDocument}
            onRefresh={fetchDocuments}
            error={error}
          />
        </div>

        {/* Mobile backdrop */}
        {mobileSidebarOpen && (
          <div
            onClick={() => setMobileSidebarOpen(false)}
            className="fixed inset-0 z-30 lg:hidden"
            style={{ background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }}
          />
        )}

        {/* AI Chat Workspace — 70% desktop */}
        <ChatBox
          messages={messages}
          isThinking={isThinking}
          onSend={sendMessage}
          onClear={clearChat}
        />
      </main>
    </div>
  );
}

export default App;

import React, { useState, useEffect } from 'react';
import { RequestHistoryItem, PlaygroundRequest } from '../../types';
import { Button } from '../ui';

interface RequestHistoryProps {
  onReplayRequest: (request: PlaygroundRequest) => void;
  currentRequest?: PlaygroundRequest;
}

const RequestHistory: React.FC<RequestHistoryProps> = ({
  onReplayRequest,
  currentRequest
}) => {
  const [history, setHistory] = useState<RequestHistoryItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);

  const STORAGE_KEY = 'playground_request_history';
  const MAX_HISTORY_ITEMS = 50;

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    if (currentRequest) {
      const historyItem: RequestHistoryItem = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        request: currentRequest,
      };

      setHistory(prev => {
        const newHistory = [historyItem, ...prev].slice(0, MAX_HISTORY_ITEMS);
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(newHistory));
        } catch (error) {
          console.error('Failed to save request history:', error);
        }
        return newHistory;
      });
    }
  }, [currentRequest]);

  const loadHistory = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setHistory(parsed);
      }
    } catch (error) {
      console.error('Failed to load request history:', error);
    }
  };

  const saveHistory = (newHistory: RequestHistoryItem[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newHistory));
    } catch (error) {
      console.error('Failed to save request history:', error);
    }
  };


  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  const deleteHistoryItem = (id: string) => {
    const newHistory = history.filter(item => item.id !== id);
    setHistory(newHistory);
    saveHistory(newHistory);
  };

  const filteredHistory = history.filter(item => {
    if (!searchTerm) return true;
    
    const searchLower = searchTerm.toLowerCase();
    return (
      item.request.model.toLowerCase().includes(searchLower) ||
      item.request.messages.some(msg => 
        msg.content.toLowerCase().includes(searchLower)
      ) ||
      (item.request.provider && item.request.provider.toLowerCase().includes(searchLower))
    );
  });

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
  };

  const getMessagePreview = (messages: any[]) => {
    const userMessage = messages.find(msg => msg.role === 'user');
    if (!userMessage) return 'No user message';
    
    const preview = userMessage.content.substring(0, 100);
    return preview.length < userMessage.content.length ? `${preview}...` : preview;
  };

  return (
    <div className="h-full flex flex-col bg-white border-l border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-medium text-gray-900">History</h3>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="lg:hidden text-gray-500 hover:text-gray-700"
          >
            {isExpanded ? '✕' : '☰'}
          </button>
        </div>
        
        {/* Search */}
        <div className={`space-y-3 ${isExpanded ? 'block' : 'hidden lg:block'}`}>
          <input
            type="text"
            placeholder="Search history..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          
          {history.length > 0 && (
            <Button
              onClick={clearHistory}
              variant="danger"
              size="sm"
              className="w-full"
            >
              Clear All
            </Button>
          )}
        </div>
      </div>

      {/* History List */}
      <div className={`flex-1 overflow-auto ${isExpanded ? 'block' : 'hidden lg:block'}`}>
        {filteredHistory.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            {history.length === 0 ? (
              <>
                <span className="text-2xl mb-2 block">📝</span>
                <p>No requests yet</p>
                <p className="text-sm mt-1">Your request history will appear here</p>
              </>
            ) : (
              <>
                <span className="text-2xl mb-2 block">🔍</span>
                <p>No matching requests</p>
                <p className="text-sm mt-1">Try a different search term</p>
              </>
            )}
          </div>
        ) : (
          <div className="p-2 space-y-2">
            {filteredHistory.map((item) => (
              <div
                key={item.id}
                className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 cursor-pointer group"
                onClick={() => onReplayRequest(item.request)}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-medium text-blue-600">
                      {item.request.model}
                    </span>
                    {item.request.provider && (
                      <span className="text-xs text-gray-500">
                        ({item.request.provider})
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-1">
                    <span className="text-xs text-gray-500">
                      {formatTimestamp(item.timestamp)}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteHistoryItem(item.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 text-xs"
                    >
                      ✕
                    </button>
                  </div>
                </div>
                
                <p className="text-sm text-gray-700 line-clamp-3">
                  {getMessagePreview(item.request.messages)}
                </p>
                
                <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                  <span>{item.request.messages.length} message{item.request.messages.length !== 1 ? 's' : ''}</span>
                  <div className="flex items-center space-x-2">
                    <span>T: {item.request.temperature || 0.7}</span>
                    <span>Max: {item.request.max_tokens || 1000}</span>
                  </div>
                </div>
                
                {item.response && (
                  <div className="mt-2 pt-2 border-t border-gray-100">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-green-600">✓ Completed</span>
                      {item.response.usage && (
                        <span className="text-gray-500">
                          {item.response.usage.total_tokens} tokens
                        </span>
                      )}
                    </div>
                  </div>
                )}
                
                {item.error && (
                  <div className="mt-2 pt-2 border-t border-gray-100">
                    <div className="text-xs text-red-600">
                      ✗ Error: {item.error.substring(0, 50)}...
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {history.length > 0 && (
        <div className={`p-3 border-t border-gray-200 text-xs text-gray-500 ${isExpanded ? 'block' : 'hidden lg:block'}`}>
          {filteredHistory.length} of {history.length} requests
          {history.length >= MAX_HISTORY_ITEMS && (
            <div className="mt-1 text-yellow-600">
              History limited to {MAX_HISTORY_ITEMS} items
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RequestHistory;

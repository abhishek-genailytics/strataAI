import React, { useState, useRef, useEffect } from "react";
import { 
  Send, 
  Settings, 
  MessageSquare,
  User,
  Bot,
  Menu,
  X
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { ModelConfigCard } from "../components/playground/ModelConfigCard";
import { apiService } from "../services/api";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  isLoading?: boolean;
}

export const Playground: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [userInput, setUserInput] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("You are a helpful assistant.");
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedModel, setSelectedModel] = useState("");
  const [modelConfig, setModelConfig] = useState({
    temperature: 0.7,
    maxTokens: 2500,
    streaming: true,
  });
  const [showSidebar, setShowSidebar] = useState(true);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [previousProvider, setPreviousProvider] = useState<string | null>(null);
  const [chatSessions, setChatSessions] = useState<any[]>([]);
  const [hasMoreSessions, setHasMoreSessions] = useState(true);
  const [loadingMoreSessions, setLoadingMoreSessions] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load chat sessions on component mount
  useEffect(() => {
    loadChatSessions();
  }, []);

  // Detect provider changes and create new session if needed
  useEffect(() => {
    if (selectedModel) {
      const currentProvider = selectedModel.split('/')[0];
      if (previousProvider && previousProvider !== currentProvider) {
        // Provider changed, create new session
        handleProviderChange(currentProvider);
      }
      setPreviousProvider(currentProvider);
    }
  }, [selectedModel]);

  const loadChatSessions = async (reset: boolean = true) => {
    try {
      const offset = reset ? 0 : chatSessions.length;
      const response = await apiService.getChatSessions(20, offset); // Increase limit to see more sessions
      console.log('Chat sessions loaded:', response.data?.length || 0);
      if (response.data) {
        if (reset) {
          setChatSessions(response.data);
        } else {
          setChatSessions(prev => [...prev, ...(response.data || [])]);
        }
        setHasMoreSessions(response.data.length === 20);
      }
    } catch (error) {
      console.error('Error loading chat sessions:', error);
    }
  };

  const loadMoreSessions = async () => {
    if (loadingMoreSessions || !hasMoreSessions) return;
    setLoadingMoreSessions(true);
    await loadChatSessions(false);
    setLoadingMoreSessions(false);
  };

  const handleProviderChange = async (newProvider: string) => {
    // Clear current messages and start fresh session
    setMessages([]);
    setCurrentSessionId(null);
    console.log(`Provider changed to ${newProvider}, starting new session`);
  };

  const loadSessionMessages = async (sessionId: string) => {
    try {
      const response = await apiService.getSessionMessages(sessionId);
      if (response.data) {
        const sessionMessages: Message[] = response.data.map((msg: any) => ({
          id: msg.id,
          role: msg.role as "user" | "assistant" | "system",
          content: msg.content,
          timestamp: new Date(msg.created_at)
        }));
        setMessages(sessionMessages);
        setCurrentSessionId(sessionId);
      }
    } catch (error) {
      console.error('Error loading session messages:', error);
    }
  };

  const handleSessionSelect = async (sessionId: string) => {
    await loadSessionMessages(sessionId);
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [userInput]);

  const handleSendMessage = async () => {
    if (!userInput.trim() || !selectedModel || isGenerating) return;

    const newUserMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: userInput,
      timestamp: new Date(),
    };

    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages((prev) => [...prev, newUserMessage, loadingMessage]);
    setUserInput("");
    setIsGenerating(true);

    try {
      // Prepare messages for API
      const apiMessages = messages
        .filter(msg => !msg.isLoading)
        .concat([newUserMessage])
        .map(msg => ({
          role: msg.role,
          content: msg.content
        }));

      // Add system message if it's different from default
      if (systemPrompt && systemPrompt !== "You are a helpful assistant.") {
        apiMessages.unshift({
          role: "system",
          content: systemPrompt
        });
      }

      const requestData = {
        model: selectedModel,
        messages: apiMessages,
        temperature: modelConfig.temperature,
        max_tokens: modelConfig.maxTokens,
        stream: modelConfig.streaming,
        session_id: currentSessionId
      };

      const response = await apiService.playgroundChatCompletion(requestData);
      
      if (response.error) {
        throw new Error(response.error);
      }

      // Update current session ID from response
      if (response.data?.session_id) {
        setCurrentSessionId(response.data.session_id);
      }

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.data?.choices[0]?.message?.content || "No response generated",
        timestamp: new Date(),
      };

      // Replace loading message with actual response
      setMessages((prev) => prev.slice(0, -1).concat([aiResponse]));
      
      // Reload chat sessions to get updated list
      await loadChatSessions();
    } catch (error) {
      console.error("Error generating response:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Error: ${error instanceof Error ? error.message : "Failed to generate response"}`,
        timestamp: new Date(),
      };
      setMessages((prev) => prev.slice(0, -1).concat([errorMessage]));
    } finally {
      setIsGenerating(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const MessageBubble = ({ message }: { message: Message }) => {
    const isUser = message.role === 'user';
    
    return (
      <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
        <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            isUser ? 'bg-blue-500 ml-3' : 'bg-gray-200 mr-3'
          }`}>
            {isUser ? (
              <User className="w-4 h-4 text-white" />
            ) : (
              <Bot className="w-4 h-4 text-gray-600" />
            )}
          </div>
          <div className={`rounded-2xl px-4 py-2 ${
            isUser 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-100 text-gray-900'
          }`}>
            {message.isLoading ? (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            ) : (
              <div className="whitespace-pre-wrap">{message.content}</div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="w-full flex bg-white" style={{ height: '100vh', overflow: 'hidden' }}>
      {/* Sidebar */}
      {showSidebar && (
        <div className="w-80 border-r border-gray-200 bg-gray-50 flex flex-col">
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Configuration</h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSidebar(false)}
              className="text-gray-500"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {/* Model Configuration */}
            <div className="mb-6">
              <ModelConfigCard
                selectedModel={selectedModel}
                onModelChange={setSelectedModel}
                modelConfig={modelConfig}
                onConfigChange={setModelConfig}
                currentSessionId={currentSessionId}
                onSessionSelect={handleSessionSelect}
              />
            </div>

            {/* System Prompt */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                System Prompt
              </label>
              <textarea
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                rows={4}
                placeholder="Enter system prompt..."
              />
            </div>

            {/* Chat History */}
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Chat History</h3>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {chatSessions.map((session) => (
                  <button
                    key={session.id}
                    onClick={() => handleSessionSelect(session.id)}
                    className={`w-full text-left p-2 rounded-lg text-sm hover:bg-gray-100 transition-colors ${
                      currentSessionId === session.id ? 'bg-blue-50 border border-blue-200' : 'bg-white border border-gray-200'
                    }`}
                  >
                    <div className="font-medium text-gray-900 truncate">
                      {session.session_name || 'New Chat'}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {session.provider}/{session.model} • {session.message_count || 0} messages
                    </div>
                  </button>
                ))}
                {hasMoreSessions && (
                  <button
                    onClick={loadMoreSessions}
                    disabled={loadingMoreSessions}
                    className="w-full p-2 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
                  >
                    {loadingMoreSessions ? 'Loading...' : 'Load More'}
                  </button>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-2">
              <Button
                variant="outline"
                onClick={() => {
                  setMessages([]);
                  setCurrentSessionId(null);
                }}
                className="w-full"
              >
                New Chat
              </Button>
              <Button
                variant="outline"
                onClick={() => setMessages([])}
                className="w-full"
                disabled={messages.length === 0}
              >
                Clear Current Chat
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 flex-shrink-0">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSidebar(!showSidebar)}
              className="text-gray-600"
            >
              <Menu className="w-5 h-5" />
            </Button>
            <h1 className="text-xl font-semibold text-gray-900">Playground</h1>
            <span className="text-sm text-gray-500">
              {selectedModel || "No model selected"}
            </span>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 text-lg mb-2">Start a conversation</p>
                <p className="text-gray-400 text-sm">
                  {selectedModel ? "Type a message below to get started" : "Select a model first"}
                </p>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area - Fixed at bottom */}
        <div className="border-t border-gray-200 p-4 flex-shrink-0">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-end space-x-3">
              <div className="flex-1">
                <textarea
                  ref={textareaRef}
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={selectedModel ? "Type your message..." : "Select a model first"}
                  disabled={!selectedModel || isGenerating}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none disabled:bg-gray-100 disabled:cursor-not-allowed"
                  rows={1}
                  style={{ minHeight: '48px', maxHeight: '200px' }}
                />
              </div>
              <Button
                onClick={handleSendMessage}
                disabled={!userInput.trim() || !selectedModel || isGenerating}
                className="bg-blue-500 hover:bg-blue-600 text-white p-3 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
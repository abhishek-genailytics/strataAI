import React, { useState } from "react";
import { Play, Plus, Code, Save } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
}

export const Playground: React.FC = () => {
  const [activeTab, setActiveTab] = useState("chat");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "system",
      content: "You are a helpful assistant.",
      timestamp: new Date(),
    },
  ]);
  const [userInput, setUserInput] = useState("");
  const [systemPrompt, setSystemPrompt] = useState(
    "You are a helpful assistant."
  );
  const [showAdvancedFields, setShowAdvancedFields] = useState(false);
  const [inputMode, setInputMode] = useState<
    "user" | "web-search" | "code-execution"
  >("user");

  const handleSendMessage = () => {
    if (!userInput.trim()) return;

    const newUserMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: userInput,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newUserMessage]);
    setUserInput("");

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "This is a simulated response from the AI model. In a real implementation, this would be the actual response from the selected model.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiResponse]);
    }, 1000);
  };

  const promptExamples = [
    {
      title: "Data Extraction with JSON Outputs",
      description:
        "Turn unstructured text into bespoke JSON tables with auto-generated keys",
    },
    {
      title: "JSON creation",
      description:
        "This prompt creates synthetic data for a product in a JSON format",
    },
    {
      title: "Non-English Content Generation",
      description:
        "Generate product announcement tweets in 10 most commonly spoken languages",
    },
    {
      title: "Removing PII",
      description: "Automatically detect and remove PII from text documents",
    },
  ];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <button className="text-gray-500 hover:text-gray-700">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
              />
            </svg>
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Playground</h1>
        </div>

        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-600">Your Prompt</span>
          <button className="text-sm text-gray-600 hover:text-gray-900 px-3 py-1 rounded hover:bg-gray-100">
            Recent
          </button>
          <button className="text-sm text-gray-600 hover:text-gray-900 px-3 py-1 rounded hover:bg-gray-100 flex items-center space-x-1">
            <Code className="w-4 h-4" />
            <span>Code</span>
          </button>
          <button className="text-sm text-gray-600 hover:text-gray-900 px-3 py-1 rounded hover:bg-gray-100">
            Clear
          </button>
          <button className="text-sm text-gray-600 hover:text-gray-900 px-3 py-1 rounded hover:bg-gray-100">
            Reset Playground
          </button>
          <button className="bg-gray-800 text-white px-4 py-2 rounded-lg hover:bg-gray-700 flex items-center space-x-2">
            <Save className="w-4 h-4" />
            <span>Save Prompt</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Sidebar - Configuration */}
        <div className="lg:col-span-1 space-y-6">
          {/* Model Configuration */}
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-900">
                Model Configuration
              </h3>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-500">⚡</span>
                <span className="text-xs text-gray-500">⚙️</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-700">
                  openai/chatgpt-4o-latest
                </span>
                <span className="text-xs text-gray-500">💎</span>
              </div>
              <div className="text-xs text-gray-500 space-y-1">
                <div>
                  temp: 0.7 | max tokens: 2500 | streaming mode: true | store
                  logs: true
                </div>
              </div>
            </div>
          </div>

          {/* Input Variables */}
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-900">
                Input Variables (0)
              </h3>
              <button className="text-gray-400 hover:text-gray-600">
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-gray-500">
              No input variables configured
            </p>
          </div>

          {/* MCP Servers */}
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-900">
                MCP Servers (0)
              </h3>
              <button className="text-gray-400 hover:text-gray-600">
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-gray-500">No MCP servers configured</p>
          </div>

          {/* Input Guardrails */}
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-900">
                Input Guardrails (0)
              </h3>
              <button className="text-gray-400 hover:text-gray-600">
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-gray-500">
              No input guardrails configured
            </p>
          </div>

          {/* Output Guardrails */}
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-900">
                Output Guardrails (0)
              </h3>
              <button className="text-gray-400 hover:text-gray-600">
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-gray-500">
              No output guardrails configured
            </p>
          </div>

          {/* Structured Output */}
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-900">
                Structured Output
              </h3>
              <button className="text-gray-400 hover:text-gray-600">
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-gray-500">
              No structured output configured
            </p>
          </div>
        </div>

        {/* Main Content - Chat Interface */}
        <div className="lg:col-span-2 space-y-6">
          {/* Tabs */}
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="flex border-b border-gray-200">
              {["Chat", "Embedding", "Rerank", "Image"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab.toLowerCase())}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.toLowerCase()
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            <div className="p-6">
              {/* System Prompt */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  SYSTEM PROMPT
                </label>
                <textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={3}
                  placeholder="Enter system prompt..."
                />
              </div>

              {/* Response Area */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Response will appear here
                </label>
                <div className="w-full h-64 border border-gray-300 rounded-lg bg-gray-50 flex items-center justify-center">
                  <p className="text-gray-500">
                    AI response will appear here after you send a message
                  </p>
                </div>
              </div>

              {/* Prompt Examples */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-700 mb-3">
                  Prompt Examples
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {promptExamples.map((example, index) => (
                    <div
                      key={index}
                      className="p-3 border border-gray-200 rounded-lg hover:border-gray-300 cursor-pointer"
                    >
                      <h5 className="font-medium text-gray-900 text-sm mb-1">
                        {example.title}
                      </h5>
                      <p className="text-xs text-gray-600">
                        {example.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* User Input */}
              <div className="space-y-4">
                <div className="flex space-x-2">
                  {[
                    { key: "user", label: "User", icon: "👤" },
                    { key: "web-search", label: "Web Search", icon: "🌐" },
                    {
                      key: "code-execution",
                      label: "Code Execution",
                      icon: "⚡",
                    },
                  ].map((mode) => (
                    <button
                      key={mode.key}
                      onClick={() => setInputMode(mode.key as any)}
                      className={`px-3 py-2 text-sm rounded-lg border transition-colors ${
                        inputMode === mode.key
                          ? "border-blue-500 bg-blue-50 text-blue-700"
                          : "border-gray-300 text-gray-600 hover:border-gray-400"
                      }`}
                    >
                      <span className="mr-2">{mode.icon}</span>
                      {mode.label}
                    </button>
                  ))}
                </div>

                <div className="flex space-x-3">
                  <input
                    type="text"
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                    placeholder="Enter user message..."
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                    Add message
                  </button>
                  <button
                    onClick={handleSendMessage}
                    className="px-6 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 flex items-center space-x-2"
                  >
                    <Play className="w-4 h-4" />
                    <span>Run</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

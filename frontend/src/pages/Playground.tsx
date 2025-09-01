import React, { useState } from "react";
import { 
  Play, 
  Plus, 
  Code, 
  Save, 
  Settings, 
  Zap, 
  MessageSquare,
  Globe,
  Terminal,
  RotateCcw,
  Copy,
  Download
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";

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
  const [systemPrompt, setSystemPrompt] = useState("You are a helpful assistant.");
  const [showAdvancedFields, setShowAdvancedFields] = useState(false);
  const [inputMode, setInputMode] = useState<"user" | "web-search" | "code-execution">("user");
  const [isGenerating, setIsGenerating] = useState(false);
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2500);
  const [streamingMode, setStreamingMode] = useState(true);
  const [storeLogs, setStoreLogs] = useState(true);

  const handleSendMessage = () => {
    if (!userInput.trim()) return;

    setIsGenerating(true);
    const newUserMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: userInput,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newUserMessage]);
    setUserInput("");

    // Simulate AI response with streaming effect
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "This is a simulated response from the AI model. In a real implementation, this would be the actual response from the selected model with proper streaming support.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiResponse]);
      setIsGenerating(false);
    }, 2000);
  };

  const promptExamples = [
    {
      title: "Data Extraction with JSON Outputs",
      description: "Turn unstructured text into bespoke JSON tables with auto-generated keys",
      icon: "📊",
    },
    {
      title: "JSON creation", 
      description: "This prompt creates synthetic data for a product in a JSON format",
      icon: "🔧",
    },
    {
      title: "Non-English Content Generation",
      description: "Generate product announcement tweets in 10 most commonly spoken languages",
      icon: "🌍",
    },
    {
      title: "Removing PII",
      description: "Automatically detect and remove PII from text documents",
      icon: "🔒",
    },
  ];

  const inputModes = [
    { key: "user", label: "User", icon: MessageSquare, color: "blue" },
    { key: "web-search", label: "Web Search", icon: Globe, color: "green" },
    { key: "code-execution", label: "Code Execution", icon: Terminal, color: "purple" },
  ];

  return (
    <>
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Playground</h1>

          <div className="flex items-center space-x-3">
            <span className="text-sm text-slate-600 px-3 py-1 bg-white/60 rounded-full border border-slate-200">
              Your Prompt
            </span>
            <Button variant="ghost" size="sm" className="text-slate-600 hover:bg-white/60">
              Recent
            </Button>
            <Button variant="ghost" size="sm" className="text-slate-600 hover:bg-white/60">
              <Code className="w-4 h-4 mr-1" />
              Code
            </Button>
            <Button variant="ghost" size="sm" className="text-slate-600 hover:bg-white/60">
              <RotateCcw className="w-4 h-4 mr-1" />
              Clear
            </Button>
            <Button variant="outline" size="sm" className="border-slate-300 text-slate-700 hover:border-slate-400 bg-white/60">
              Reset Playground
            </Button>
            <Button className="bg-gradient-to-r from-slate-800 to-slate-900 hover:from-slate-700 hover:to-slate-800 text-white shadow-lg border-0">
              <Save className="w-4 h-4 mr-2" />
              Save Prompt
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Left Sidebar - Configuration */}
          <div className="lg:col-span-1 space-y-6">
            {/* Model Configuration */}
            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-slate-900">Model Configuration</h3>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-slate-500">⚡</span>
                    <span className="text-xs text-slate-500">⚙️</span>
                  </div>
                </div>
                
                <div className="p-3 bg-gradient-to-r from-slate-50 to-blue-50 rounded-lg border border-slate-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-slate-900 text-sm">openai/chatgpt-4o-latest</span>
                    <span className="text-lg">💎</span>
                  </div>
                  <div className="text-xs text-slate-600 space-y-1">
                    <div className="flex flex-wrap gap-2">
                      <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs">temp: {temperature}</span>
                      <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded text-xs">max tokens: {maxTokens}</span>
                    </div>
                    <div className="flex flex-wrap gap-2 mt-2">
                      <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded text-xs">
                        streaming: {streamingMode ? 'true' : 'false'}
                      </span>
                      <span className="bg-orange-100 text-orange-700 px-2 py-0.5 rounded text-xs">
                        store logs: {storeLogs ? 'true' : 'false'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            {/* Configuration Sections */}
            {[
              { title: "Input Variables", count: 0, icon: "📝" },
              { title: "MCP Servers", count: 0, icon: "🔧" },
              { title: "Input Guardrails", count: 0, icon: "🛡️" },
              { title: "Output Guardrails", count: 0, icon: "🔒" },
              { title: "Structured Output", count: 0, icon: "📋" },
            ].map((section) => (
              <Card key={section.title} className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center">
                    <span className="mr-2">{section.icon}</span>
                    {section.title} ({section.count})
                  </h3>
                  <Button variant="ghost" size="sm" className="text-slate-400 hover:text-slate-600">
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  No {section.title.toLowerCase()} configured
                </p>
              </Card>
            ))}
          </div>

          {/* Main Content - Chat Interface */}
          <div className="lg:col-span-3">
            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
              {/* Tabs */}
              <div className="flex border-b border-slate-200 -mx-6 -mt-6 px-6 pt-6">
                {[
                  { id: "chat", label: "Chat", icon: MessageSquare },
                  { id: "embedding", label: "Embedding", icon: Zap },
                  { id: "rerank", label: "Rerank", icon: Settings },
                  { id: "image", label: "Image", icon: Code },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center px-6 py-4 text-sm font-medium border-b-2 transition-all duration-200 ${
                      activeTab === tab.id
                        ? "border-blue-500 text-blue-600 bg-blue-50/50"
                        : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
                    }`}
                  >
                    <tab.icon className="w-4 h-4 mr-2" />
                    {tab.label}
                  </button>
                ))}
              </div>

              <div className="mt-6 space-y-6">
                {/* System Prompt */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2 uppercase tracking-wide">
                    System Prompt
                  </label>
                  <textarea
                    value={systemPrompt}
                    onChange={(e) => setSystemPrompt(e.target.value)}
                    className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none bg-white shadow-sm transition-shadow"
                    rows={3}
                    placeholder="Enter system prompt..."
                  />
                </div>

                {/* Response Area */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    Response
                  </label>
                  <div className="w-full h-64 border border-slate-300 rounded-xl bg-gradient-to-br from-slate-50 to-white flex items-center justify-center shadow-inner">
                    {isGenerating ? (
                      <div className="text-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                        <p className="text-slate-600">AI is generating response...</p>
                      </div>
                    ) : (
                      <div className="text-center">
                        <MessageSquare className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                        <p className="text-slate-500">Response will appear here after you send a message</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Prompt Examples */}
                <div>
                  <h4 className="text-sm font-semibold text-slate-700 mb-4">Prompt Examples</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {promptExamples.map((example, index) => (
                      <Card
                        key={index}
                        className="cursor-pointer hover:shadow-lg transition-all duration-200 border-slate-200 hover:border-blue-300 group bg-white/60"
                        onClick={() => setUserInput(example.title)}
                      >
                        <div className="flex items-start space-x-3">
                          <div className="text-2xl group-hover:scale-110 transition-transform duration-200">
                            {example.icon}
                          </div>
                          <div className="flex-1">
                            <h5 className="font-semibold text-slate-900 text-sm mb-1 group-hover:text-blue-600 transition-colors">
                              {example.title}
                            </h5>
                            <p className="text-xs text-slate-600 leading-relaxed">
                              {example.description}
                            </p>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>

                {/* User Input Section */}
                <div className="space-y-4">
                  {/* Input Mode Selector */}
                  <div className="flex space-x-2">
                    {inputModes.map((mode) => (
                      <button
                        key={mode.key}
                        onClick={() => setInputMode(mode.key as any)}
                        className={`flex items-center px-4 py-2 text-sm rounded-xl border transition-all duration-200 ${
                          inputMode === mode.key
                            ? `border-${mode.color}-400 bg-${mode.color}-50 text-${mode.color}-700 shadow-sm`
                            : "border-slate-300 text-slate-600 hover:border-slate-400 hover:bg-white/60"
                        }`}
                      >
                        <mode.icon className="w-4 h-4 mr-2" />
                        {mode.label}
                      </button>
                    ))}
                  </div>

                  {/* Input Field */}
                  <div className="flex space-x-3">
                    <div className="flex-1">
                      <textarea
                        value={userInput}
                        onChange={(e) => setUserInput(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            handleSendMessage();
                          }
                        }}
                        placeholder="Enter user message..."
                        className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none bg-white shadow-sm transition-shadow"
                        rows={3}
                      />
                    </div>
                    <div className="flex flex-col space-y-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="border-slate-300 text-slate-700 hover:border-slate-400 bg-white/60"
                      >
                        Add message
                      </Button>
                      <Button
                        onClick={handleSendMessage}
                        disabled={!userInput.trim() || isGenerating}
                        className="bg-gradient-to-r from-slate-800 to-slate-900 hover:from-slate-700 hover:to-slate-800 text-white shadow-lg border-0 disabled:opacity-50"
                      >
                        <Play className="w-4 h-4 mr-2" />
                        {isGenerating ? "Running..." : "Run"}
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-slate-200">
                  <div className="flex items-center space-x-4 text-xs text-slate-500">
                    <span>Model: openai/chatgpt-4o-latest</span>
                    <span>•</span>
                    <span>Tokens: ~{Math.ceil(userInput.length / 4)}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button variant="ghost" size="sm" className="text-slate-500">
                      <Copy className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm" className="text-slate-500">
                      <Download className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
    </>
  );
};
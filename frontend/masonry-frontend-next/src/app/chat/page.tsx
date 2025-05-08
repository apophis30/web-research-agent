"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, ChevronLeft, ChevronRight, Search } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { makeApiRequest } from "@/utils/api";
import Link from "next/link";
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'


interface Message {
  id: string;
  content: string;
  sender: "user" | "bot";
  timestamp: Date;
  status?: "sending" | "sent" | "error";
}

interface ApiConfig {
  apiUrl: string;
  userId: string;
}

interface SuggestedPrompt {
  title: string;
  content: string;
}

const UserIcon = () => {
  return (
    <svg
      data-testid="geist-icon"
      height="16"
      strokeLinejoin="round"
      viewBox="0 0 16 16"
      width="16"
      style={{ color: 'currentcolor' }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M7.75 0C5.95507 0 4.5 1.45507 4.5 3.25V3.75C4.5 5.54493 5.95507 7 7.75 7H8.25C10.0449 7 11.5 5.54493 11.5 3.75V3.25C11.5 1.45507 10.0449 0 8.25 0H7.75ZM6 3.25C6 2.2835 6.7835 1.5 7.75 1.5H8.25C9.2165 1.5 10 2.2835 10 3.25V3.75C10 4.7165 9.2165 5.5 8.25 5.5H7.75C6.7835 5.5 6 4.7165 6 3.75V3.25ZM2.5 14.5V13.1709C3.31958 11.5377 4.99308 10.5 6.82945 10.5H9.17055C11.0069 10.5 12.6804 11.5377 13.5 13.1709V14.5H2.5ZM6.82945 9C4.35483 9 2.10604 10.4388 1.06903 12.6857L1 12.8353V13V15.25V16H1.75H14.25H15V15.25V13V12.8353L14.931 12.6857C13.894 10.4388 11.6452 9 9.17055 9H6.82945Z"
        fill="currentColor"
      />
    </svg>
  );
};

export default function ChatPage() {
  const [activeTab, setActiveTab] = useState("chat");
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [apiConfig, setApiConfig] = useState<ApiConfig>({
    apiUrl: "http://localhost:8000",
    userId: "nextjs_user"
  });

  const [sessionId, setSessionId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "greeting",
      content: "Hello there!\nHow can I help you today?",
      sender: "bot",
      timestamp: new Date(),
      status: "sent"
    },
  ]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedPrompts: SuggestedPrompt[] = [
    {
      title: "What are the advantages",
      content: "of using Next.js?",
    },
    {
      title: "Write code to",
      content: "demonstrate dijkstra's algorithm",
    },
    {
      title: "Help me write an essay",
      content: "about silicon valley",
    },
    {
      title: "What is the weather",
      content: "in San Francisco?",
    },
  ];

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSendMessage = async () => {
    if (input.trim() === "" || !apiConfig.apiUrl) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      content: input,
      sender: "user",
      timestamp: new Date(),
      status: "sending"
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      // Update message status to sent
      setMessages((prev) => 
        prev.map(msg => 
          msg.id === userMessage.id 
            ? { ...msg, status: "sent" }
            : msg
        )
      );

      // Make API request to chat endpoint
      const response = await makeApiRequest('chat', {
        message: userMessage.content,
        user_id: apiConfig.userId,
        session_id: sessionId
      }, apiConfig.apiUrl);

      // Create bot message from response
      const botMessage: Message = {
        id: `bot-${Date.now()}`,
        content: response.response,
        sender: "bot",
        timestamp: new Date(),
        status: "sent"
      };

      // Update session ID if it's a new session
      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
      }

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      // Handle error
      console.error("Error", error)
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        content: "I'm sorry, I encountered an error while processing your message. Please try again.",
        sender: "bot",
        timestamp: new Date(),
        status: "error"
      };
      setMessages((prev) => [...prev, errorMessage]);

      // Update user message status to error
      setMessages((prev) => 
        prev.map(msg => 
          msg.id === userMessage.id 
            ? { ...msg, status: "error" }
            : msg
        )
      );
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestedPrompt = (prompt: SuggestedPrompt) => {
    setInput(`${prompt.title} ${prompt.content}`);
  };

  const handleApiUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setApiConfig({
      ...apiConfig,
      apiUrl: e.target.value
    });
  };

  const handleUserIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setApiConfig({
      ...apiConfig,
      userId: e.target.value
    });
  };

  return (
    <div className="flex h-screen bg-black text-white">
      {/* Sidebar */}
      <div className={`${isSidebarCollapsed ? 'w-16' : 'w-80'} border-r border-gray-800 flex flex-col transition-all duration-300`}>
        <div className="p-4 flex justify-between items-center border-b border-gray-800">
          {!isSidebarCollapsed && <h1 className="text-xl font-bold">Chatbot</h1>}
          <div className="flex items-center gap-2">
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-8 w-8"
              onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            >
              {isSidebarCollapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
            </Button>
          </div>
        </div>
        {!isSidebarCollapsed && (
          <div className="h-full py-6 px-4 flex flex-col">
            <h2 className="text-2xl font-bold mb-2">Web Research Assistant</h2>
            <Separator className="mb-6" />
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="api-url">API URL</Label>
                <Input 
                  id="api-url" 
                  value={apiConfig.apiUrl} 
                  onChange={handleApiUrlChange}
                  className="bg-gray-900 border-gray-700"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="user-id">User ID (optional)</Label>
                <Input 
                  id="user-id" 
                  value={apiConfig.userId} 
                  onChange={handleUserIdChange}
                  className="bg-gray-900 border-gray-700"
                />
              </div>
            </div>
            
            <Separator className="my-6" />
            
            <div className="mt-auto">
              <h3 className="font-semibold mb-2">About</h3>
              <p className="text-sm text-gray-400">
                This application lets you perform web research, search for information, 
                scrape webpages, and analyze content.
              </p>
            </div>
          </div>
        )}
        {isSidebarCollapsed && (
          <div className="flex flex-col items-center py-4">
            <div className="h-8 w-8 flex items-center justify-center text-gray-400 hover:text-white transition-colors">
              <UserIcon />
            </div>
          </div>
        )}
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        <div className="p-4 border-b border-gray-800 flex justify-between items-center">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="bg-transparent">
              <TabsTrigger value="chat" className="text-gray-400 data-[state=active]:text-black">
                Chat
              </TabsTrigger>
            </TabsList>
          </Tabs>
          <Link href="/">
            <Button variant="outline" className="bg-gray-800 hover:bg-gray-700 text-white border-gray-700 flex items-center gap-2">
              <Search className="h-4 w-4" />
              Search Agent
            </Button>
          </Link>
        </div>

        {/* Messages Area */}
        <ScrollArea className="flex-1 p-4 overflow-y-auto">
          <div className="space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.sender === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-3xl whitespace-pre-wrap ${
                    message.sender === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-800 text-white"
                  } rounded-lg p-4 relative group`}
                >
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                    </ReactMarkdown>
                  <div className="text-xs text-gray-400 mt-1">
                    {message.timestamp.toLocaleTimeString()}
                    {message.sender === "user" && (
                      <span className="ml-2">
                        {message.status === "sending" && "Sending..."}
                        {message.status === "sent" && "✓"}
                        {message.status === "error" && "✕"}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Suggested Prompts */}
        {messages.length === 1 && (
          <div className="p-4 grid grid-cols-2 gap-4">
            {suggestedPrompts.map((prompt, index) => (
              <Card
                key={index}
                className="bg-black/40 border-gray-800 cursor-pointer hover:bg-gray-900/80 transition-all duration-300 backdrop-blur-sm shadow-lg hover:shadow-xl hover:shadow-gray-900/20 group"
                onClick={() => handleSuggestedPrompt(prompt)}
              >
                <CardContent className="p-4">
                  <p className="font-medium text-slate-200 group-hover:text-slate-100 transition-colors">
                    {prompt.title}
                  </p>
                  <p className="text-slate-400 group-hover:text-slate-300 transition-colors">
                    {prompt.content}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 border-t border-gray-800">
          <div className="relative">
            <Input
              className="w-full bg-gray-900 border-gray-700 pl-4 pr-10 py-6 rounded-lg text-white focus:ring-2 focus:ring-blue-500 transition-all"
              placeholder="Send a message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center space-x-2">
              <Button
                onClick={handleSendMessage}
                variant="ghost"
                size="icon"
                className="text-gray-400 hover:text-black transition-colors"
                disabled={input.trim() === ""}
              >
                <Send className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
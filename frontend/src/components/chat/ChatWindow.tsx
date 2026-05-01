import { useState, useRef, useEffect } from "react";
import { useChatStore } from "../../store/chatStore";
import { useWebSocket } from "../../hooks/useWebSocket";
import type { ChatMessage, WSEvent } from "../../types";
import MessageBubble from "./MessageBubble";

export default function ChatWindow() {
  const [input, setInput] = useState("");
  const [customerId] = useState(() => `C-${Math.random().toString(36).slice(2, 8)}`);
  const [conversationId] = useState(() => crypto.randomUUID());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { messages, addMessage, isProcessing, setProcessing, setCurrentAgent, addEvent } =
    useChatStore();

  const { connected, sendMessage } = useWebSocket({
    conversationId,
    customerId,
    onEvent: handleEvent,
  });

  function handleEvent(event: WSEvent) {
    addEvent(event);

    switch (event.type) {
      case "agent_start":
        setCurrentAgent(event.agent as string);
        setProcessing(true);
        break;

      case "agent_response":
        addMessage({
          id: crypto.randomUUID(),
          role: "assistant",
          content: event.content as string,
          agent_name: event.agent as string,
          tools_called: [],
          created_at: new Date().toISOString(),
        });
        setProcessing(false);
        break;

      case "error":
        addMessage({
          id: crypto.randomUUID(),
          role: "system",
          content: event.message as string,
          tools_called: [],
          created_at: new Date().toISOString(),
        });
        setProcessing(false);
        break;

      case "human_approval_needed":
        addMessage({
          id: crypto.randomUUID(),
          role: "system",
          content: `[需要人工审批] ${event.reason}`,
          tools_called: [],
          created_at: new Date().toISOString(),
        });
        break;
    }
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || isProcessing) return;

    addMessage({
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      tools_called: [],
      created_at: new Date().toISOString(),
    });

    sendMessage(text);
    setInput("");
  };

  return (
    <div className="flex flex-col h-full">
      <div className="border-b px-6 py-3 bg-white flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">智能客服</h1>
          <p className="text-sm text-gray-500">
            {connected ? "已连接" : "连接中..."} · 客户: {customerId}
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-20">
            <p className="text-4xl mb-4">💬</p>
            <p>发送消息开始对话</p>
            <p className="text-sm mt-2">支持账单查询、技术支持、退款申请等</p>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isProcessing && (
          <div className="flex items-center gap-2 text-gray-400">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.1s]" />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]" />
            </div>
            <span className="text-sm">AI 正在思考...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t p-4 bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="输入消息..."
            className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isProcessing}
          />
          <button
            onClick={handleSend}
            disabled={isProcessing || !input.trim()}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  );
}

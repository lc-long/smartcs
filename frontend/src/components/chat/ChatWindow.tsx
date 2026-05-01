import { useState, useRef, useEffect } from "react";
import { useChatStore } from "../../store/chatStore";
import { useWebSocket } from "../../hooks/useWebSocket";
import { useAuth } from "../../contexts/AuthContext";
import type { WSEvent } from "../../types";
import MessageBubble from "./MessageBubble";

const QUICK_QUESTIONS = [
  { label: "查订单", question: "帮我查一下我的订单" },
  { label: "查账单", question: "帮我查一下我的账单" },
  { label: "退款", question: "我想申请退款" },
  { label: "产品问题", question: "我的设备出问题了" },
  { label: "退款政策", question: "你们的退款政策是什么？" },
  { label: "客服电话", question: "你们的客服电话是多少？" },
];

const AGENT_LABELS: Record<string, { name: string; color: string; icon: string }> = {
  billing: { name: "账单客服", color: "bg-green-100 text-green-800", icon: "💰" },
  technical: { name: "技术支持", color: "bg-blue-100 text-blue-800", icon: "🔧" },
  refund: { name: "退款客服", color: "bg-orange-100 text-orange-800", icon: "💸" },
  general: { name: "通用客服", color: "bg-purple-100 text-purple-800", icon: "💬" },
  escalation: { name: "人工客服", color: "bg-red-100 text-red-800", icon: "👤" },
  supervisor: { name: "智能路由", color: "bg-gray-100 text-gray-800", icon: "🤖" },
};

export default function ChatWindow() {
  const { user } = useAuth();
  const [input, setInput] = useState("");
  const customerId = user?.customer_id || `guest-${user?.id?.slice(0, 8) || "unknown"}`;
  const [conversationId] = useState(() => crypto.randomUUID());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { messages, addMessage, isProcessing, setProcessing, currentAgent, setCurrentAgent, addEvent } =
    useChatStore();

  const { connected, sendMessage } = useWebSocket({
    conversationId,
    customerId,
    onEvent: handleEvent,
  });

  function handleEvent(event: WSEvent) {
    addEvent(event);

    switch (event.type) {
      case "planning":
        if (event.status === "analyzing") {
          setCurrentAgent("supervisor");
          setProcessing(true);
        }
        break;

      case "complex_task_start":
        // 复杂任务开始，显示正在协调多个Agent
        setCurrentAgent("supervisor");
        setProcessing(true);
        break;

      case "parallel_start":
        // 并行执行开始
        setCurrentAgent("supervisor");
        break;

      case "subtask_start":
        // 子任务开始，更新当前Agent
        setCurrentAgent(event.agent as string);
        break;

      case "subtask_complete":
        // 子任务完成，但可能还有其他子任务
        break;

      case "agent_start":
        setCurrentAgent(event.agent as string);
        setProcessing(true);
        break;

      case "agent_complete":
        // Agent 完成，但可能还有其他 Agent 在执行
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
        setCurrentAgent(null);
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
        setCurrentAgent(null);
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

  const handleSend = (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText || isProcessing) return;

    addMessage({
      id: crypto.randomUUID(),
      role: "user",
      content: messageText,
      tools_called: [],
      created_at: new Date().toISOString(),
    });

    sendMessage(messageText);
    setInput("");
  };

  const agentInfo = currentAgent ? AGENT_LABELS[currentAgent] : null;

  return (
    <div className="flex flex-col h-full">
      {/* 头部 */}
      <div className="border-b px-6 py-3 bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold">智能客服</h1>
            <p className="text-sm text-gray-500">
              {connected ? (
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  已连接
                </span>
              ) : (
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></span>
                  连接中...
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isProcessing && agentInfo && (
              <span className={`px-3 py-1 rounded-full text-sm flex items-center gap-1 ${agentInfo.color}`}>
                <span>{agentInfo.icon}</span>
                <span>{agentInfo.name} 处理中...</span>
              </span>
            )}
            <span className="text-xs text-gray-400">ID: {customerId}</span>
          </div>
        </div>
      </div>

      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-20">
            <p className="text-5xl mb-4">🤖</p>
            <p className="text-lg font-medium">欢迎使用智能客服系统</p>
            <p className="text-sm mt-2 mb-8">请选择下方快捷问题或直接输入您的问题</p>
            
            {/* 快速问题模板 */}
            <div className="flex flex-wrap justify-center gap-2 max-w-md mx-auto">
              {QUICK_QUESTIONS.map((q) => (
                <button
                  key={q.label}
                  onClick={() => handleSend(q.question)}
                  className="px-4 py-2 bg-white border rounded-full text-sm text-gray-600 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-300 transition-colors"
                >
                  {q.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isProcessing && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-sm">
              {agentInfo?.icon || "🤖"}
            </div>
            <div className="bg-gray-100 rounded-2xl rounded-tl-md px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.1s]" />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]" />
                </div>
                <span className="text-sm text-gray-500">
                  {currentAgent === "supervisor"
                    ? "正在协调多个Agent处理..."
                    : agentInfo
                    ? `${agentInfo.name} 正在处理...`
                    : "AI 正在思考..."}
                </span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
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
            onClick={() => handleSend()}
            disabled={isProcessing || !input.trim()}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            发送
          </button>
        </div>
        <div className="flex gap-2 mt-2">
          {QUICK_QUESTIONS.slice(0, 4).map((q) => (
            <button
              key={q.label}
              onClick={() => handleSend(q.question)}
              disabled={isProcessing}
              className="text-xs text-gray-500 hover:text-blue-500 disabled:opacity-50"
            >
              {q.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

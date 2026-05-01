import type { ChatMessage } from "../../types";

interface Props {
  message: ChatMessage;
}

const agentLabels: Record<string, string> = {
  router: "路由",
  billing: "账单",
  technical: "技术",
  refund: "退款",
  general: "通用",
  escalation: "人工",
};

const agentColors: Record<string, string> = {
  router: "bg-purple-100 text-purple-700",
  billing: "bg-green-100 text-green-700",
  technical: "bg-blue-100 text-blue-700",
  refund: "bg-orange-100 text-orange-700",
  general: "bg-gray-100 text-gray-700",
  escalation: "bg-red-100 text-red-700",
};

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm px-4 py-2 rounded-full">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-3 ${
          isUser ? "bg-blue-500 text-white" : "bg-white border shadow-sm"
        }`}
      >
        {!isUser && message.agent_name && (
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`text-xs px-2 py-0.5 rounded-full ${
                agentColors[message.agent_name] || "bg-gray-100"
              }`}
            >
              {agentLabels[message.agent_name] || message.agent_name}Agent
            </span>
          </div>
        )}

        <p className="text-sm whitespace-pre-wrap">{message.content}</p>

        {message.tools_called.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {message.tools_called.map((tool) => (
              <span
                key={tool}
                className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
              >
                🔧 {tool}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

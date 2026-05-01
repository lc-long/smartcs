import type { ChatMessage } from "../../types";

interface Props {
  message: ChatMessage;
}

const agentLabels: Record<string, string> = {
  router: "智能路由",
  billing: "账单客服",
  technical: "技术支持",
  refund: "退款客服",
  general: "通用客服",
  escalation: "人工客服",
  supervisor: "智能路由",
};

const agentColors: Record<string, string> = {
  router: "bg-purple-100 text-purple-700",
  billing: "bg-green-100 text-green-700",
  technical: "bg-blue-100 text-blue-700",
  refund: "bg-orange-100 text-orange-700",
  general: "bg-gray-100 text-gray-700",
  escalation: "bg-red-100 text-red-700",
  supervisor: "bg-gray-100 text-gray-700",
};

const agentIcons: Record<string, string> = {
  router: "🔀",
  billing: "💰",
  technical: "🔧",
  refund: "💸",
  general: "💬",
  escalation: "👤",
  supervisor: "🤖",
};

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center my-2">
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm px-4 py-2 rounded-full flex items-center gap-2">
          <span>⚠️</span>
          <span>{message.content}</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-sm mr-2 flex-shrink-0">
          {agentIcons[message.agent_name || "general"] || "🤖"}
        </div>
      )}
      
      <div
        className={`max-w-[70%] ${
          isUser
            ? "bg-blue-500 text-white rounded-2xl rounded-tr-md"
            : "bg-white border shadow-sm rounded-2xl rounded-tl-md"
        } px-4 py-3`}
      >
        {!isUser && message.agent_name && (
          <div className="flex items-center gap-2 mb-2">
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                agentColors[message.agent_name] || "bg-gray-100"
              }`}
            >
              {agentLabels[message.agent_name] || message.agent_name}
            </span>
          </div>
        )}

        <div className="text-sm whitespace-pre-wrap leading-relaxed">
          {formatContent(message.content)}
        </div>

        {message.tools_called.length > 0 && (
          <div className="mt-3 pt-2 border-t border-gray-100 flex flex-wrap gap-1">
            <span className="text-xs text-gray-400">调用工具:</span>
            {message.tools_called.map((tool) => (
              <span
                key={tool}
                className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded"
              >
                {tool}
              </span>
            ))}
          </div>
        )}

        <div className={`text-xs mt-2 ${isUser ? "text-blue-200" : "text-gray-400"}`}>
          {new Date(message.created_at).toLocaleTimeString("zh-CN", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-sm ml-2 flex-shrink-0">
          👤
        </div>
      )}
    </div>
  );
}

function formatContent(content: string): React.ReactNode {
  // 处理 Markdown 表格
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let tableRows: string[] = [];
  let inTable = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    if (line.startsWith("|") && line.endsWith("|")) {
      if (!inTable) {
        inTable = true;
        tableRows = [];
      }
      tableRows.push(line);
    } else {
      if (inTable) {
        elements.push(renderTable(tableRows, elements.length));
        tableRows = [];
        inTable = false;
      }
      
      if (line.startsWith("**") && line.endsWith("**")) {
        elements.push(
          <p key={i} className="font-semibold my-1">
            {line.slice(2, -2)}
          </p>
        );
      } else if (line.startsWith("- ") || line.startsWith("* ")) {
        elements.push(
          <li key={i} className="ml-4 my-0.5">
            {line.slice(2)}
          </li>
        );
      } else if (/^\d+\./.test(line)) {
        elements.push(
          <li key={i} className="ml-4 my-0.5 list-decimal">
            {line.replace(/^\d+\.\s*/, "")}
          </li>
        );
      } else if (line) {
        elements.push(<p key={i} className="my-1">{line}</p>);
      }
    }
  }

  if (inTable && tableRows.length > 0) {
    elements.push(renderTable(tableRows, elements.length));
  }

  return <>{elements}</>;
}

function renderTable(rows: string[], key: number): React.ReactNode {
  if (rows.length < 2) return null;

  const headerCells = rows[0]
    .split("|")
    .slice(1, -1)  // Remove first and last empty elements from split
    .map((cell) => cell.trim());

  const bodyRows = rows.slice(2).map((row) =>
    row
      .split("|")
      .slice(1, -1)  // Remove first and last empty elements from split
      .map((cell) => cell.trim())
  );

  return (
    <div key={key} className="overflow-x-auto my-2">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-50">
            {headerCells.map((cell, i) => (
              <th key={i} className="px-3 py-2 text-left border font-medium">
                {cell || "\u00A0"}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {bodyRows.map((row, i) => (
            <tr key={i} className="hover:bg-gray-50">
              {row.map((cell, j) => (
                <td key={j} className="px-3 py-2 border">
                  {cell || "\u00A0"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export type MessageRole = "user" | "assistant" | "system" | "human_agent";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  agent_name?: string;
  tools_called: string[];
  created_at: string;
}

export interface ChatResponse {
  conversation_id: string;
  message: ChatMessage;
  metadata: {
    intent: string;
    confidence: number;
    routing_reasoning: string;
    model_used: string;
    token_usage: Record<string, number>;
    latency_ms: number;
  };
}

export interface ApprovalItem {
  id: string;
  conversation_id: string;
  approval_type: string;
  customer_id: string;
  agent_name: string;
  action_description: string;
  risk_level: string;
  status: string;
  created_at: string;
}

export type WSMessageType =
  | "user_message"
  | "agent_start"
  | "agent_response"
  | "agent_switch"
  | "agent_complete"
  | "tool_call"
  | "tool_result"
  | "human_approval_needed"
  | "approval_result"
  | "human_takeover"
  | "human_release"
  | "error"
  | "done"
  | "planning"
  | "sentiment"
  | "complex_task_start"
  | "parallel_start"
  | "subtask_start"
  | "subtask_complete";

export interface WSEvent {
  type: WSMessageType;
  [key: string]: unknown;
}

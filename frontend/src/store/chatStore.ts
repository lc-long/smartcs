import { create } from "zustand";
import type { ChatMessage, WSEvent } from "../types";

interface ChatState {
  messages: ChatMessage[];
  currentAgent: string | null;
  isProcessing: boolean;
  events: WSEvent[];

  addMessage: (msg: ChatMessage) => void;
  setCurrentAgent: (agent: string | null) => void;
  setProcessing: (v: boolean) => void;
  addEvent: (event: WSEvent) => void;
  clear: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  currentAgent: null,
  isProcessing: false,
  events: [],

  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setCurrentAgent: (agent) => set({ currentAgent: agent }),
  setProcessing: (v) => set({ isProcessing: v }),
  addEvent: (event) => set((state) => ({ events: [...state.events, event] })),
  clear: () => set({ messages: [], events: [], currentAgent: null, isProcessing: false }),
}));

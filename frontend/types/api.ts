// Company types
export interface Company {
  id: string;
  name: string;
  description: string | null;
  embedding_model: string;
  embedding_type: string;
  llm_model: string;
  llm_provider: string;
  created_at: string;
}

// User types
export interface User {
  id: string;
  email: string;
  name: string;
  company_id: string | null;
  created_at: string;
}

// Chat types
export interface Chat {
  id: string;
  title: string | null;
  user_id: string;
  company_id: string | null;
  selected_document_ids: string[] | null;  // NEW
  created_at: string;
  updated_at: string;
}

// Document types
export interface DocumentInfo {
  document_id: string;
  filename: string;
  num_chunks: number;
  created_at: string;
  metadata: Record<string, any> | null;
}

export interface DocumentListResponse {
  documents: DocumentInfo[];
  total: number;
}

// Chat Message types
export interface ChatMessage {
  id: string;
  chat_id: string;
  chat_query: string;
  context_document: Record<string, any> | null;
  response: string | null;
  created_at: string;
  status?: string;  // NEW: "processing" | "done" | "error"
}

// Query Response types
export interface ChatQueryResponse {
  message_id: string;
  chat_id: string;
  query: string;
  response: string;
  context_documents: Record<string, any>[];
  created_at: string;
  llm_model: string;
  llm_provider: string;
}

// Document Upload types
export interface DocumentUploadResponse {
  status: string;
  document_id: string;
  filename: string;
  text_length: number;
  num_chunks: number;
  chunk_size: number;
  overlap: number;
  metadata: Record<string, any>;
  processing_info?: Record<string, any>;
}

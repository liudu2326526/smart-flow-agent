export interface DocumentInfo {
  id: number;
  filename: string;
  status: string;
  uploaded_at: string;
  size: number;
}

export interface DocumentListResponse {
  code: number;
  message: string;
  data: DocumentInfo[];
}

export interface DocumentUploadResponse {
  code: number;
  message: string;
  data: {
    id: number;
    filename: string;
    size: number;
    status: string;
    url?: string;
  };
}

export const getDocuments = async (status?: string): Promise<DocumentListResponse> => {
  const url = status ? `/api/v1/documents?status=${status}` : '/api/v1/documents';
  const res = await fetch(url);
  return res.json();
};

export const uploadDocument = async (file: File, sessionId?: string): Promise<DocumentUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  const res = await fetch('/api/v1/documents/upload', {
    method: 'POST',
    body: formData,
  });
  
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || '上传失败');
  }
  return data;
};

export const deleteDocument = async (docId: number): Promise<{ code: number; message: string }> => {
  const res = await fetch(`/api/v1/documents/${docId}`, {
    method: 'DELETE',
  });
  return res.json();
};

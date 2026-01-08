export interface DocumentInfo {
  id: string;
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
    id: string;
    filename: string;
    size: number;
    status: string;
    url?: string;
  };
}

export const getDocuments = async (user_id: string = 'admin', status?: string): Promise<DocumentListResponse> => {
  let url = `/api/v1/documents?user_id=${user_id}`;
  if (status) {
    url += `&status=${status}`;
  }
  const res = await fetch(url);
  return res.json();
};

export const uploadDocument = async (file: File, sessionId?: string, user_id: string = 'admin'): Promise<DocumentUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_id', user_id);
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

export const deleteDocument = async (docId: string, user_id: string = 'admin'): Promise<{ code: number; message: string }> => {
  const res = await fetch(`/api/v1/documents/${docId}?user_id=${user_id}`, {
    method: 'DELETE',
  });
  return res.json();
};

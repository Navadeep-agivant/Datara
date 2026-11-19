import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 45000,
});

export const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getProfile = async (sessionId) => {
  const response = await api.get(`/sessions/${sessionId}/profile`);
  return response.data;
};

export const runDetection = async (sessionId, params = {}) => {
  const response = await api.post(`/sessions/${sessionId}/detect`, params);
  return response.data;
};

export const getExplanations = async (sessionId) => {
  const response = await api.get(`/sessions/${sessionId}/explain`);
  return response.data;
};

export const getCleaningOperations = async (sessionId) => {
  const response = await api.get(`/sessions/${sessionId}/clean`);
  return response.data;
};

export const previewCleaningOperation = async (sessionId, operationId) => {
  const response = await api.get(`/sessions/${sessionId}/clean/preview`, {
    params: { operation_id: operationId }
  });
  return response.data;
};

export const approveCleaningOperations = async (sessionId, operationIds) => {
  const response = await api.post(`/sessions/${sessionId}/clean/approve`, {
    operation_ids: operationIds,
  });
  return response.data;
};

export const applyAllLowRisk = async (sessionId) => {
  const response = await api.post(`/sessions/${sessionId}/clean/apply-all-low-risk`);
  return response.data;
};

export const undoCleaningOperation = async (sessionId) => {
  const response = await api.post(`/sessions/${sessionId}/clean/undo`);
  return response.data;
};

export const getQualityScore = async (sessionId) => {
  const response = await api.get(`/sessions/${sessionId}/score`);
  return response.data;
};

export const getReportUrl = (sessionId) => {
  return `/api/sessions/${sessionId}/report`;
};

export const getExportCsvUrl = (sessionId) => {
  return `/api/sessions/${sessionId}/export/csv`;
};

export const adaptiveLearn = async (sessionId) => {
  const response = await api.post(`/sessions/${sessionId}/adaptive-learn`);
  return response.data;
};

export const editSandboxOperation = async (sessionId, operationId, edits) => {
  const response = await api.post(`/sessions/${sessionId}/clean/sandbox-edit`, {
    operation_id: operationId,
    edits: edits,
  });
  return response.data;
};

export const aiSuggestRemediation = async (sessionId, operationId, rowIndex = null, columnName = null) => {
  const response = await api.post(`/sessions/${sessionId}/clean/ai-suggest`, {
    operation_id: operationId,
    row_index: rowIndex,
    column_name: columnName,
  });
  return response.data;
};

export default api;

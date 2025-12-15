// frontend/src/api/market.ts
import http from "./http";

export type DraftInitReq = {
  category_id: number;
  device_model_id: number;
  years_used: number;
  original_price: number;
};

export type DraftInitResp = {
  draft_key: string;
  meta?: DraftInitReq & Record<string, any>;
};

export type AnalyzeResp = {
  main_image: string;
  grade_label: string;
  grade_score: number;
  defects: string[];
};

export type PublishReq = {
  // step1
  category_id: number;
  device_model_id: number;
  years_used: number;
  original_price: number | string;

  // step2
  grade_label: string;
  defects: string[];

  // step3
  title: string;
  description: string;
  selling_price: number | string;
};

export async function initDraft(payload: DraftInitReq): Promise<DraftInitResp> {
  // 注意：你后端现在是 /api/market/drafts/init/（带斜杠）
  const res = await http.post("/api/market/drafts/init/", payload);
  return res.data;
}

export async function uploadDraftImage(draftKey: string, file: File): Promise<any> {
  const form = new FormData();
  // 字段名必须叫 image（和你 curl 一致）
  form.append("image", file);

  const res = await http.post(`/api/market/drafts/${draftKey}/images/`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

// 批量上传（最多4张），按顺序逐张上传；第1张会成为主图
export async function uploadDraftImages(draftKey: string, files: File[]): Promise<any[]> {
  const list = Array.isArray(files) ? files.slice(0, 4) : [];
  const results: any[] = [];

  for (const f of list) {
    const r = await uploadDraftImage(draftKey, f);
    results.push(r);
  }

  return results;
}

export async function analyzeDraft(draftKey: string): Promise<AnalyzeResp> {
  const res = await http.post(`/api/market/drafts/${draftKey}/analyze/`);
  return res.data;
}

export type EstimateReq = {
  category_id: number;
  years_used: number;
  original_price: number | string;
  grade_label: string;
  defects: string[];
};

export async function estimateDraft(draftKey: string, payload: EstimateReq): Promise<any> {
  const res = await http.post(`/api/market/drafts/${draftKey}/estimate/`, payload);
  return res.data;
}

export async function publishDraft(draftKey: string, payload: PublishReq): Promise<any> {
  const res = await http.post(`/api/market/drafts/${draftKey}/publish/`, payload);
  return res.data;
}
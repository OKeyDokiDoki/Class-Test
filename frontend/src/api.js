import axios from "axios";
import { communityData, merchantData, residentData } from "./mockData";

const api = axios.create({ baseURL: "/api", timeout: 2500 });

async function withFallback(request, fallback) {
  try {
    const response = await request();
    return response.data?.data ?? response.data;
  } catch {
    return fallback;
  }
}

export const getResidentAssessment = () =>
  withFallback(() => api.get("/resident/assessment"), residentData);
export const getMerchantRecommendations = () =>
  withFallback(() => api.get("/merchant/recommendations"), merchantData);
export const getCommunityOverview = () =>
  withFallback(() => api.get("/community/overview"), communityData);

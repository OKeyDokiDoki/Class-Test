import { Building2, CircleUserRound, Store } from "@lucide/vue";

export const ROLE_IDS = Object.freeze({
  RESIDENT: "resident",
  MERCHANT: "merchant",
  COMMUNITY: "community"
});

export const USER_ROLES = Object.freeze([
  { id: ROLE_IDS.RESIDENT, name: "居民端", caption: "生活圈体检", icon: CircleUserRound },
  { id: ROLE_IDS.MERCHANT, name: "商户端", caption: "智能选址", icon: Store },
  { id: ROLE_IDS.COMMUNITY, name: "社区端", caption: "精准招商", icon: Building2 }
]);

export const STORAGE_KEYS = Object.freeze({
  ACTIVE_ROLE: "life-circle:active-role"
});

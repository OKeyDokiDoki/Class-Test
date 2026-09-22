const PHONE_PATTERN = /^1[3-9]\d{9}$/;

export function validateMerchantIntent(intent = {}) {
  const errors = {};
  if (!intent.merchantName?.trim()) errors.merchantName = "请填写商户名称";
  if (!intent.businessType?.trim()) errors.businessType = "请选择经营业态";
  if (!PHONE_PATTERN.test(intent.contact?.trim() ?? "")) errors.contact = "请填写正确的手机号";

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}

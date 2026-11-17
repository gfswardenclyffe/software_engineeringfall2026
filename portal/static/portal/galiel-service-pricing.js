/* Galiel service-size and fee-preview helpers.
   Visual preview only. No checkout, payment, model writes or rate fetching.
   Once approved, supply an audited per-service rate and a dated Banxico FIX/EUR
   snapshot from the SERVER, not an arbitrary browser-side spot rate. */
(function () {
  "use strict";
  const SQFT_PER_SQM = 10.7639104167097;
  function sqm(value, unit) {
    const number = Number(value);
    if (!Number.isFinite(number) || number < 0) return null;
    return unit === "ft2" ? number / SQFT_PER_SQM : number;
  }
  function calculateFee(sizeSqm, baseFee, extraPerSqm) {
    if (![sizeSqm, baseFee, extraPerSqm].every(Number.isFinite) || [sizeSqm, baseFee, extraPerSqm].some(n => n < 0)) return null;
    return Math.round((baseFee + Math.max(0, sizeSqm - 100) * extraPerSqm) * 100) / 100;
  }
  // Banxico FIX is MXN per USD. EUR/MXN must have its own dated approved reference.
  function approximatePayment(primaryAmount, currency, fx) {
    if (!Number.isFinite(primaryAmount) || primaryAmount < 0 || !fx || !fx.approved) return null;
    if (currency === "MXN" && fx.mxnPerUsd > 0) return {unit:"USD", amount: primaryAmount / fx.mxnPerUsd};
    if (currency === "MXN" && fx.mxnPerEur > 0) return {unit:"EUR", amount: primaryAmount / fx.mxnPerEur};
    return null;
  }
  // Helpers exported for later isolated, fee-sheet-backed tests. They do not
  // render a fee until reviewed inputs exist.
  window.GalielPricingPreview = Object.freeze({sqm, calculateFee, approximatePayment});
  const input = document.getElementById("business-size");
  if (!input) return;
  const lang = input.dataset.locale || document.documentElement.lang || "en";
  let unit = lang === "en" ? "ft2" : "m2";
  const buttons = [...document.querySelectorAll("[data-area-unit]")];
  function refresh() {
    for (const button of buttons) button.setAttribute("aria-pressed", String(button.dataset.areaUnit === unit));
    const converted = sqm(input.value, unit);
    input.dataset.sqm = converted === null || input.value.trim() === "" ? "" : converted.toFixed(2);
  }
  for (const button of buttons) button.addEventListener("click", () => {
    const next = button.dataset.areaUnit;
    if (next !== unit) {
      const oldSqm = input.value.trim() === "" ? null : sqm(input.value, unit);
      unit = next;
      if (oldSqm !== null) input.value = Number((next === "ft2" ? oldSqm * SQFT_PER_SQM : oldSqm).toFixed(2)).toString();
    }
    refresh();
  });
  input.addEventListener("input", refresh);
  refresh();
})();

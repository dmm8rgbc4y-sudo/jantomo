// ===========================================
// 📱 iPhone専用「ホーム画面に追加」案内バナー
// ===========================================

document.addEventListener("DOMContentLoaded", () => {
  const banner = document.getElementById("ios-a2hs-banner");
  const closeBtn = document.getElementById("ios-a2hs-close");
  if (!banner || !closeBtn) return;

  // -------------------------
  // ▼ iPhone / iPad / iPod 判定
  // -------------------------
  const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);

  // -------------------------
  // ▼ PWAで起動中か？
  //    ※standalone = ホーム画面追加済み
  // -------------------------
  const isInStandalone =
    window.navigator.standalone === true ||
    window.matchMedia("(display-mode: standalone)").matches;

  // -------------------------
  // ▼ 一度閉じたら二度と出さない
  // -------------------------
  if (localStorage.getItem("iosA2HS_shown")) return;

  // -------------------------
  // ▼ iOS かつ PWAではない状態のみ
  // -------------------------
  if (isIOS && !isInStandalone) {
    // weeklyページのみ表示
    if (window.location.pathname.includes("/weekly")) {
      banner.classList.remove("hidden");
    }
  }

  // -------------------------
  // ▼ 閉じるボタン
  // -------------------------
  closeBtn.addEventListener("click", () => {
    banner.classList.add("hidden");
    localStorage.setItem("iosA2HS_shown", "true");
  });
});

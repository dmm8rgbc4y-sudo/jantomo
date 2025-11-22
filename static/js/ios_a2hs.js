// ===========================================
// 📱 iPhone専用「ホーム画面に追加」案内バナー（改良版）
// ===========================================

document.addEventListener("DOMContentLoaded", () => {
  const banner = document.getElementById("ios-a2hs-banner");
  const closeBtn = document.getElementById("ios-a2hs-close");
  if (!banner || !closeBtn) return;

  // -------------------------
  // ▼ iPhone / iPad / iPod 判定
  // -------------------------
  const ua = navigator.userAgent.toLowerCase();
  const isIOS = /iphone|ipad|ipod/.test(ua);

  // -------------------------
  // ▼ LINE / Instagram / Facebookのインアプリブラウザ判定
  // -------------------------
  const isInAppBrowser =
    ua.includes("line") ||
    ua.includes("instagram") ||
    ua.includes("fbav") || ua.includes("fban");

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
  // ▼ iOS かつ PWAではない状態のみ検討
  // -------------------------
  if (isIOS && !isInStandalone) {

    // weeklyページのみ表示
    if (window.location.pathname.includes("/weekly")) {

      // ★ インアプリブラウザの場合は文言を差し替え
      if (isInAppBrowser) {
        banner.querySelector("p").innerHTML =
          `LINE等のアプリ内ブラウザでは<br>
          <b>ホーム画面に追加</b>できません。<br>
           <b>Safari または Chrome</b> で開いてご利用ください。`;
      }

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

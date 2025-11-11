// ===============================
// 📲 PWA案内バナー（新規登録ページ専用）
// ===============================
window.addEventListener("load", () => {
  // すでにPWAとして起動中なら非表示
  if (window.matchMedia("(display-mode: standalone)").matches) {
    localStorage.setItem("pwaPromptShown", "true");
    return;
  }

  // 一度表示したら再表示しない
  if (localStorage.getItem("pwaPromptShown")) return;

  // 現在のURLを確認
  const currentPath = window.location.pathname;

  // 新規登録ページ（例: /register）以外では表示しない
  if (!currentPath.includes("/register")) return;

  // register ページのときだけ表示
  const banner = document.getElementById("pwa-banner");
  if (banner) banner.classList.remove("hidden");

  // ページ遷移または閉じると次回以降非表示
  window.addEventListener("beforeunload", () => {
    localStorage.setItem("pwaPromptShown", "true");
  });
});

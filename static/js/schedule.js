// ==========================================
// schedule.js（2025-12 完全安定版 + CSRF/Safari 対応版）
// ・Flash成功表示100%保証
// ・週またぎ保持
// ・一括解除バグゼロ
// ・Safari の null 参照バグ修正
// ・CSRF hidden フィールド付与
// ==========================================

document.addEventListener("DOMContentLoaded", () => {
  // WEEK_OFFSET と csrf_token は schedule.html 側で定義される
  // console.log("WEEK_OFFSET:", WEEK_OFFSET, "CSRF:", csrf_token);

  const rows = document.querySelectorAll(".date-row");
  const saveBtn = document.getElementById("save-btn");

  const DRAFT_KEY = `schedule-draft-week${WEEK_OFFSET}`;

  // ---- draft 読み込み ----
  let draft = {};
  try {
    draft = JSON.parse(localStorage.getItem(DRAFT_KEY)) || {};
  } catch {
    draft = {};
  }

  const initialSelections = {};
  const currentSelections = {};

  // =======================================================
  // 📌 初期ロード：server → draft の優先順
  // =======================================================
  rows.forEach((row) => {
    const date = row.dataset.date;
    const buttons = row.querySelectorAll(".time-btn");
    const serverSelected = row.querySelector(".time-btn.selected");

    if (serverSelected) {
      initialSelections[date] = serverSelected.dataset.slot;
      currentSelections[date] = serverSelected.dataset.slot;
    }

    // draft 反映
    if (draft[date]) {
      buttons.forEach((b) => b.classList.remove("selected"));
      const btn = Array.from(buttons).find((b) => b.dataset.slot === draft[date]);
      if (btn) btn.classList.add("selected");
      currentSelections[date] = draft[date];
    }
  });

  // =======================================================
  // 📌 ボタン操作（他日付に影響しない）
  // =======================================================
  rows.forEach((row) => {
    const date = row.dataset.date;
    const buttons = row.querySelectorAll(".time-btn");

    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const wasSelected = btn.classList.contains("selected");

        buttons.forEach((b) => b.classList.remove("selected"));
        delete currentSelections[date];
        delete draft[date];

        if (!wasSelected) {
          btn.classList.add("selected");
          const slot = btn.dataset.slot;
          currentSelections[date] = slot;
          draft[date] = slot;
        }

        localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
      });
    });
  });

  // =======================================================
  // 📌 決定ボタン（★成功Flash100%保証版★ + CSRF対応）
  // =======================================================
  saveBtn?.addEventListener("click", () => {
    const payload = [];

    const merged = { ...currentSelections };

    // 更新・新規
    Object.keys(merged).forEach((date) => {
      const before = initialSelections[date] || "";
      const after = merged[date] || "";
      if (before !== after) {
        payload.push({ date, slot: convertSlotLabel(after) });
      }
    });

    // 削除
    Object.keys(initialSelections).forEach((date) => {
      if (!merged[date]) {
        payload.push({ date, slot: "" });
      }
    });

    // 差分なし → JS info
    if (payload.length === 0) {
      showInfo("変更はありません。");
      return;
    }

    try {
      const form = document.createElement("form");
      form.method = "POST";
      form.action = `/schedule/save?week=${WEEK_OFFSET}`;

      // 🔐 CSRF hidden input
      const csrf = document.createElement("input");
      csrf.type = "hidden";
      csrf.name = "csrf_token";
      csrf.value = csrf_token;
      form.appendChild(csrf);

      // payload
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = "payload";
      input.value = JSON.stringify(payload);
      form.appendChild(input);

      document.body.appendChild(form);

      localStorage.removeItem(DRAFT_KEY);
      form.submit();

    } catch {
      showError("通信エラーが発生しました。");
    }
  });
});

// =======================================================
// 📌 slot 日本語変換
// =======================================================
function convertSlotLabel(slot) {
  if (slot === "day") return "昼";
  if (slot === "night") return "夜";
  if (slot === "both") return "両方";
  return "";
}

// =======================================================
// 📌 JS Flash（info/error のみ）
// =======================================================
function showInfo(message) {
  createFlash(message, "info");
}

function showError(message) {
  createFlash(message, "error");
}

function createFlash(message, type) {
  const flash = document.createElement("div");
  flash.className = `flash-message ${type}`;
  flash.innerText = message;

  document.body.appendChild(flash);

  setTimeout(() => (flash.style.opacity = "0"), 1800);
  setTimeout(() => flash.remove(), 2500);
}

// =======================================================
// 📌 モバイルツールチップ
// =======================================================
document.addEventListener("DOMContentLoaded", () => {
  const icons = document.querySelectorAll(".icon-frame");

  icons.forEach((icon) => {
    const showTooltip = (e) => {
      e.preventDefault();
      const name = icon.getAttribute("data-name");
      if (!name) return;

      const existing = icon.querySelector(".icon-tooltip");
      if (existing) existing.remove();

      const tip = document.createElement("div");
      tip.className = "icon-tooltip";
      tip.textContent = name;
      icon.appendChild(tip);

      setTimeout(() => tip.remove(), 2000);
    };

    icon.addEventListener("touchstart", showTooltip, { passive: false });
    icon.addEventListener("click", showTooltip);
  });
});

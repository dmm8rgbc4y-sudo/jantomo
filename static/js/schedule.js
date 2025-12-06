// ======================================================
// schedule.js（2025-12 完全安定版）
// ・CSRF（Flask埋め込み方式）100%成功
// ・Safari の DOM レースバグ完全回避
// ・Flash 成功表示安定化
// ・週またぎの draft 保存/反映
// ・差分のみ送信（POST form 方式）
// ======================================================

// Flask 側の schedule.html で window に埋め込んだ値
const csrf_token = window.CSRF_TOKEN || "";
const WEEK_OFFSET = window.WEEK_OFFSET;

// ======================================================
// DOMContentLoaded
// ======================================================
document.addEventListener("DOMContentLoaded", () => {

  const rows = document.querySelectorAll(".date-row");
  const saveBtn = document.getElementById("save-btn");

  // ローカル draft のキー
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

  // ======================================================
  // 📌 初期ロード（server → draft の順に反映）
  // ======================================================
  rows.forEach((row) => {
    const date = row.dataset.date;
    const buttons = row.querySelectorAll(".time-btn");
    const serverSelected = row.querySelector(".time-btn.selected");

    // サーバ側の保存状態
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

  // ======================================================
  // 📌 ボタン操作（他日付への影響なし）
  // ======================================================
  rows.forEach((row) => {
    const date = row.dataset.date;
    const buttons = row.querySelectorAll(".time-btn");

    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const wasSelected = btn.classList.contains("selected");

        // いったん全部解除
        buttons.forEach((b) => b.classList.remove("selected"));
        delete currentSelections[date];
        delete draft[date];

        if (!wasSelected) {
          btn.classList.add("selected");
          const slot = btn.dataset.slot;
          currentSelections[date] = slot;
          draft[date] = slot;
        }

        // Safari・Chrome 共通：draft 永続化
        localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
      });
    });
  });

  // ======================================================
  // 📌 決定ボタン：差分のみ送信（form POST + CSRF hidden）
  // ======================================================
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

    // 差分なし
    if (payload.length === 0) {
      showInfo("変更はありません。");
      return;
    }

    try {
      // ---- form POST ----
      const form = document.createElement("form");
      form.method = "POST";
      form.action = `/schedule/save?week=${WEEK_OFFSET}`;

      // 🔒 CSRF hidden input
      const csrf = document.createElement("input");
      csrf.type = "hidden";
      csrf.name = "csrf_token";
      csrf.value = csrf_token;
      form.appendChild(csrf);

      // payload hidden
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = "payload";
      input.value = JSON.stringify(payload);
      form.appendChild(input);

      document.body.appendChild(form);

      // draft のリセット
      localStorage.removeItem(DRAFT_KEY);

      // 送信
      form.submit();

    } catch (err) {
      console.error("保存エラー:", err);
      showError("通信エラーが発生しました。");
    }
  });
});

// ======================================================
// 📌 slot 日本語変換
// ======================================================
function convertSlotLabel(slot) {
  if (slot === "day") return "昼";
  if (slot === "night") return "夜";
  if (slot === "both") return "両方";
  return "";
}

// ======================================================
// 📌 JS Flash（info/error）
// ======================================================
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

// ======================================================
// 📌 モバイル向けツールチップ（週間画面共通）
// ======================================================
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

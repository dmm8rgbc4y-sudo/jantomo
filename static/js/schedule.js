// schedule.js
document.addEventListener("DOMContentLoaded", () => {
  const rows = document.querySelectorAll(".date-row");
  const saveBtn = document.getElementById("save-btn");

  // 全日分の初期状態（ロード時の状態）を記録
  const initialSelections = {};
  const currentSelections = {};

  rows.forEach((row) => {
    const date = row.dataset.date;
    const selectedBtn = row.querySelector(".time-btn.selected");
    if (selectedBtn) {
      initialSelections[date] = selectedBtn.dataset.slot;
      currentSelections[date] = selectedBtn.dataset.slot;
    }
  });

  // --- ボタン操作 ---
  rows.forEach((row) => {
    const date = row.dataset.date;
    const buttons = row.querySelectorAll(".time-btn");

    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const isSelected = btn.classList.contains("selected");

        // まず全ボタン解除
        buttons.forEach((b) => b.classList.remove("selected"));
        delete currentSelections[date];

        // 未選択状態からクリック → 新規選択
        if (!isSelected) {
          btn.classList.add("selected");
          currentSelections[date] = btn.dataset.slot;
        }
      });
    });
  });

  // --- 決定ボタン ---
  saveBtn.addEventListener("click", async () => {
    const payload = [];

    // 変更のあった日だけ送信
    Object.keys(currentSelections).forEach((date) => {
      const before = initialSelections[date] || "";
      const after = currentSelections[date] || "";

      if (before !== after) {
        payload.push({
          date,
          slot: convertSlotLabel(after),
        });
      }
    });

    // 削除された日も追加（初期→あり, 現在→なし）
    Object.keys(initialSelections).forEach((date) => {
      if (!currentSelections[date]) {
        payload.push({
          date,
          slot: "", // 未選択を明示
        });
      }
    });

    if (payload.length === 0) {
      showFlashMessage("変更はありません。", "info");
      return;
    }

    try {
      const response = await fetch("/schedule/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        credentials: "same-origin",
      });

      if (response.redirected) {
        window.location.href = response.url;
      } else {
        window.location.reload();
      }
    } catch (e) {
      showFlashMessage("通信エラーが発生しました。", "error");
    }
  });
});

// --- slotを日本語に変換 ---
function convertSlotLabel(slot) {
  if (slot === "day") return "昼";
  if (slot === "night") return "夜";
  if (slot === "both") return "両方";
  return "";
}

// --- Flashメッセージ ---
function showFlashMessage(message, type) {
  const flash = document.createElement("div");
  flash.className = `flash-message ${type}`;
  flash.innerText = message;
  flash.style.position = "fixed";
  flash.style.bottom = "20px";
  flash.style.left = "50%";
  flash.style.transform = "translateX(-50%)";
  flash.style.padding = "10px 18px";
  flash.style.borderRadius = "8px";
  flash.style.fontWeight = "700";
  flash.style.color = "white";
  flash.style.zIndex = "9999";
  flash.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.15)";
  flash.style.backgroundColor =
    type === "success"
      ? "#2ecc71"
      : type === "info"
      ? "#3498db"
      : "#e74c3c";

  document.body.appendChild(flash);
  setTimeout(() => {
    flash.style.transition = "opacity 0.5s";
    flash.style.opacity = "0";
  }, 1800);
  setTimeout(() => flash.remove(), 2500);
}

// ==========================
// 📱 スマホ対応ツールチップ（iOS完全対応版）
// ==========================
document.addEventListener("DOMContentLoaded", () => {
  const icons = document.querySelectorAll(".icon-frame");

  icons.forEach((icon) => {
    const showTooltip = (e) => {
      // iOSの長押しメニューを無効化
      e.preventDefault();

      const name = icon.getAttribute("data-name");
      if (!name) return;

      // 既に表示中なら削除して再生成
      const existing = icon.querySelector(".icon-tooltip");
      if (existing) existing.remove();

      // 吹き出し生成
      const tooltip = document.createElement("div");
      tooltip.className = "icon-tooltip";
      tooltip.textContent = name;
      icon.appendChild(tooltip);

      // 2秒後に消える
      setTimeout(() => tooltip.remove(), 2000);
    };

    // 📱 スマホの即時タップ対応（preventDefaultが効くように passive: false）
    icon.addEventListener("touchstart", showTooltip, { passive: false });

    // 💻 PCブラウザ用クリック対応
    icon.addEventListener("click", showTooltip);
  });
});

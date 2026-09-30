"use strict";

import { t } from "../core/i18n.js";

// Icons smaller than this are drawn larger in the popup, with crisp pixels.
const MIN_PREVIEW_SIDE = 176;

function el(id) {
  return document.getElementById(id);
}

function parseRegion(text) {
  const values = (text || "").split(",").map(Number);
  return values.length === 4 && values.every(Number.isInteger) ? values : null;
}

// Scale a small image up by a whole factor so it stays sharp.
function upscaleSmall(img, width, height) {
  const factor = Math.max(1, Math.floor(MIN_PREVIEW_SIDE / Math.max(width, height)));
  img.style.width = factor > 1 ? `${width * factor}px` : "";
  img.classList.toggle("icon-preview-pixelated", factor > 1);
}

export const iconPreviewMethods = {
  _iconPreviewEscHandler: null,
  _iconPreviewRequest: 0,

  // The icon cell under a click, or null. Missing icons have nothing to show.
  _iconPreviewTarget(target) {
    const cell = target.closest(".sprite-cell, .icon-cell[data-icon-path]");
    if (!cell || cell.classList.contains("icon-cell-missing")) return null;
    return cell;
  },

  openIconPreviewFromCell(cell) {
    if (cell.classList.contains("sprite-cell")) {
      this.openIconPreview(cell.dataset.spritePath, parseRegion(cell.dataset.spriteRegion));
    } else {
      this.openIconPreview(cell.dataset.iconPath, null);
    }
  },

  async openIconPreview(path, region) {
    if (!path) return;
    const request = ++this._iconPreviewRequest;

    el("icon-preview-status").textContent = t("iconPreview.loading");
    el("icon-preview-status").hidden = false;
    el("icon-preview-sprite").hidden = true;
    el("icon-preview-full").hidden = true;
    el("icon-preview-path").textContent = path;
    el("icon-preview-overlay").hidden = false;
    this._bindIconPreviewClose();

    const result = await window.pywebview.api.get_icon_preview(path, region);
    // A newer click, or a close, replaced this request while it loaded.
    if (request !== this._iconPreviewRequest) return;

    if (!result?.url) {
      el("icon-preview-status").textContent = result?.error || "-";
      return;
    }
    el("icon-preview-status").hidden = true;
    this._showIconPreview(result);
  },

  _showIconPreview(result) {
    const image = el("icon-preview-image");
    image.src = result.url;
    // The preview may be scaled down; lay it out at the image's own size.
    image.style.width = "";
    image.classList.remove("icon-preview-pixelated");
    if (!result.region) upscaleSmall(image, result.width, result.height);

    el("icon-preview-caption").textContent = result.region
      ? `${t("iconPreview.sheet")} · ${t("iconPreview.size", { width: result.width, height: result.height })}`
      : t("iconPreview.size", { width: result.width, height: result.height });
    el("icon-preview-full").hidden = false;

    const regionBox = el("icon-preview-region");
    if (!result.region) {
      regionBox.hidden = true;
      el("icon-preview-sprite").hidden = true;
      return;
    }

    const [x1, y1, x2, y2] = result.region;
    Object.assign(regionBox.style, {
      left: `${(x1 / result.width) * 100}%`,
      top: `${(y1 / result.height) * 100}%`,
      width: `${((x2 - x1) / result.width) * 100}%`,
      height: `${((y2 - y1) / result.height) * 100}%`,
    });
    regionBox.title = t("iconPreview.region", { x1, y1, x2, y2 });
    regionBox.hidden = false;

    const sprite = el("icon-preview-sprite-image");
    sprite.src = result.sprite;
    upscaleSmall(sprite, x2 - x1, y2 - y1);
    el("icon-preview-sprite").hidden = false;
  },

  _bindIconPreviewClose() {
    if (this._iconPreviewEscHandler) return;
    this._iconPreviewEscHandler = (event) => {
      if (event.key === "Escape") this.closeIconPreview();
    };
    document.addEventListener("keydown", this._iconPreviewEscHandler);
  },

  closeIconPreview() {
    this._iconPreviewRequest++;
    el("icon-preview-overlay").hidden = true;
    el("icon-preview-image").removeAttribute("src");
    el("icon-preview-sprite-image").removeAttribute("src");
    if (this._iconPreviewEscHandler) {
      document.removeEventListener("keydown", this._iconPreviewEscHandler);
      this._iconPreviewEscHandler = null;
    }
  },

  _setupIconPreview() {
    // A click on the dimmed backdrop closes, a click inside the popup does not.
    el("icon-preview-overlay").addEventListener("click", (event) => {
      if (event.target.id === "icon-preview-overlay") this.closeIconPreview();
    });
  },
};

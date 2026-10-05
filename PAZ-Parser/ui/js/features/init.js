"use strict";

import { loadLang, applyTranslations } from "../core/i18n.js";

export const initMethods = {
  async init() {
    const saved = localStorage.getItem("outputPath");
    if (saved) document.getElementById("output-path").value = saved;

    const [status, settings] = await Promise.all([
      window.pywebview.api.get_status(),
      window.pywebview.api.get_settings(),
    ]);
    await loadLang(settings.language ?? "en");
    applyTranslations();
    // After loadLang, so a keyed status reads in the saved language.
    this.setStatus(status);
    this._applyTableRowHeight(settings.table_row_height);

    this._setupDividers();
    this._setupOutputPathSave();
    this._setupPreviewTableSelection();
    this._setupIconPreview();
    this._setupEscapeClear();
    this._setupImageZoom();
    this._initTabSearch();
    this._initGlobalSearch();

    const last = await window.pywebview.api.get_last_folder();
    if (last && last.path) {
      this._showFolderPath(last.path);
      await this._showTreeLoading();
      window.pywebview.api.open_folder_path(last.path);
    }
  },
};

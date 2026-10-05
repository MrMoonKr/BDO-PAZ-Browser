"use strict";

export const folderMethods = {
  // Drops data-i18n, so applyTranslations() (on a settings save) keeps the
  // path instead of writing "No folder selected" back.
  _showFolderPath(path) {
    const el = document.getElementById("folder-path");
    el.textContent = path;
    el.classList.remove("muted");
    el.removeAttribute("data-i18n");
  },

  async openFolder() {
    await this._showTreeLoading();
    const result = await window.pywebview.api.open_folder();
    if (result.ok) {
      this._showFolderPath(result.path);
    } else if (this._isFolderLoaded) {
      // Cancelled: the backend still holds the previous folder, so bring
      // its tree and search back.
      this._loadTreeRoot();
    } else {
      document.getElementById("tree").innerHTML = "";
    }
  },

  onFolderLoaded() {
    this._isFolderLoaded = true;
    this._loadTreeRoot();
  },
};

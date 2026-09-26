"use strict";

export const folderMethods = {
  async openFolder() {
    await this._showTreeLoading();
    const result = await window.pywebview.api.open_folder();
    if (result.ok) {
      const el = document.getElementById("folder-path");
      el.textContent = result.path;
      el.classList.remove("muted");
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

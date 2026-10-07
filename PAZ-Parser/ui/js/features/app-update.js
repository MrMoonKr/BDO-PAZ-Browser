"use strict";

import { t } from "../core/i18n.js";

// The exe's update banner: checked once on start, when "Check for updates on
// start" is on. A click opens the popup with the release notes, an Update
// button and Open on GitHub. Updating downloads in the background, then the
// app closes and a helper swaps the new version in and restarts it.
export const appUpdateMethods = {
  // get_app_update(): version, current, notes_html (escaped by Python), page_url.
  _appUpdate: null,
  _appUpdateEscHandler: null,

  async checkAppUpdate() {
    const update = await window.pywebview.api.get_app_update();
    if (!update?.version) return;
    this._appUpdate = update;
    document.getElementById("app-update-text").textContent = t("appUpdate.available", { version: update.version });
    document.getElementById("app-update").hidden = false;
  },

  // Hidden for this run only; the next start checks again.
  dismissAppUpdate() {
    document.getElementById("app-update").hidden = true;
  },

  openAppUpdate() {
    const update = this._appUpdate;
    if (!update) return;
    document.getElementById("app-update-title").textContent = t("appUpdate.title", { version: update.version });
    document.getElementById("app-update-current").textContent = t("appUpdate.current", { version: update.current });
    document.getElementById("app-update-notes").innerHTML = update.notes_html;
    document.getElementById("app-update-install").disabled = false;
    document.getElementById("app-update-overlay").hidden = false;
    this._appUpdateEscHandler = (event) => {
      if (event.key === "Escape") this.closeAppUpdate();
    };
    document.addEventListener("keydown", this._appUpdateEscHandler);
  },

  closeAppUpdate() {
    document.getElementById("app-update-overlay").hidden = true;
    if (this._appUpdateEscHandler) {
      document.removeEventListener("keydown", this._appUpdateEscHandler);
      this._appUpdateEscHandler = null;
    }
  },

  openAppUpdatePage() {
    window.pywebview.api.open_url(this._appUpdate?.page_url ?? "");
  },

  async installAppUpdate() {
    const button = document.getElementById("app-update-install");
    button.disabled = true;
    const result = await window.pywebview.api.install_app_update();
    if (!result?.ok) {
      button.disabled = false;
      this.showError(result?.error ?? t("appUpdate.failed", { message: "" }));
      return;
    }
    // The status bar shows the download; the app closes once it is unpacked.
    this.closeAppUpdate();
    this.dismissAppUpdate();
  },

  // Pushed by the backend when the download or unpacking failed.
  onAppUpdateFailed(message) {
    this.showError(t("appUpdate.failed", { message }));
    document.getElementById("app-update").hidden = false;
  },

  _setupAppUpdate() {
    // A click on the dimmed backdrop closes, a click inside the popup does not.
    document.getElementById("app-update-overlay").addEventListener("click", (event) => {
      if (event.target.id === "app-update-overlay") this.closeAppUpdate();
    });
  },
};

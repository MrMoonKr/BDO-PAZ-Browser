"use strict";

import { t } from "../core/i18n.js";

export const tableMethods = {
  // Parsed tables sort on the server over every record, not just the page on
  // screen. Only headers the handler gave a sort key are clickable.
  _initTableSort(container) {
    container.querySelectorAll("th.sortable[data-sort-key]").forEach((th) => {
      const field = th.dataset.sortKey;
      const isActive = this._parsedSort?.field === field;
      th.classList.toggle("sort-asc", isActive && this._parsedSort.dir === "asc");
      th.classList.toggle("sort-desc", isActive && this._parsedSort.dir === "desc");
      th.addEventListener("click", () => this._sortParsedTable(th, field));
    });
  },

  // A new column starts ascending; the active column flips. Either way the
  // view returns to page 1. The header shows a spinner until the sorted page
  // replaces the table.
  async _sortParsedTable(th, field) {
    // CSS already blocks header clicks while busy; this covers keyboard or
    // scripted clicks too, so heavy sorts never stack up.
    if (document.getElementById("preview-content").classList.contains("parsed-busy")) return;
    const isFlip = this._parsedSort?.field === field && this._parsedSort.dir === "asc";
    const sort = { field, dir: isFlip ? "desc" : "asc" };

    th.classList.add("sort-pending");
    const isLoaded = await this._gotoParsedPage(0, sort);
    // On success the table was re-rendered; on failure clear the spinner.
    th.classList.remove("sort-pending");
    // Match positions belong to the previous order. Off-tab, switching back
    // resets the search anyway.
    if (isLoaded && this._activeTab === "parsed") this._resetTabSearch();
  },

  _initTableIcons(container) {
    const cells = [...container.querySelectorAll(".icon-cell[data-icon-path]")];
    if (!cells.length) return;

    if (!this._iconUrlCache) {
      this._iconUrlCache = new Map();
    }

    if (!this._iconObserver) {
      this._iconObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          this._iconObserver.unobserve(entry.target);
          this._loadIconCell(entry.target);
        });
      }, {
        root: document.getElementById("preview-content"),
        rootMargin: "128px",
      });
    }

    cells.forEach((cell) => {
      if (cell.dataset.iconObserved === "1") return;
      cell.dataset.iconObserved = "1";
      this._iconObserver.observe(cell);
    });
  },

  async _loadIconCell(cell) {
    const path = cell.dataset.iconPath;
    if (!path || cell.dataset.iconLoaded === "1") return;
    cell.dataset.iconLoaded = "1";

    let url = this._iconUrlCache.get(path);
    if (url === undefined) {
      const result = await window.pywebview.api.get_icon_data_url(path);
      url = result?.url || "";
      this._iconUrlCache.set(path, url);
    }

    if (!url) {
      // Not shipped in the PAZ. Collapse to a dash rather than leave an empty
      // swatch beside a path that resolves to nothing. The full path stays in
      // the cell's title attribute.
      cell.classList.add("icon-cell-missing");
      cell.textContent = "-";
      return;
    }

    const img = document.createElement("img");
    img.className = "icon-cell-thumb";
    img.src = url;
    img.alt = "";
    img.loading = "lazy";

    const thumb = cell.querySelector(".icon-cell-thumb");
    if (thumb) {
      thumb.replaceWith(img);
    } else {
      cell.prepend(img);
    }
  },

  _setupPreviewTableSelection() {
    const previewContent = document.getElementById("preview-content");

    previewContent.addEventListener("click", (event) => {
      const row = event.target.closest(".data-table tbody tr");

      if (!row || !previewContent.contains(row)) {
        return;
      }

      const table = row.closest(".data-table");

      table.querySelectorAll("tbody tr.selected-row").forEach((selectedRow) => {
        selectedRow.classList.remove("selected-row");
      });

      row.classList.add("selected-row");
    });

    document.addEventListener("keydown", async (event) => {
      if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== "c") {
        return;
      }

      const selectedRow = previewContent.querySelector(".data-table tbody tr.selected-row");

      if (!selectedRow) {
        return;
      }

      const selectedText = window.getSelection().toString();

      if (selectedText) {
        return;
      }

      event.preventDefault();

      const values = Array.from(selectedRow.querySelectorAll("td"))
        .map((cell) => cell.innerText.trim())
        .join("\t");

      await navigator.clipboard.writeText(values);
      this.setStatus({ key: "status.copiedRow" });
    });
  },
};

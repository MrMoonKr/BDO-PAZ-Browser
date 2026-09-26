"use strict";

export const app = {
  _selectedPath: null,
  _currentFolderPath: null,
  _extractPaths: new Set(),
  _searchTimer: null,
  _searchSeq: 0,
  _selectSeq: 0,
  _inSearch: false,
  _parsedHtml: null,
  _hexHtml: null,
  _activeTab: "hex",
  _inGlobalSearch: false,
  _hexPage: 0,
  _hexTotalPages: 1,
  _parsedPage: 0,
  _parsedTotalPages: 1,
  // Active parsed-table sort, {field, dir}, or null for file order.
  _parsedSort: null,
  // Bumped per parsed page request so late responses can be dropped.
  _parsedPageSeq: 0,
};

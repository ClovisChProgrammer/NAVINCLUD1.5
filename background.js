chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    navIncludSettings: { enabled: false, type: 'none', intensity: 100, shift: 0.5 }
  });
});
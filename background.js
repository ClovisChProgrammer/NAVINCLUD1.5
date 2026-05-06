chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    navIncludSettings: { enabled: false, type: 'none', intensity: 100, shift: 0.5 }
  });
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url?.startsWith('http')) {
    chrome.storage.local.get(['navIncludSettings'], (res) => {
      if (res.navIncludSettings?.enabled) {
        chrome.tabs.sendMessage(tabId, { action: 'applyNavInclud', settings: res.navIncludSettings }).catch(() => {});
      }
    });
  }
});
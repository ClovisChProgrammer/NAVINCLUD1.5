document.addEventListener('DOMContentLoaded', function() {
  var elements = {
    type: document.getElementById('daltonismType'),
    intensity: document.getElementById('intensitySlider'),
    shift: document.getElementById('shiftSlider'),
    enabled: document.getElementById('toggleFilter'),
    intensityVal: document.getElementById('intensityValue'),
    shiftVal: document.getElementById('shiftValue'),
    dragHandle: document.querySelector('.drag-handle'),
    openWizard: document.getElementById('openWizard'),
    openCalibrate: document.getElementById('openCalibrate')
  };

  var updateUi = function(s) {
    if (!s) return;
    elements.type.value = s.type;
    elements.intensity.value = s.intensity;
    elements.shift.value = s.shift * 100;
    elements.enabled.checked = s.enabled;
    elements.intensityVal.textContent = s.intensity + '%';
    elements.shiftVal.textContent = Number(s.shift).toFixed(2);
  };

  var saveAndBroadcast = function() {
    var s = {
      type: elements.type.value,
      intensity: parseInt(elements.intensity.value),
      shift: elements.shift.value / 100,
      enabled: elements.enabled.checked
    };
    elements.intensityVal.textContent = s.intensity + '%';
    elements.shiftVal.textContent = s.shift.toFixed(2);

    chrome.storage.local.set({ navIncludSettings: s });
  };

  chrome.storage.local.get(['navIncludSettings'], function(res) {
    if (res.navIncludSettings) updateUi(res.navIncludSettings);
  });

  chrome.storage.onChanged.addListener(function(changes) {
    if (changes.navIncludSettings) updateUi(changes.navIncludSettings.newValue);
  });

  [elements.type, elements.intensity, elements.shift, elements.enabled].forEach(function(el) {
    el.addEventListener('input', saveAndBroadcast);
  });

  
  // Drag
  elements.dragHandle.addEventListener('mousedown', function(e) {
    if (e.target.closest('button, select, input, a')) return;
    chrome.windows.getCurrent(function(win) {
      var startX = e.screenX, startY = e.screenY;
      var winL = win.left, winT = win.top;
      var onMove = function(ev) {
        chrome.windows.update(win.id, {
          left: Math.round(winL + (ev.screenX - startX)),
          top: Math.round(winT + (ev.screenY - startY))
        });
      };
      var onUp = function() {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      };
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });
  });

  elements.openWizard.onclick = function() {
    chrome.windows.create({ url: 'wizard.html', type: 'popup', width: 420, height: 600 });
  };

  elements.openCalibrate.onclick = function() {
    chrome.windows.create({ url: 'calibrate.html', type: 'popup', width: 800, height: 700 });
  };

});

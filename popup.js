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
    openCalibrate: document.getElementById('openCalibrate'),
    exportResults: document.getElementById('exportResults')
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

    chrome.storage.local.set({ navIncludSettings: s }, function() {
      chrome.tabs.query({}, function(tabs) {
        tabs.forEach(function(t) {
          if (t.url && t.url.startsWith('http')) {
            chrome.tabs.sendMessage(t.id, { action: 'applyNavInclud', settings: s }).catch(function(){});
          }
        });
      });
    });
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

  chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
    if (message.action === 'experienceTick') {
      var mins = Math.floor(message.timeLeft / 60);
      var secs = message.timeLeft % 60;
      var display = mins + ':' + (secs < 10 ? '0' + secs : secs);
      var timerDisplay = document.getElementById('timer-display');
      if (timerDisplay) timerDisplay.textContent = display;

      var section = document.getElementById('test-active-section');
      if (section) section.style.display = 'block';
    }

    if (message.action === 'experienceEnded') {
      var section = document.getElementById('test-active-section');
      if (section) section.style.display = 'none';
    }
  });

  var exitTestBtn = document.getElementById('exitTestBtn');
  if (exitTestBtn) {
    exitTestBtn.onclick = function() {
      chrome.runtime.sendMessage({ action: 'exitExperience' });
      var section = document.getElementById('test-active-section');
      if (section) section.style.display = 'none';
    };
  }
  
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

  // EXPORTAR TODOS OS TESTES - ler todos os testes do array
  elements.exportResults.onclick = function() {
    chrome.storage.local.get(['testHistoryIds'], function(res) {
      var ids = res.testHistoryIds || [];
      if (!Array.isArray(ids) || ids.length === 0) {
        alert('Nenhum teste encontrado para exportar.');
        return;
      }

      // Ler cada teste individualmente para montar o array completo
      var history = [];
      var loaded = 0;

      ids.forEach(function(key) {
        chrome.storage.local.get([key], function(items) {
          if (items[key]) {
            history.push(items[key]);
          }
          loaded++;
          if (loaded === ids.length) {
            // Todos carregados, exportar
            if (history.length === 0) {
              alert('Erro: testes nao encontrados no armazenamento.');
              return;
            }

            var now = new Date();
            var timestamp = now.toISOString().replace(/[:.]/g, '-').slice(0, 19);
            var dataStr = JSON.stringify(history, null, 2);
            var blob = new Blob([dataStr], { type: 'application/json' });
            var url = URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            a.download = 'navinclud_' + history.length + '_testes_' + timestamp + '.json';
            a.click();
            URL.revokeObjectURL(url);
          }
        });
      });
    });
  };
});

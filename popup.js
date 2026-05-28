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
    testCountDisplay: document.getElementById('testCountDisplay'),
    exportStart: document.getElementById('exportStart'),
    exportConfirm1: document.getElementById('exportConfirm1'),
    exportConfirm2: document.getElementById('exportConfirm2'),
    exportNameInput: document.getElementById('exportNameInput'),
    exportResult: document.getElementById('exportResult'),
    exportResultMsg: document.getElementById('exportResultMsg')
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

  function updateTestCount() {
    chrome.storage.local.get(['testHistoryIds'], function(res) {
      var ids = res.testHistoryIds || [];
      if (elements.testCountDisplay) {
        elements.testCountDisplay.textContent = ids.length;
      }
    });
  }

  function resetExportUI() {
    elements.exportStart.style.display = 'block';
    elements.exportConfirm1.style.display = 'none';
    elements.exportConfirm2.style.display = 'none';
    elements.exportNameInput.style.display = 'none';
    elements.exportResult.style.display = 'none';
    document.getElementById('confirmInput').value = '';
    document.getElementById('userNameInput').value = '';
  }

  chrome.storage.local.get(['navIncludSettings'], function(res) {
    if (res.navIncludSettings) updateUi(res.navIncludSettings);
    updateTestCount();
  });

  chrome.storage.onChanged.addListener(function(changes) {
    if (changes.navIncludSettings) updateUi(changes.navIncludSettings.newValue);
    if (changes.testHistoryIds) updateTestCount();
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

  // --- EXPORT FLOW ---

  elements.exportStart.onclick = function() {
    chrome.storage.local.get(['testHistoryIds'], function(res) {
      var ids = res.testHistoryIds || [];
      if (!Array.isArray(ids) || ids.length === 0) {
        alert('Nenhum teste encontrado para exportar.');
        return;
      }
      elements.exportStart.style.display = 'none';
      elements.exportConfirm1.style.display = 'block';
    });
  };

  document.getElementById('exportYes').onclick = function() {
    elements.exportConfirm1.style.display = 'none';
    elements.exportConfirm2.style.display = 'block';
  };

  document.getElementById('exportNo').onclick = function() {
    resetExportUI();
  };

  document.getElementById('cancelBtn').onclick = function() {
    resetExportUI();
  };

  document.getElementById('confirmBtn').onclick = function() {
    var input = document.getElementById('confirmInput');
    if (input.value.trim().toLowerCase() !== 'confirmo') {
      alert('Digite exatamente a palavra CONFIRMO para prosseguir.');
      return;
    }
    elements.exportConfirm2.style.display = 'none';
    elements.exportNameInput.style.display = 'block';
  };

  document.getElementById('cancelExportBtn').onclick = function() {
    resetExportUI();
  };

  document.getElementById('proceedExportBtn').onclick = function() {
    var userName = document.getElementById('userNameInput').value.trim();
    if (!userName) {
      alert('Por favor, informe seu nome.');
      return;
    }

    chrome.storage.local.get(['testHistoryIds'], function(res) {
      var ids = res.testHistoryIds || [];
      if (!Array.isArray(ids) || ids.length === 0) {
        alert('Nenhum teste encontrado para exportar.');
        resetExportUI();
        return;
      }

      var history = [];
      var loaded = 0;

      ids.forEach(function(key) {
        chrome.storage.local.get([key], function(items) {
          if (items[key]) {
            history.push(items[key]);
          }
          loaded++;
          if (loaded === ids.length) {
            if (history.length === 0) {
              alert('Erro: testes nao encontrados no armazenamento.');
              resetExportUI();
              return;
            }

            var now = new Date();
            var timestamp = now.toISOString().replace(/[:.]/g, '-').slice(0, 19);
            var dataStr = JSON.stringify(history, null, 2);
            
            // Download 1: arquivo principal
            var blob1 = new Blob([dataStr], { type: 'application/json' });
            var url1 = URL.createObjectURL(blob1);
            var a = document.createElement('a');
            a.href = url1;
            a.download = 'navinclud_' + history.length + '_testes_' + timestamp + '.json';
            a.click();
            URL.revokeObjectURL(url1);

            // Download 2: backup em DADOS_EXTRAÍDOS
            var blob2 = new Blob([dataStr], { type: 'application/json' });
            var backupFilename = 'DADOS_EXTRAIDOS/bkp_' + userName.replace(/\s+/g, '_') + '_' + timestamp + '.json';
            try {
              chrome.downloads.download({
                url: URL.createObjectURL(blob2),
                filename: backupFilename,
                saveAs: false
              }, function() {
                elements.exportNameInput.style.display = 'none';
                elements.exportResultMsg.innerHTML = 'ARQUIVO E BKP SALVOS COM ÊXITO.<br><small>(Downloads: ' + history.length + ' testes)</small>';
                elements.exportResult.style.display = 'block';
                // Limpa storage apos exportacao
                chrome.storage.local.get(['testHistoryIds'], function(res) {
                  var ids = res.testHistoryIds || [];
                  var keysToRemove = ids.slice();
                  keysToRemove.push('testHistoryIds');
                  chrome.storage.local.remove(keysToRemove, function() { updateTestCount(); });
                });
              });
            } catch(e) {
              // Fallback: segundo download normal se chrome.downloads falhar
              var url2 = URL.createObjectURL(blob2);
              var a2 = document.createElement('a');
              a2.href = url2;
              a2.download = backupFilename.replace('/', '_');
              a2.click();
              URL.revokeObjectURL(url2);

              elements.exportNameInput.style.display = 'none';
              elements.exportResultMsg.innerHTML = 'ARQUIVO E BKP SALVOS COM ÊXITO.<br><small>(Downloads: ' + history.length + ' testes)</small>';
              elements.exportResult.style.display = 'block';
              // Limpa storage apos exportacao
              chrome.storage.local.get(['testHistoryIds'], function(res) {
                var ids = res.testHistoryIds || [];
                var keysToRemove = ids.slice();
                keysToRemove.push('testHistoryIds');
                chrome.storage.local.remove(keysToRemove, function() { updateTestCount(); });
              });
            }
          }
        });
      });
    });
  };

  document.getElementById('zeroYesBtn').onclick = function() {
    chrome.storage.local.get(['testHistoryIds'], function(res) {
      var ids = res.testHistoryIds || [];
      var keysToRemove = ids.slice();
      keysToRemove.push('testHistoryIds');
      chrome.storage.local.remove(keysToRemove, function() {
        updateTestCount();
        resetExportUI();
      });
    });
  };

  document.getElementById('zeroNoBtn').onclick = function() {
    resetExportUI();
  };
});

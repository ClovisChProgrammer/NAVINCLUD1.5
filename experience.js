document.addEventListener('DOMContentLoaded', function() {
  var timeLeft = 120;
  var experienceTabIds = [];
  var timerDisplay = document.getElementById('timer');
  var timerInterval = null;
  var tabsOpened = false;

  function openExperienceTabs() {
    if (tabsOpened) return;
    tabsOpened = true;
    var urls = ['https://www.youtube.com', 'https://www.google.com/search?tbm=isch&q=fotos+bonitas+e+coloridas'];
    urls.forEach(function(url) {
      chrome.tabs.create({ url: url, active: false }, function(tab) {
        experienceTabIds.push(tab.id);
      });
    });
  }

  function updateTimer() {
    var minutes = Math.floor(timeLeft / 60);
    var seconds = timeLeft % 60;
    var display = minutes + ':' + (seconds < 10 ? '0' + seconds : seconds);
    timerDisplay.textContent = display;

    chrome.runtime.sendMessage({
      action: 'experienceTick',
      timeLeft: timeLeft
    });

    if (timeLeft <= 30 && timeLeft > 10) {
      timerDisplay.className = 'warning';
    } else if (timeLeft <= 10) {
      timerDisplay.className = 'critical';
    }

    if (timeLeft <= 0) {
      clearInterval(timerInterval);
      finishExperience();
      return;
    }
    timeLeft--;
  }

  function finishExperience() {
    experienceTabIds.forEach(function(tabId) {
      try { chrome.tabs.remove(tabId); } catch(e) {}
    });

    document.getElementById('experience-active').classList.remove('active');
    document.getElementById('post-experience-screen').classList.add('active');

    chrome.runtime.sendMessage({ action: 'experienceEnded' });
  }

  // Timer robusto
  try {
    openExperienceTabs();
    updateTimer();
    timerInterval = setInterval(updateTimer, 1000);
  } catch(e) {
    console.error('Erro ao iniciar timer:', e);
  }

  // Botao ENCERRAR NAVEGACAO
  document.getElementById('exit-experience-btn').addEventListener('click', function() {
    clearInterval(timerInterval);
    finishExperience();
  });

  // Botao GRAVAR AS RESPOSTAS
  document.getElementById('save-responses-btn').addEventListener('click', function() {
    var visual = document.querySelector('input[name="visualImprovement"]:checked');
    var navEase = document.querySelector('input[name="navigationEase"]:checked');
    var recommend = document.querySelector('input[name="wouldRecommend"]:checked');
    var comfort = document.querySelector('input[name="comfortLevel"]:checked');

    if (!visual || !navEase || !recommend || !comfort) {
      alert('Por favor, responda todas as perguntas antes de gravar.');
      return;
    }

    var experienceData = {
      visualImprovement: visual.value,
      navigationEase: navEase.value,
      wouldRecommend: recommend.value,
      comfortLevel: comfort.value
    };

    chrome.storage.local.get(['lastTestResult'], function(items) {
      var testEntry = items.lastTestResult;
      if (!testEntry) {
        alert('Erro: dados do teste nao encontrados.');
        return;
      }

      testEntry.experiencePostTest = experienceData;
      chrome.storage.local.set({ lastTestResult: testEntry }, function() {
        showThankYou();
      });
    });
  });

  function showThankYou() {
    document.getElementById('post-experience-screen').classList.remove('active');
    document.getElementById('thankyou-screen').classList.add('active');

    chrome.runtime.sendMessage({ action: 'experienceEnded' });

    setTimeout(function() {
      chrome.windows.getCurrent(function(win) {
        if (win && win.id) {
          try { chrome.windows.remove(win.id); } catch(e) {}
        }
      });
    }, 5000);
  }

  // Escutar mensagem de "Sair do Teste" do popup
  chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
    if (message.action === 'exitExperience') {
      clearInterval(timerInterval);
      finishExperience();
    }
  });
});
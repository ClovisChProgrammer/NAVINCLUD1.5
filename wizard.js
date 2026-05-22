const PLATES = [
  { id: 1, img: 'plate1.webp', options: [12, 15, 17, 'Nao sei'], correct: 12, type: 'control' },
  { id: 2, img: 'plate2.webp', options: [73, 13, 8, 'Nao sei'], correct: 73, type: 'control' },
  { id: 3, img: 'plate3.webp', options: [29, 70, 21, 'Nao sei'], correct: 29, type: 'protanopia' },
  { id: 4, img: 'plate4.webp', options: [45, 15, 10, 'Nao sei'], correct: 45, type: 'protanopia' },
  { id: 5, img: 'plate5.webp', options: [6, 3, 8, 'Nao sei'], correct: 6, type: 'protanomaly' },
  { id: 6, img: 'plate6.webp', options: [8, 3, 5, 'Nao sei'], correct: 8, type: 'protanomaly' },
  { id: 7, img: 'plate7.webp', options: [8, 3, 5, 'Nao sei'], correct: 8, type: 'deuteranopia' },
  { id: 8, img: 'plate8.webp', options: [5, 2, 6, 'Nao sei'], correct: 5, type: 'deuteranopia' },
  { id: 9, img: 'plate9.webp', options: [2, 8, 6, 'Nao sei'], correct: 2, type: 'deuteranomaly' },
  { id: 10, img: 'plate10.webp', options: [15, 13, 10, 'Nao sei'], correct: 15, type: 'deuteranomaly' },
  { id: 11, img: 'plate11.webp', options: [6, 1, 12, 'Nao sei'], correct: 6, type: 'tritanopia' },
  { id: 12, img: 'plate12.webp', options: [3, 5, 8, 'Nao sei'], correct: 3, type: 'tritanopia' },
  { id: 13, img: 'plate13.webp', options: [26, 21, 24, 'Nao sei'], correct: 26, type: 'tritanomaly' },
  { id: 14, img: 'plate14.webp', options: [42, 12, 44, 'Nao sei'], correct: 42, type: 'tritanomaly' },
  { id: 15, img: 'plate15.webp', options: [7, 4, 1, 'Nao sei'], correct: 7, type: 'achromatopsia' },
  { id: 16, img: 'plate16.webp', options: [16, 13, 10, 'Nao sei'], correct: 16, type: 'achromatopsia' },
  { id: 17, img: 'plate17.webp', options: [4, 1, 7, 'Nao sei'], correct: 4, type: 'achromatomaly' },
  { id: 18, img: 'plate18.webp', options: [10, 13, 8, 'Nao sei'], correct: 10, type: 'achromatomaly' }
];

let currentStep = 0;
let errors = {
  protanopia: 0, protanomaly: 0,
  deuteranopia: 0, deuteranomaly: 0,
  tritanopia: 0, tritanomaly: 0,
  achromatopsia: 0, achromatomaly: 0,
  control: 0
};
let correctCount = 0;
let timeouts = {
  protanopia: 0, protanomaly: 0,
  deuteranopia: 0, deuteranomaly: 0,
  tritanopia: 0, tritanomaly: 0,
  achromatopsia: 0, achromatomaly: 0,
  control: 0
};
let plateStartTime = 0;
let timerInterval = null;
let reactionTimes = [];
let preTestData = { sexo: '', idade: '', turma: '' };
let scorePoints = {};
PLATES.forEach(function(p) { scorePoints[p.type] = 0; });
let testPerception = [];
let currentTestEntry = null;

function getParentType(type) {
  if (type.startsWith('protan')) return 'protan';
  if (type.startsWith('deuteran')) return 'deuteran';
  if (type.startsWith('tritan')) return 'tritan';
  if (type.startsWith('achroma')) return 'achromat';
  return type;
}

document.addEventListener('DOMContentLoaded', function() {
  var plateImg = document.getElementById('plate-display');
  var optionsContainer = document.getElementById('options-container');
  var progressFill = document.getElementById('progress-fill');
  var timerDisplay = document.getElementById('timer');

  // Pre-teste
  document.getElementById('pre-test-btn').onclick = function() {
    var sexo = document.getElementById('preSexo').value;
    var idade = document.getElementById('preIdade').value;
    var turma = document.getElementById('preTurma').value.trim();
    if (!sexo) { alert('Por favor, selecione seu sexo.'); return; }
    if (!idade || parseInt(idade) < 5 || parseInt(idade) > 100) { alert('Por favor, informe uma idade valida (5 a 100).'); return; }
    if (!turma) { alert('Por favor, informe sua sala e turma.'); return; }
    preTestData = { sexo: sexo, idade: parseInt(idade), turma: turma };
    document.getElementById('pre-test-screen').classList.remove('active');
    document.getElementById('quiz-container').classList.add('active');
    renderStep();
  };

  function resetTestState() {
    currentStep = 0;
    errors = {
      protanopia: 0, protanomaly: 0,
      deuteranopia: 0, deuteranomaly: 0,
      tritanopia: 0, tritanomaly: 0,
      achromatopsia: 0, achromatomaly: 0,
      control: 0
    };
    correctCount = 0;
    timeouts = {
      protanopia: 0, protanomaly: 0,
      deuteranopia: 0, deuteranomaly: 0,
      tritanopia: 0, tritanomaly: 0,
      achromatopsia: 0, achromatomaly: 0,
      control: 0
    };
    reactionTimes = [];
    scorePoints = {};
    PLATES.forEach(function(p) { scorePoints[p.type] = 0; });
    testPerception = [];
    currentTestEntry = null;
    if (progressFill) progressFill.style.width = '0%';
  }

  function renderStep() {
    if (currentStep >= PLATES.length) {
      clearInterval(timerInterval);
      showPerceptionQuestion();
      return;
    }
    var plate = PLATES[currentStep];
    plateImg.src = 'images/' + plate.img;
    optionsContainer.innerHTML = '';
    plateStartTime = Date.now();

    timerDisplay.textContent = '0s';
    timerDisplay.className = '';

    var timeElapsed = 0;
    clearInterval(timerInterval);

    timerInterval = setInterval(function() {
      timeElapsed++;
      timerDisplay.textContent = timeElapsed + 's';
      if (timeElapsed <= 5) {
        timerDisplay.className = '';
      } else if (timeElapsed <= 10) {
        timerDisplay.className = 'warning';
      } else {
        timerDisplay.className = 'critical';
      }
       if (timeElapsed >= 15) {
         clearInterval(timerInterval);
         var reactionTime = Date.now() - plateStartTime;
         reactionTimes.push(reactionTime);
         timeouts[plate.type]++;
         errors[plate.type]++;
         currentStep++;
        if (progressFill) progressFill.style.width = (currentStep / PLATES.length * 100) + '%';
        renderStep();
      }
    }, 1000);

    // Randomizar ordem das opções (Fisher-Yates shuffle)
    var shuffledOptions = plate.options.slice();
    for (var i = shuffledOptions.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var temp = shuffledOptions[i];
      shuffledOptions[i] = shuffledOptions[j];
      shuffledOptions[j] = temp;
    }

    shuffledOptions.forEach(function(opt) {
      var btn = document.createElement('button');
      btn.className = 'option-btn';
      btn.textContent = opt;
      btn.onclick = function() {
        clearInterval(timerInterval);
        var reactionTime = Date.now() - plateStartTime;
        reactionTimes.push(reactionTime);

        var timeTaken = reactionTime / 1000;
        if (String(opt) !== String(plate.correct)) {
          errors[plate.type]++;
        } else {
          correctCount++;
          if (timeTaken <= 5) {
            scorePoints[plate.type] += 1;
          } else if (timeTaken > 5 && timeTaken <= 10) {
            scorePoints[plate.type] += 0.5;
          }
        }

        currentStep++;
        if (progressFill) progressFill.style.width = (currentStep / PLATES.length * 100) + '%';
        renderStep();
      };
      optionsContainer.appendChild(btn);
    });
  }

  function showPerceptionQuestion() {
    document.getElementById('quiz-container').classList.remove('active');
    document.getElementById('perception-screen').classList.add('active');
  }

  // Handler para "O que achou do teste?"
  document.getElementById('perception-btn').onclick = function() {
    var checked = Array.from(document.querySelectorAll('input[name="testPerception"]:checked'));
    if (checked.length === 0) {
      alert('Por favor, marque pelo menos uma opcao.');
      return;
    }
    testPerception = checked.map(function(el) { return el.value; });

    document.getElementById('perception-screen').classList.remove('active');

    var correctPercent = (correctCount / 18) * 100;

    if (errors.control > 0) {
      document.getElementById('results-screen').classList.add('active');
      document.getElementById('result-text').innerHTML =
        '<p style="color:red;">Erro em placas de controle - calibracao de monitor incorreta.</p>' +
        '<p>Por favor, recalibre seu monitor usando a pagina de calibracao e refaca o teste.</p>';
      document.getElementById('apply-wizard').style.display = 'none';
      return;
    }

    if (correctPercent >= 90) {
      document.getElementById('normal-post-screen').classList.add('active');
    } else {
      var parentErrors = {};
      Object.keys(errors).forEach(function(k) {
        if (k !== 'control' && errors[k] > 0) {
          var parent = getParentType(k);
          parentErrors[parent] = (parentErrors[parent] || 0) + errors[k];
        }
      });

      var defectTypes = Object.keys(parentErrors).filter(function(k) { return parentErrors[k] > 0; });

      if (defectTypes.length === 1) {
        var defectType = defectTypes[0];
        var nopiaSuffix = (defectType === 'achromat') ? 'opsia' : 'opia';
        var filterType = defectType + nopiaSuffix;
        var intensity = 100, shift = 0.5;

        var maliaSuffix = 'omaly';
        var maliaErrors = errors[defectType + maliaSuffix] || 0;
        var nopiaErrors = errors[defectType + nopiaSuffix] || 0;
        if (maliaErrors > 0 && nopiaErrors === 0) {
          filterType = defectType + maliaSuffix;
          intensity = 80; shift = 0.6;
        }

        document.getElementById('invite-text').innerHTML =
          'De acordo com seu teste, ele esta apontando possivel <strong>' + filterType.toUpperCase() + '</strong>.<br>' +
          'Por isso convidamos voce a fazer uma experiencia de 2 minutos apenas.';
        document.getElementById('experience-invite-screen').classList.add('active');

        document.getElementById('start-experience-btn').onclick = function() {
          var finalSettings = { type: filterType, intensity: intensity, shift: shift, enabled: true };

          currentTestEntry = buildTestEntry('deficient', {
            visualImprovement: '',
            navigationEase: '',
            wouldRecommend: '',
            comfortLevel: ''
          }, finalSettings);

          var testKey = 'test_' + currentTestEntry.testId;
          var toSave = {};
          toSave[testKey] = currentTestEntry;

          chrome.storage.local.get(['testHistoryIds'], function(res) {
            var ids = res.testHistoryIds || [];
            ids.push(testKey);
            toSave['testHistoryIds'] = ids;

            chrome.storage.local.set(toSave, function() {
              chrome.storage.local.set({ 'activeExperienceTestKey': testKey }, function() {
                chrome.storage.local.set({ navIncludSettings: finalSettings }, function() {
                  chrome.windows.create({
                    url: 'experience.html',
                    type: 'popup',
                    width: 600,
                    height: 700
                  }, function() {
                    chrome.windows.getCurrent(function(win) {
                      chrome.windows.remove(win.id);
                    });
                  });
                  chrome.tabs.query({}, function(tabs) {
                    tabs.forEach(function(t) {
                      if (t.url && t.url.startsWith('http')) {
                        chrome.tabs.sendMessage(t.id, { action: 'applyNavInclud', settings: finalSettings }).catch(function(){});
                      }
                    });
                  });
                });
              });
            });
          });
        };
      } else {
        document.getElementById('results-screen').classList.add('active');
        document.getElementById('result-text').innerHTML =
          '<p style="color:orange;">Erros em multiplos tipos de daltonismo detectados.</p>' +
          '<p>Recomendamos recalibrar o monitor e refazer o teste.</p>';
        document.getElementById('apply-wizard').style.display = 'none';
      }
    }
  };

  // Botao NOVO TESTE (visao normal >=90%)
  document.getElementById('new-test-btn').onclick = function() {
    resetTestState();
    document.getElementById('congrats-screen').classList.remove('active');
    document.getElementById('pre-test-screen').classList.add('active');
  };

  // Botao finalizar normal (questionario "ja fez antes?")
  document.getElementById('normal-post-btn').onclick = function() {
    var alreadyTaken = document.querySelector('input[name="alreadyTaken"]:checked');
    if (!alreadyTaken) { alert('Por favor, responda se ja fez este teste antes.'); return; }

    saveTestResult('normal', {
      alreadyTaken: alreadyTaken.value
    });

    document.getElementById('normal-post-screen').classList.remove('active');
    document.getElementById('congrats-screen').classList.add('active');
    document.getElementById('congrats-text').innerHTML =
      'Obrigado por participar da pesquisa de TCC.<br><br>' +
      'Seus dados foram gravados com sucesso.';
    document.getElementById('new-test-btn').textContent = 'NOVO TESTE';
  };

  function buildTestEntry(testType, extraData, filterSettings) {
    var correctPercent = (correctCount / 18) * 100;

    var parentErrors = {};
    Object.keys(errors).forEach(function(k) {
      if (k !== 'control' && errors[k] > 0) {
        var parent = getParentType(k);
        parentErrors[parent] = (parentErrors[parent] || 0) + errors[k];
      }
    });

    var detectedDefect = 'none';
    if (Object.keys(parentErrors).length === 1) {
      var p = Object.keys(parentErrors)[0];
      var nopiaSuffix = (p === 'achromat') ? 'opsia' : 'opia';
      var hasOmalia = errors[p + 'omaly'] > 0;
      detectedDefect = p + (hasOmalia ? 'omaly' : nopiaSuffix);
    }

    var testEntry = {
      testId: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      terminalId: 'navinclud-' + crypto.randomUUID().slice(0,8),
      preTest: preTestData,
      testResults: {
        totalPlates: 18,
        correctCount: correctCount,
        correctPercent: correctPercent,
        avgReactionTimeMs: reactionTimes.length > 0 ? Math.round(reactionTimes.reduce(function(a,b) { return a+b; }, 0) / reactionTimes.length) : 0,
        errorsByType: errors,
        scorePointsByType: scorePoints,
        detectedDefect: detectedDefect,
        controlPlateErrors: errors.control > 0,
        testPerception: testPerception
      }
    };

    if (testType === 'normal') {
      testEntry.normalPostTest = {
        alreadyTaken: extraData ? extraData.alreadyTaken : ''
      };
    } else {
      testEntry.experiencePostTest = {
        visualImprovement: '',
        navigationEase: '',
        wouldRecommend: '',
        comfortLevel: ''
      };
      testEntry.appliedFilter = {
        type: filterSettings.type,
        intensity: filterSettings.intensity,
        shift: filterSettings.shift,
        enabled: filterSettings.enabled
      };
    }

    return testEntry;
  }

  function saveTestResult(testType, extraData) {
    var testEntry = buildTestEntry(testType, extraData, null);

    var testKey = 'test_' + testEntry.testId;
    chrome.storage.local.get(['testHistoryIds'], function(res) {
      var ids = res.testHistoryIds || [];
      ids.push(testKey);
      var toSave = {};
      toSave[testKey] = testEntry;
      toSave['testHistoryIds'] = ids;
      chrome.storage.local.set(toSave, function() {
        console.log('Teste salvo com chave:', testKey, 'Total no historico:', ids.length);
      });
    });
  }

  document.getElementById('apply-wizard').onclick = function() {
    chrome.storage.local.get(['navIncludSettings'], function(res) {
      var settings = res.navIncludSettings || { type: 'none', intensity: 100, shift: 0.5, enabled: true };
      chrome.tabs.query({}, function(tabs) {
        tabs.forEach(function(t) {
          if (t.url && t.url.startsWith('http')) {
            chrome.tabs.sendMessage(t.id, { action: 'applyNavInclud', settings: settings }).catch(function(){});
            chrome.tabs.reload(t.id);
          }
        });
      });
      setTimeout(function() { window.close(); }, 300);
    });
  };
});

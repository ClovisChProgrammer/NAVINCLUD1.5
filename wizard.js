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
let pendingFilterSettings = null;

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

  renderStep();

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
    pendingFilterSettings = null;
    if (progressFill) progressFill.style.width = '0%';
  }

  function renderStep() {
    if (currentStep >= PLATES.length) {
      clearInterval(timerInterval);
      showResults();
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

        if (String(opt) !== String(plate.correct)) {
          errors[plate.type]++;
        } else {
          correctCount++;
        }

        currentStep++;
        if (progressFill) progressFill.style.width = (currentStep / PLATES.length * 100) + '%';
        renderStep();
      };
      optionsContainer.appendChild(btn);
    });
  }

  function showResults() {
    document.getElementById('quiz-container').classList.remove('active');
    document.getElementById('results-screen').classList.add('active');

    var correctPercent = (correctCount / 18) * 100;

    if (errors.control > 0) {
      document.getElementById('result-text').innerHTML =
        '<p style="color:red; font-weight:bold;">ERRO DE CALIBRAÇÃO</p>' +
        '<p>Erro em placas de controle - calibração de monitor incorreta.</p>' +
        '<p>Por favor, recalibre seu monitor usando a página de calibração e refaça o teste.</p>';
      document.getElementById('apply-wizard').style.display = 'none';
      document.getElementById('negativo-close-btn').style.display = 'none';
      document.getElementById('recalibrate-btn').style.display = '';
      document.getElementById('retake-test-btn').style.display = '';
      return;
    }

    if (correctPercent >= 90) {
      document.getElementById('result-text').innerHTML =
        '<p style="color:green; font-size:20px; font-weight:bold;">✓ TESTE NEGATIVO</p>' +
        '<p>Você consegue discernir as cores muito bem. Seu teste não indicou nenhuma dificuldade significativa de visão de cores.</p>';
      document.getElementById('apply-wizard').style.display = 'none';
      document.getElementById('negativo-close-btn').style.display = '';
      document.getElementById('recalibrate-btn').style.display = 'none';
      document.getElementById('retake-test-btn').style.display = 'none';
      return;
    }

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

      var maliaErrors = errors[defectType + 'omaly'] || 0;
      var nopiaErrors = errors[defectType + nopiaSuffix] || 0;
      if (maliaErrors > 0 && nopiaErrors === 0) {
        filterType = defectType + 'omaly';
        intensity = 80; shift = 0.6;
      }

      document.getElementById('result-text').innerHTML =
        '<p style="color:#d55e00; font-size:20px; font-weight:bold;">TESTE POSITIVO</p>' +
        '<p>Foi identificada uma provável dificuldade em discernir determinadas cores, podendo ser classificado como provável <strong>' + filterType.toUpperCase() + '</strong>.</p>' +
        '<p>Ao clicar no botão abaixo, a extensão aplicará as configurações mais próximas do resultado do seu teste. A partir de agora, qualquer página que você abrir exibirá o filtro automaticamente. Você também pode fazer ajustes finos nos controles de "Intensidade" e "Ajuste de Shift" no popup da extensão.</p>';

      document.getElementById('apply-wizard').style.display = '';
      document.getElementById('apply-wizard').textContent = 'APLICAR FILTRO';
      document.getElementById('negativo-close-btn').style.display = 'none';
      document.getElementById('recalibrate-btn').style.display = 'none';
      document.getElementById('retake-test-btn').style.display = 'none';

      pendingFilterSettings = { type: filterType, intensity: intensity, shift: shift, enabled: true };
    } else {
      document.getElementById('result-text').innerHTML =
        '<p style="color:orange; font-weight:bold;">MÚLTIPLAS DEFICIÊNCIAS DETECTADAS</p>' +
        '<p>Foram detectados erros em múltiplos tipos de placas. Recomendamos recalibrar o monitor e refazer o teste para um resultado mais preciso.</p>';
      document.getElementById('apply-wizard').style.display = 'none';
      document.getElementById('negativo-close-btn').style.display = 'none';
      document.getElementById('recalibrate-btn').style.display = '';
      document.getElementById('retake-test-btn').style.display = '';
    }
  }

  document.getElementById('apply-wizard').onclick = function() {
    if (pendingFilterSettings) {
      chrome.storage.local.set({ navIncludSettings: pendingFilterSettings });
    }
    window.close();
  };

  document.getElementById('negativo-close-btn').onclick = function() {
    window.close();
  };

  document.getElementById('recalibrate-btn').onclick = function() {
    chrome.windows.create({ url: 'calibrate.html', type: 'popup', width: 800, height: 700 }, function() {
      chrome.windows.getCurrent(function(win) {
        if (win && win.id) { chrome.windows.remove(win.id); }
      });
    });
  };

  document.getElementById('retake-test-btn').onclick = function() {
    resetTestState();
    document.getElementById('results-screen').classList.remove('active');
    document.getElementById('quiz-container').classList.add('active');
    renderStep();
  };
});

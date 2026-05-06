function applyNavIncludFilter(settings) {
  const oldStyle = document.getElementById('navinclud-style');
  const oldSVG = document.getElementById('navinclud-svg');
  if (oldStyle) oldStyle.remove();
  if (oldSVG) oldSVG.remove();

  if (!settings || !settings.enabled || settings.type === 'none') {
    document.documentElement.style.filter = '';
    return;
  }

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.id = "navinclud-svg";
  svg.style.display = "none";
  
  const matrixValue = calculateMatrix(settings.type, settings.intensity / 100, settings.shift);
  
  svg.innerHTML = `
    <defs>
      <filter id="navinclud-filter" color-interpolation-filters="sRGB">
        <feColorMatrix type="matrix" values="${matrixValue}" />
      </filter>
    </defs>
  `;
  document.body.appendChild(svg);

  const style = document.createElement('style');
  style.id = 'navinclud-style';
  style.innerHTML = `html { filter: url(#navinclud-filter) !important; }`;
  document.head.appendChild(style);
}

function calculateMatrix(type, intensity, shift) {
  const base = {
    protanopia: [0.567, 0.433, 0, 0.558, 0.442, 0, 0, 0.242, 0.758],
    deuteranopia: [0.625, 0.375, 0, 0.7, 0.3, 0, 0, 0.3, 0.7],
    tritanopia: [0.95, 0.05, 0, 0, 0.433, 0.567, 0, 0.475, 0.525],
    achromatopsia: [0.299, 0.587, 0.114, 0.299, 0.587, 0.114, 0.299, 0.587, 0.114]
  };

  let b;
  if (type.includes('anomaly')) {
    let baseType = type.replace('anomaly', 'anopia');
    b = base[baseType] || [1,0,0,0,1,0,0,0,1];
    intensity *= 0.6;
  } else if (type === 'achromatomaly') {
    b = base.achromatopsia;
    intensity *= 0.6;
  } else {
    b = base[type] || [1,0,0,0,1,0,0,0,1];
  }

  const i = intensity;
  const n = 1 - i;
  const brightness = shift; // Shift agora é brilho adicionado (0 a 1)

  return [
    n + i*b[0], i*b[1], i*b[2], 0, brightness,
    i*b[3], n + i*b[4], i*b[5], 0, brightness,
    i*b[6], i*b[7], n + i*b[8], 0, brightness,
    0, 0, 0, 1, 0
  ].join(', ');
}

chrome.runtime.onMessage.addListener((m) => {
  if (m.action === 'applyNavInclud') applyNavIncludFilter(m.settings);
});

chrome.storage.local.get(['navIncludSettings'], (res) => {
  if (res.navIncludSettings?.enabled) applyNavIncludFilter(res.navIncludSettings);
});
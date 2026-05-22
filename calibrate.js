document.addEventListener('DOMContentLoaded', function() {
  var btn = document.getElementById('calibrate-next-btn');
  if (btn) {
    btn.addEventListener('click', function() {
      chrome.windows.create({ 
        url: 'wizard.html', 
        type: 'popup', 
        width: 420, 
        height: 600 
      }, function() {
        chrome.windows.getCurrent(function(win) {
          if (win && win.id) {
            chrome.windows.remove(win.id);
          }
        });
      });
    });
  }
});

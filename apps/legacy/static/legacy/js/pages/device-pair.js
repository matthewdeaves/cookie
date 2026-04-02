/* ES5 only — iOS 9 compatible */
/* global XMLHttpRequest, document, window */

var pollTimer = null;
var countdownTimer = null;

function getCsrfToken() {
  var value = '; ' + document.cookie;
  var parts = value.split('; csrftoken=');
  if (parts.length === 2) {
    return parts.pop().split(';').shift();
  }
  return '';
}

function showError(msg) {
  var el = document.getElementById('error-msg');
  el.textContent = msg;
  el.classList.remove('hidden');
}

function hideError() {
  document.getElementById('error-msg').classList.add('hidden');
}

function requestCode() {
  hideError();
  var btn = document.getElementById('pair-btn');
  btn.textContent = 'Requesting code...';
  btn.disabled = true;

  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/auth/device/code/');
  xhr.setRequestHeader('Content-Type', 'application/json');

  var csrf = getCsrfToken();
  if (csrf) {
    xhr.setRequestHeader('X-CSRFToken', csrf);
  }

  xhr.onload = function() {
    btn.textContent = 'Pair this device';
    btn.disabled = false;

    if (xhr.status === 201) {
      try {
        var data = JSON.parse(xhr.responseText);
        showCode(data.code, data.expires_in, data.poll_interval);
      } catch (e) {
        showError('Failed to process response');
      }
    } else {
      try {
        var errData = JSON.parse(xhr.responseText);
        showError(errData.error || 'Failed to get code');
      } catch (e) {
        showError('Failed to get code');
      }
    }
  };

  xhr.onerror = function() {
    btn.textContent = 'Pair this device';
    btn.disabled = false;
    showError('Network error. Please try again.');
  };

  xhr.send(null);
}

function showCode(code, expiresIn, pollInterval) {
  document.getElementById('request-section').classList.add('hidden');
  document.getElementById('code-display').classList.remove('hidden');
  document.getElementById('code-value').textContent = code;

  var expiresAt = Date.now() + (expiresIn * 1000);
  updateExpiry(expiresAt);

  // Countdown timer updates every second for smooth display
  if (countdownTimer) {
    clearInterval(countdownTimer);
  }
  countdownTimer = setInterval(function() {
    updateExpiry(expiresAt);
  }, 1000);

  // Poll timer fires at the server-specified interval
  if (pollTimer) {
    clearInterval(pollTimer);
  }
  pollTimer = setInterval(function() {
    pollStatus(expiresAt);
  }, (pollInterval || 5) * 1000);
}

function updateExpiry(expiresAt) {
  var remaining = Math.max(0, Math.floor((expiresAt - Date.now()) / 1000));
  var minutes = Math.floor(remaining / 60);
  var seconds = remaining % 60;
  var pad = seconds < 10 ? '0' : '';
  document.getElementById('expires-msg').textContent =
    'Expires in ' + minutes + ':' + pad + seconds;

  if (remaining <= 0) {
    onExpired();
  }
}

function pollStatus(expiresAt) {
  if (Date.now() >= expiresAt) {
    onExpired();
    return;
  }

  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/auth/device/poll/');

  xhr.onload = function() {
    if (xhr.status === 200) {
      // Authorized
      if (pollTimer) {
        clearInterval(pollTimer);
      }
      if (countdownTimer) {
        clearInterval(countdownTimer);
      }
      document.getElementById('status-msg').textContent = 'Paired! Redirecting...';
      window.location.href = '/legacy/home/';
    } else if (xhr.status === 410) {
      onExpired();
    }
    // 202 = still pending, keep polling
  };

  xhr.onerror = function() {
    // Network error, keep polling
  };

  xhr.send();
}

function onExpired() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
  document.getElementById('code-display').classList.add('hidden');
  document.getElementById('request-section').classList.remove('hidden');
  showError('Code expired. Please request a new one.');
}

// Attach click handler (CSP blocks inline onclick attributes)
var pairBtn = document.getElementById('pair-btn');
if (pairBtn) {
  pairBtn.addEventListener('click', requestCode);
}

/*
 * Real-time client for CitySolution.
 *
 * Opens one Server-Sent Events connection to /stream (see events.py and
 * the /stream route in app.py) and reacts to whatever arrives:
 *   - always: patch any element with a matching data-stat="..." attribute
 *     (overview numbers, stats-strip numbers) straight from the event's
 *     "stats" payload
 *   - always: on a "delete" event, fade out and remove any element
 *     tagged data-complaint-id="<id>" that's currently in the DOM
 *   - always: keep the small connection indicator (#live-indicator, if
 *     present) showing connected / reconnecting
 *   - finally: call window.onLiveEvent(data) if the current page defined
 *     one, so it can do page-specific things (dashboard.html and
 *     my_complaints.html fetch a freshly rendered fragment for the
 *     affected complaint and swap it in; complaint_detail.html reloads
 *     itself if the complaint it's showing changed).
 *
 * Nothing here duplicates server-side rendering logic - it only ever
 * asks the server for fresh HTML when something needs to change beyond
 * a plain text/number swap.
 */
(function () {
  function patchStats(stats) {
    if (!stats) return;
    Object.keys(stats).forEach(function (key) {
      var value = stats[key];
      if (value === null || typeof value === 'object') return; // skip lists like by_category
      document.querySelectorAll('[data-stat="' + key + '"]').forEach(function (el) {
        el.textContent = value;
      });
    });
  }

  function removeComplaintNodes(id) {
    document.querySelectorAll('[data-complaint-id="' + id + '"]').forEach(function (node) {
      node.classList.add('live-removing');
      setTimeout(function () {
        if (node.parentNode) node.parentNode.removeChild(node);
      }, 350);
    });
  }

  function bumpNewBanner() {
    var banner = document.getElementById('live-new-banner');
    if (!banner) return;
    var current = parseInt(banner.getAttribute('data-count') || '0', 10) + 1;
    banner.setAttribute('data-count', current);
    var countEl = banner.querySelector('[data-new-count]');
    if (countEl) countEl.textContent = current;
    banner.classList.add('visible');
  }

  function setLiveIndicator(state) {
    var el = document.getElementById('live-indicator');
    if (!el) return;
    el.className = 'live-indicator live-' + state;
    if (state === 'connected') el.textContent = '\u25CF Live';
    else if (state === 'connecting') el.textContent = '\u25CB Connecting\u2026';
    else el.textContent = '\u25CB Reconnecting\u2026';
  }

  function initNotifications() {
    var button = document.getElementById('notification-toggle');
    if (!button) return;

    var enabled = false;
    try {
      enabled = localStorage.getItem('citysolution-notifications') === 'enabled';
    } catch (e) {}
    enabled = enabled && 'Notification' in window && Notification.permission === 'granted';

    function updateButton() {
      var label = enabled
        ? 'Turn desktop alerts for new complaints and status updates off'
        : 'Enable desktop alerts for new complaints and status updates';
      button.setAttribute('aria-pressed', String(enabled));
      button.setAttribute('aria-label', label);
      button.title = label;
    }

    button.addEventListener('click', function () {
      if (!('Notification' in window)) {
        button.setAttribute('aria-label', 'Desktop alerts are unavailable in this browser');
        button.title = 'Desktop alerts are unavailable in this browser';
        return;
      }
      if (enabled) {
        enabled = false;
      } else if (Notification.permission === 'denied') {
        button.setAttribute('aria-label', 'Allow desktop alerts in browser settings');
        button.title = 'Allow desktop alerts in browser settings';
        return;
      } else if (Notification.permission === 'granted') {
        enabled = true;
      } else {
        Notification.requestPermission().then(function (permission) {
          enabled = permission === 'granted';
          updateButton();
          try { localStorage.setItem('citysolution-notifications', enabled ? 'enabled' : 'disabled'); } catch (e) {}
        });
        return;
      }
      updateButton();
      try { localStorage.setItem('citysolution-notifications', enabled ? 'enabled' : 'disabled'); } catch (e) {}
    });
    updateButton();
    return function () { return enabled; };
  }

  function showNotification(data, desktopEnabled) {
    if (!data.message || (data.type !== 'new_complaint' && data.type !== 'update')) return;
    var container = document.getElementById('live-notifications');
    if (container) {
      var toast = document.createElement(data.id ? 'a' : 'div');
      toast.className = 'live-toast';
      toast.textContent = data.message;
      if (data.id) toast.href = '/complaint/' + encodeURIComponent(data.id);
      container.appendChild(toast);
      window.setTimeout(function () {
        toast.classList.add('live-toast-dismissed');
        window.setTimeout(function () { toast.remove(); }, 250);
      }, 7000);
    }

    if (desktopEnabled && document.hidden) {
      var notification = new Notification(
        data.type === 'new_complaint' ? 'New civic complaint' : 'Complaint updated',
        { body: data.message, tag: 'citysolution-' + (data.id || data.type) }
      );
      notification.onclick = function () {
        window.focus();
        if (data.id) window.location.assign('/complaint/' + encodeURIComponent(data.id));
        notification.close();
      };
    }
  }

  function initEmailActions() {
    document.addEventListener('submit', async function (event) {
      var form = event.target.closest('form.dash-card-email');
      if (!form) return;
      event.preventDefault();

      var button = form.querySelector('button[type="submit"]');
      var card = form.closest('.dash-card');
      var feedback = card && card.querySelector('.dash-card-email-feedback');
      var resend = button.dataset.emailSent === 'true';
      if (resend && !window.confirm('A resolution email was already sent for this complaint. Send it again?')) return;

      button.disabled = true;
      button.setAttribute('aria-busy', 'true');
      if (feedback) {
        feedback.hidden = false;
        feedback.textContent = 'Sending email...';
      }

      async function sendEmail(allowResend) {
        var response = await fetch(form.action, {
          method: 'POST',
          credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
          body: JSON.stringify({ resend: allowResend })
        });
        var result;
        try { result = await response.json(); }
        catch (error) { result = {}; }
        return { response: response, result: result };
      }

      try {
        var outcome = await sendEmail(resend);
        if (outcome.response.status === 409 && outcome.result.requires_confirmation) {
          if (!window.confirm(outcome.result.error + ' Send again?')) {
            if (feedback) feedback.hidden = true;
            return;
          }
          outcome = await sendEmail(true);
        }
        if (!outcome.response.ok || !outcome.result.ok) {
          throw new Error(outcome.result.error || 'Failed to send email. Please check the email service configuration.');
        }
        button.dataset.emailSent = 'true';
        button.textContent = 'Email Sent ✓';
        button.title = 'Click to resend after confirmation';
        if (feedback) {
          feedback.hidden = false;
          feedback.textContent = outcome.result.message + (outcome.result.email_sent_at ? ' — ' + outcome.result.email_sent_at : '');
        }
      } catch (error) {
        if (feedback) {
          feedback.hidden = false;
          feedback.textContent = error.message || 'Failed to send email. Please check the email service configuration.';
        }
      } finally {
        button.disabled = false;
        button.removeAttribute('aria-busy');
      }
    });
  }

  function init() {
    initEmailActions();
    if (!window.EventSource) return; // very old browser - app still works, just without live updates
    setLiveIndicator('connecting');
    var desktopNotificationsEnabled = initNotifications() || function () { return false; };

    var source = new EventSource('/stream');
    source.onopen = function () { setLiveIndicator('connected'); };
    source.onerror = function () { setLiveIndicator('reconnecting'); };

    source.onmessage = function (evt) {
      var data;
      try {
        data = JSON.parse(evt.data);
      } catch (e) {
        return;
      }

      patchStats(data.stats);
      showNotification(data, desktopNotificationsEnabled());

      if (data.type === 'delete') {
        removeComplaintNodes(data.id);
      } else if (data.type === 'new_complaint') {
        bumpNewBanner();
      }

      if (typeof window.onLiveEvent === 'function') {
        window.onLiveEvent(data);
      }
    };
  }

  document.addEventListener('DOMContentLoaded', init);
})();

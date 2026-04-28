/**
 * Pull-to-refresh (ES5, iOS 9 compatible).
 *
 * Listens for vertical drags from the top of the page. When the page is
 * already scrolled to the top, dragging down past PULL_THRESHOLD reloads
 * the current page. Used by iOS standalone (Add to Home Screen) installs
 * where the system rubber-band doesn't trigger a real refresh.
 *
 * Safety:
 *   - aborts if the touch starts inside an input/textarea/[contenteditable]
 *   - aborts if any scrollable ancestor of the touch target has scrollTop>0
 *   - aborts on multi-touch
 *   - feature-detects passive listeners (iOS 9 doesn't support the options
 *     object — passing one would be parsed as useCapture=true)
 */
(function() {
    'use strict';

    if (!('ontouchstart' in window)) return;

    var PULL_THRESHOLD = 70;
    var ACTIVATION_DISTANCE = 10;
    var MAX_PULL = PULL_THRESHOLD * 1.6;

    var startY = null;
    var distance = 0;
    var pulling = false;
    var releasing = false;
    var indicator;
    var icon;

    // Feature-detect passive listeners (iOS 9.3 lacks support).
    var supportsPassive = false;
    try {
        var opts = Object.defineProperty({}, 'passive', {
            get: function() { supportsPassive = true; return false; }
        });
        window.addEventListener('test-passive', null, opts);
        window.removeEventListener('test-passive', null, opts);
    } catch (e) {}

    function isAtTop() {
        var sy = window.pageYOffset || document.documentElement.scrollTop || 0;
        return sy <= 0;
    }

    function hasScrolledScrollableAncestor(target) {
        var node = target;
        while (node && node !== document.body && node !== document.documentElement) {
            var style = window.getComputedStyle ? window.getComputedStyle(node) : node.currentStyle;
            if (style) {
                var overflowY = style.overflowY;
                if ((overflowY === 'auto' || overflowY === 'scroll') && node.scrollHeight > node.clientHeight) {
                    if (node.scrollTop > 0) return true;
                }
            }
            node = node.parentNode;
        }
        return false;
    }

    function ensureIndicator() {
        if (indicator) return;
        indicator = document.getElementById('ptr-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'ptr-indicator';
            indicator.className = 'ptr-indicator';
            indicator.setAttribute('aria-hidden', 'true');
            icon = document.createElement('div');
            icon.className = 'ptr-indicator-icon';
            indicator.appendChild(icon);
            document.body.appendChild(indicator);
        } else {
            icon = indicator.querySelector('.ptr-indicator-icon');
        }
    }

    function render() {
        ensureIndicator();
        if (!pulling && !releasing) {
            indicator.style.display = 'none';
            indicator.className = 'ptr-indicator';
            return;
        }
        indicator.style.display = 'flex';
        var translateY = releasing ? 24 : Math.min(distance * 0.6, 48);
        indicator.style.webkitTransform = 'translateY(' + translateY + 'px)';
        indicator.style.transform = 'translateY(' + translateY + 'px)';
        var ready = distance >= PULL_THRESHOLD;
        indicator.className = 'ptr-indicator' + (ready ? ' ptr-indicator-ready' : '') + (releasing ? ' ptr-indicator-releasing' : '');
        if (icon && !releasing) {
            var rot = Math.min(1, distance / PULL_THRESHOLD) * 270;
            icon.style.webkitTransform = 'rotate(' + rot + 'deg)';
            icon.style.transform = 'rotate(' + rot + 'deg)';
        }
    }

    function reset() {
        startY = null;
        distance = 0;
        pulling = false;
        render();
    }

    function onTouchStart(e) {
        if (releasing) return;
        if (!e.touches || e.touches.length !== 1) return;
        if (!isAtTop()) return;
        var target = e.target;
        if (!target) return;
        // closest is polyfilled in legacy/polyfills.js for iOS 9.
        if (target.closest && target.closest('input, textarea, select, [contenteditable="true"], [data-no-ptr]')) return;
        if (hasScrolledScrollableAncestor(target)) return;
        startY = e.touches[0].clientY;
    }

    function onTouchMove(e) {
        if (startY === null) return;
        if (!e.touches || e.touches.length !== 1) {
            reset();
            return;
        }
        var dy = e.touches[0].clientY - startY;
        if (dy <= 0) {
            reset();
            return;
        }
        if (dy < ACTIVATION_DISTANCE) return;
        if (e.cancelable) e.preventDefault();
        distance = Math.min(dy, MAX_PULL);
        pulling = true;
        render();
    }

    function onTouchEnd() {
        if (pulling && distance >= PULL_THRESHOLD) {
            releasing = true;
            render();
            // Brief frame for the user to see the spinner state before reload.
            setTimeout(function() { window.location.reload(); }, 80);
            return;
        }
        reset();
    }

    var moveOpts = supportsPassive ? { passive: false } : false;
    var passiveOpts = supportsPassive ? { passive: true } : false;

    document.addEventListener('touchstart', onTouchStart, passiveOpts);
    document.addEventListener('touchmove', onTouchMove, moveOpts);
    document.addEventListener('touchend', onTouchEnd, passiveOpts);
    document.addEventListener('touchcancel', reset, passiveOpts);
})();

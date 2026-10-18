/* Cookie Legacy - reload a page that was in the background for a few minutes (iPad locked and unlocked)
   so nobody has to hit refresh. Not while cooking (timers live in the page), typing, or with a dialog open. ES5. */
(function () {
    'use strict';
    var AWAY_MS = 3 * 60 * 1000;
    var hiddenAt = null;

    function busy() {
        if (document.querySelector('.play-mode')) { return true; }
        var a = document.activeElement;
        if (a && /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName)) { return true; }
        var m = document.querySelector('.modal-overlay');
        return !!(m && !/(^|\s)hidden(\s|$)/.test(m.className) && m.offsetHeight > 0);
    }

    document.addEventListener('visibilitychange', function () {
        if (document.hidden) { hiddenAt = new Date().getTime(); return; }
        var away = hiddenAt === null ? 0 : new Date().getTime() - hiddenAt;
        hiddenAt = null;
        if (away >= AWAY_MS && !busy()) { window.location.reload(); }
    });
})();

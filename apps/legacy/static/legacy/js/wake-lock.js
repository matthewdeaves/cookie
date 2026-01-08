/**
 * Wake Lock functionality (ES5, iOS 9 compatible)
 * Prevents screen from locking during Play Mode
 *
 * Uses different techniques based on iOS version:
 * - iOS 10+: Silent video loop (standard NoSleep.js approach)
 * - iOS 9 and below: Page refresh technique (triggers activity to prevent sleep)
 *
 * Based on NoSleep.js patterns: https://github.com/richtr/NoSleep.js
 */
var Cookie = Cookie || {};

Cookie.WakeLock = (function() {
    'use strict';

    var video = null;
    var enabled = false;
    var wantEnabled = false;
    var noSleepTimer = null;

    // Detect iOS version
    // Returns version number (e.g., 9.3) or false if not iOS
    function getIOSVersion() {
        var match = navigator.userAgent.match(/CPU.*OS ([0-9_]+)/i);
        if (match && match[1]) {
            return parseFloat(match[1].replace(/_/g, '.'));
        }
        // Check for "CPU like Mac OS" (some iOS variants)
        if (/CPU like.*AppleWebKit.*Mobile/i.test(navigator.userAgent)) {
            return 3.2; // Assume old iOS
        }
        return false;
    }

    var iosVersion = getIOSVersion();
    var isOldIOS = iosVersion !== false && iosVersion < 10;

    // Base64-encoded silent MP4 video for iOS 10+
    var SILENT_MP4 = 'data:video/mp4;base64,AAAAIGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1wNDEAAAAIZnJlZQAAA3NtZGF0AAACoAYF//+c3EXpvebZSLeWLNgg2SPu73gyNjQgLSBjb3JlIDE1NSByMjkwMSA3ZDBmZjIyIC0gSC4yNjQvTVBFRy00IEFWQyBjb2RlYyAtIENvcHlsZWZ0IDIwMDMtMjAxOCAtIGh0dHA6Ly93d3cudmlkZW9sYW4ub3JnL3gyNjQuaHRtbCAtIG9wdGlvbnM6IGNhYmFjPTEgcmVmPTMgZGVibG9jaz0xOjA6MCBhbmFseXNlPTB4MzoweDExMyBtZT1oZXggc3VibWU9NyBwc3k9MSBwc3lfcmQ9MS4wMDowLjAwIG1peGVkX3JlZj0xIG1lX3JhbmdlPTE2IGNocm9tYV9tZT0xIHRyZWxsaXM9MSA4eDhkY3Q9MSBjcW09MCBkZWFkem9uZT0yMSwxMSBmYXN0X3Bza2lwPTEgY2hyb21hX3FwX29mZnNldD0tMiB0aHJlYWRzPTMgbG9va2FoZWFkX3RocmVhZHM9MSBzbGljZWRfdGhyZWFkcz0wIG5yPTAgZGVjaW1hdGU9MSBpbnRlcmxhY2VkPTAgYmx1cmF5X2NvbXBhdD0wIGNvbnN0cmFpbmVkX2ludHJhPTAgYmZyYW1lcz0zIGJfcHlyYW1pZD0yIGJfYWRhcHQ9MSBiX2JpYXM9MCBkaXJlY3Q9MSB3ZWlnaHRiPTEgb3Blbl9nb3A9MCB3ZWlnaHRwPTIga2V5aW50PTI1MCBrZXlpbnRfbWluPTI1IHNjZW5lY3V0PTQwIGludHJhX3JlZnJlc2g9MCByY19sb29rYWhlYWQ9NDAgcmM9Y3JmIG1idHJlZT0xIGNyZj0yMy4wIHFjb21wPTAuNjAgcXBtaW49MCBxcG1heD02OSBxcHN0ZXA9NCBpcF9yYXRpbz0xLjQwIGFxPTE6MS4wMACAAAAAD2WIhAA3//728P4FNjuZQQAAAu5tb292AAAAbG12aGQAAAAAAAAAAAAAAAAAAAPoAAAAZAABAAABAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAACGHRyYWsAAABcdGtoZAAAAAMAAAAAAAAAAAAAAAEAAAAAAAAAZAAAAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAEAAAAAAAgAAAAIAAAAAACRlZHRzAAAAHGVsc3QAAAAAAAAAAQAAAGQAAAAAAAEAAAAAAZBtZGlhAAAAIG1kaGQAAAAAAAAAAAAAAAAAACgAAAAEAFXEAAAAAAAtaGRscgAAAAAAAAAAdmlkZQAAAAAAAAAAAAAAAFZpZGVvSGFuZGxlcgAAAAE7bWluZgAAABR2bWhkAAAAAQAAAAAAAAAAAAAAJGRpbmYAAAAcZHJlZgAAAAAAAAABAAAADHVybCAAAAABAAAA+3N0YmwAAACXc3RzZAAAAAAAAAABAAAAh2F2YzEAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAACAAIABEgAAABIAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY//8AAAAxYXZjQwFkAAr/4QAYZ2QACqzZX4iIhAAAAwAEAAADAFA8SJZYAQAGaOvjyyLAAAAAGHN0dHMAAAAAAAAAAQAAAAEAAAQAAAAAHHN0c2MAAAAAAAAAAQAAAAEAAAABAAAAAQAAABRzdHN6AAAAAAAAAsUAAAABAAAAFHN0Y28AAAAAAAAAAQAAADAAAABidWR0YQAAAFptZXRhAAAAAAAAACFoZGxyAAAAAAAAAABtZGlyYXBwbAAAAAAAAAAAAAAAAC1pbHN0AAAAJql0b28AAAAdZGF0YQAAAAEAAAAATGF2ZjU4LjI5LjEwMA==';

    /**
     * Create the video element for iOS 10+
     */
    function createVideo() {
        if (video) return video;

        video = document.createElement('video');
        video.setAttribute('playsinline', '');
        video.setAttribute('webkit-playsinline', '');
        video.setAttribute('muted', '');
        video.setAttribute('loop', '');
        video.muted = true;
        video.loop = true;

        // Style to hide the video
        video.style.position = 'absolute';
        video.style.left = '-9999px';
        video.style.top = '-9999px';
        video.style.width = '1px';
        video.style.height = '1px';
        video.style.opacity = '0.01';

        video.src = SILENT_MP4;
        document.body.appendChild(video);

        return video;
    }

    /**
     * Start the page refresh technique for iOS 9
     * This triggers a fake navigation every 15 seconds to prevent sleep
     */
    function startOldIOSTechnique() {
        if (noSleepTimer) return;

        noSleepTimer = window.setInterval(function() {
            if (!document.hidden) {
                // Trigger a fake page navigation and immediately stop it
                // This creates enough activity to prevent screen sleep
                window.location.href = window.location.href.split('#')[0];
                window.setTimeout(window.stop, 0);
            }
        }, 15000); // Every 15 seconds

        enabled = true;
    }

    /**
     * Stop the page refresh technique
     */
    function stopOldIOSTechnique() {
        if (noSleepTimer) {
            window.clearInterval(noSleepTimer);
            noSleepTimer = null;
        }
        enabled = false;
    }

    /**
     * Enable wake lock (marks that we want it enabled)
     * For iOS 9, this starts immediately (no user gesture needed for the timer)
     * For iOS 10+, the actual video.play() happens on unlock() from user gesture
     */
    function enable() {
        wantEnabled = true;

        if (isOldIOS) {
            // iOS 9: Use page refresh technique (works without user gesture)
            startOldIOSTechnique();
        } else {
            // iOS 10+ / other browsers: Create video for later
            createVideo();
        }
    }

    /**
     * Unlock and start the video - MUST be called from user gesture
     * (touchstart/click handler) on iOS 10+
     * For iOS 9, this is a no-op since the timer technique doesn't need it
     */
    function unlock() {
        if (!wantEnabled) return;

        if (isOldIOS) {
            // iOS 9: Timer already running from enable(), nothing to do
            return;
        }

        if (!video || enabled) return;

        try {
            var playPromise = video.play();

            if (playPromise !== undefined) {
                playPromise.then(function() {
                    enabled = true;
                }).catch(function() {
                    enabled = false;
                });
            } else {
                enabled = true;
            }
        } catch (e) {
            enabled = false;
        }
    }

    /**
     * Disable wake lock (allow screen to sleep normally)
     */
    function disable() {
        wantEnabled = false;

        if (isOldIOS) {
            stopOldIOSTechnique();
        } else {
            if (video) {
                try {
                    video.pause();
                } catch (e) {
                    // Silent fail
                }
            }
            enabled = false;
        }
    }

    /**
     * Check if wake lock is currently enabled
     */
    function isEnabled() {
        return enabled;
    }

    /**
     * Clean up resources
     */
    function destroy() {
        disable();
        if (video && video.parentNode) {
            video.parentNode.removeChild(video);
        }
        video = null;
    }

    // Public API
    return {
        enable: enable,
        unlock: unlock,
        disable: disable,
        isEnabled: isEnabled,
        destroy: destroy,
        // Expose for debugging
        _isOldIOS: isOldIOS,
        _iosVersion: iosVersion
    };
})();

/**
 * SentinelAI — Behavioral Fingerprinting SDK
 * Owner: Debarshi
 *
 * Drop this into any auth form to silently collect behavioral signals.
 * The collected data is attached as a hidden payload to form submissions.
 *
 * Usage:
 *   import { startTracking, getPayload } from './sdk/behavioral';
 *   startTracking();                      // Call when form mounts
 *   const payload = getPayload();         // Call just before form submit
 */

let trackingState = {
  startTime: null,
  keypressTimestamps: [],
  mouseMoveCount: 0,
  keypressCount: 0,
  isTracking: false,
};

/**
 * Start collecting behavioral signals.
 * Call this when the form component mounts.
 */
export function startTracking() {
  if (trackingState.isTracking) return;

  trackingState = {
    startTime: Date.now(),
    keypressTimestamps: [],
    mouseMoveCount: 0,
    keypressCount: 0,
    isTracking: true,
  };

  document.addEventListener("keydown", _onKeydown);
  document.addEventListener("mousemove", _onMouseMove);
}

/**
 * Stop collecting and clean up listeners.
 * Call this when the form unmounts.
 */
export function stopTracking() {
  document.removeEventListener("keydown", _onKeydown);
  document.removeEventListener("mousemove", _onMouseMove);
  trackingState.isTracking = false;
}

/**
 * Get the collected behavioral payload ready to send to the backend.
 * Call this just before submitting the form.
 *
 * @returns {Object} behavioral payload
 */
export function getPayload() {
  const now = Date.now();
  const timeToComplete = trackingState.startTime
    ? (now - trackingState.startTime) / 1000
    : 0;

  const typingVariance = _computeVariance(trackingState.keypressTimestamps);

  return {
    typing_variance_ms: Math.round(typingVariance),
    time_to_complete_sec: parseFloat(timeToComplete.toFixed(2)),
    mouse_move_count: trackingState.mouseMoveCount,
    keypress_count: trackingState.keypressCount,
  };
}

// --- Internal handlers ---

function _onKeydown(e) {
  const now = Date.now();
  trackingState.keypressTimestamps.push(now);
  trackingState.keypressCount++;
}

function _onMouseMove() {
  // Throttle — only count moves every 100ms to avoid huge numbers
  const now = Date.now();
  if (!_onMouseMove._last || now - _onMouseMove._last > 100) {
    trackingState.mouseMoveCount++;
    _onMouseMove._last = now;
  }
}

/**
 * Compute standard deviation of inter-keypress intervals.
 * High variance = human. Low variance = bot.
 */
function _computeVariance(timestamps) {
  if (timestamps.length < 3) return 0;

  const intervals = [];
  for (let i = 1; i < timestamps.length; i++) {
    intervals.push(timestamps[i] - timestamps[i - 1]);
  }

  const mean = intervals.reduce((a, b) => a + b, 0) / intervals.length;
  const squaredDiffs = intervals.map((v) => Math.pow(v - mean, 2));
  const variance = squaredDiffs.reduce((a, b) => a + b, 0) / squaredDiffs.length;
  return Math.sqrt(variance); // standard deviation in ms
}

/**
 * React hook version for easy use in React components.
 *
 * Usage in a component:
 *   const getPayload = useBehavioral();
 *   // then on submit: const behavioral = getPayload();
 */
export function useBehavioral() {
  // Import React at the top of your component file
  // This function returns getPayload bound to the tracking session

  if (typeof window !== "undefined") {
    startTracking();
  }

  return getPayload;
}

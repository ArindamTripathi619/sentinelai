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
  interactionTimestamps: [],
  mousePositions: [],
  focusSequence: [],
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
    interactionTimestamps: [],
    mousePositions: [],
    focusSequence: [],
    mouseMoveCount: 0,
    keypressCount: 0,
    isTracking: true,
  };

  document.addEventListener("keydown", _onKeydown);
  document.addEventListener("mousemove", _onMouseMove);
  document.addEventListener("focusin", _onFocusIn);
}

/**
 * Stop collecting and clean up listeners.
 * Call this when the form unmounts.
 */
export function stopTracking() {
  document.removeEventListener("keydown", _onKeydown);
  document.removeEventListener("mousemove", _onMouseMove);
  document.removeEventListener("focusin", _onFocusIn);
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
  const sessionTempo = _computeSessionTempo(trackingState.interactionTimestamps);
  const mouseEntropy = _computeMouseEntropy(trackingState.mousePositions);
  const fillOrderScore = _computeFillOrderScore(trackingState.focusSequence);

  return {
    typing_variance_ms: Math.round(typingVariance),
    time_to_complete_sec: parseFloat(timeToComplete.toFixed(2)),
    session_tempo_sec: parseFloat(sessionTempo.toFixed(2)),
    mouse_entropy_score: parseFloat(mouseEntropy.toFixed(2)),
    fill_order_score: parseFloat(fillOrderScore.toFixed(2)),
    mouse_move_count: trackingState.mouseMoveCount,
    keypress_count: trackingState.keypressCount,
  };
}

// --- Internal handlers ---

function _onKeydown(e) {
  const now = Date.now();
  trackingState.keypressTimestamps.push(now);
  trackingState.interactionTimestamps.push(now);
  trackingState.keypressCount++;
}

function _onMouseMove(e) {
  // Throttle — only count moves every 100ms to avoid huge numbers
  const now = Date.now();
  if (!_onMouseMove._last || now - _onMouseMove._last > 100) {
    trackingState.mouseMoveCount++;
    _onMouseMove._last = now;
    trackingState.interactionTimestamps.push(now);
    trackingState.mousePositions.push({ x: e?.clientX ?? 0, y: e?.clientY ?? 0 });
  }
}

function _onFocusIn(e) {
  const now = Date.now();
  trackingState.interactionTimestamps.push(now);
  const target = e?.target;
  const fieldId = target?.name || target?.id || target?.type || target?.tagName || "unknown";
  trackingState.focusSequence.push(String(fieldId).toLowerCase());
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

function _computeSessionTempo(timestamps) {
  if (timestamps.length < 3) return 0;

  const intervals = [];
  for (let i = 1; i < timestamps.length; i++) {
    intervals.push(timestamps[i] - timestamps[i - 1]);
  }

  return intervals.reduce((a, b) => a + b, 0) / intervals.length / 1000;
}

function _computeMouseEntropy(positions) {
  if (positions.length < 4) return 0;

  const buckets = { up: 0, down: 0, left: 0, right: 0 };
  for (let i = 1; i < positions.length; i++) {
    const dx = positions[i].x - positions[i - 1].x;
    const dy = positions[i].y - positions[i - 1].y;
    if (Math.abs(dx) >= Math.abs(dy)) {
      buckets[dx >= 0 ? "right" : "left"]++;
    } else {
      buckets[dy >= 0 ? "down" : "up"]++;
    }
  }

  const counts = Object.values(buckets).filter((count) => count > 0);
  const total = counts.reduce((a, b) => a + b, 0);
  if (!total) return 0;

  const entropy = -counts.reduce((sum, count) => {
    const p = count / total;
    return sum + p * Math.log2(p);
  }, 0);

  return Math.min(1, entropy / 2);
}

function _computeFillOrderScore(sequence) {
  if (sequence.length < 2) return 1;

  const uniqueFields = new Set(sequence);
  const transitions = sequence.length - 1;
  const repeatedTransitions = sequence.filter((field, index) => index > 0 && field === sequence[index - 1]).length;
  const orderScore = (uniqueFields.size / sequence.length) * (1 - repeatedTransitions / Math.max(1, transitions));
  return Math.max(0, Math.min(1, orderScore));
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

// =============================================================================
// Jest Setup - BruceWayneV1 Frontend
// Global mocks and polyfills for the test environment
// =============================================================================

require("@testing-library/jest-dom");

// ---------------------------------------------------------------------------
// Mock window.matchMedia
// ---------------------------------------------------------------------------
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// ---------------------------------------------------------------------------
// Mock IntersectionObserver
// ---------------------------------------------------------------------------
class MockIntersectionObserver {
  constructor(callback) {
    this.callback = callback;
    this.observations = [];
  }
  observe(element) {
    this.observations.push(element);
  }
  unobserve() {}
  disconnect() {}
}

Object.defineProperty(window, "IntersectionObserver", {
  writable: true,
  value: MockIntersectionObserver,
});

// ---------------------------------------------------------------------------
// Mock fetch
// ---------------------------------------------------------------------------
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(""),
    blob: () => Promise.resolve(new Blob()),
    headers: new Headers(),
  })
);

// ---------------------------------------------------------------------------
// Mock SpeechRecognition
// ---------------------------------------------------------------------------
class MockSpeechRecognition {
  constructor() {
    this.continuous = false;
    this.interimResults = false;
    this.lang = "en-US";
    this.onresult = null;
    this.onerror = null;
    this.onend = null;
    this.onstart = null;
  }
  start() {
    if (this.onstart) this.onstart(new Event("start"));
  }
  stop() {
    if (this.onend) this.onend(new Event("end"));
  }
  abort() {
    if (this.onend) this.onend(new Event("end"));
  }
}

Object.defineProperty(window, "SpeechRecognition", {
  writable: true,
  value: MockSpeechRecognition,
});

Object.defineProperty(window, "webkitSpeechRecognition", {
  writable: true,
  value: MockSpeechRecognition,
});

// ---------------------------------------------------------------------------
// Mock SpeechSynthesis
// ---------------------------------------------------------------------------
Object.defineProperty(window, "speechSynthesis", {
  writable: true,
  value: {
    speak: jest.fn(),
    cancel: jest.fn(),
    pause: jest.fn(),
    resume: jest.fn(),
    getVoices: jest.fn(() => []),
    speaking: false,
    paused: false,
    pending: false,
    onvoiceschanged: null,
  },
});

Object.defineProperty(window, "SpeechSynthesisUtterance", {
  writable: true,
  value: jest.fn().mockImplementation((text) => ({
    text,
    lang: "en-US",
    voice: null,
    volume: 1,
    rate: 1,
    pitch: 1,
    onend: null,
    onerror: null,
  })),
});

// ---------------------------------------------------------------------------
// Suppress specific console warnings in tests
// ---------------------------------------------------------------------------
const originalConsoleError = console.error;
console.error = (...args) => {
  if (
    typeof args[0] === "string" &&
    args[0].includes("Warning: ReactDOM.render is no longer supported")
  ) {
    return;
  }
  originalConsoleError.call(console, ...args);
};

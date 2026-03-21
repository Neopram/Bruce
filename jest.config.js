// =============================================================================
// Jest Configuration - BruceWayneV1 Frontend
// =============================================================================

const nextJest = require("next/jest");

const createJestConfig = nextJest({
  dir: "./",
});

/** @type {import('jest').Config} */
const customJestConfig = {
  testEnvironment: "jsdom",

  setupFilesAfterSetup: ["<rootDir>/jest.setup.js"],

  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
    "^@components/(.*)$": "<rootDir>/src/components/$1",
    "^@hooks/(.*)$": "<rootDir>/src/hooks/$1",
    "^@utils/(.*)$": "<rootDir>/src/utils/$1",
    "^@styles/(.*)$": "<rootDir>/src/styles/$1",
    // Handle CSS/SCSS modules
    "\\.(css|less|scss|sass)$": "identity-obj-proxy",
    // Handle image imports
    "\\.(jpg|jpeg|png|gif|svg)$": "<rootDir>/__mocks__/fileMock.js",
  },

  testMatch: [
    "<rootDir>/__tests__/**/*.{test,spec}.{ts,tsx,js,jsx}",
    "<rootDir>/src/**/*.{test,spec}.{ts,tsx,js,jsx}",
  ],

  collectCoverageFrom: [
    "src/**/*.{ts,tsx}",
    "!src/**/*.d.ts",
    "!src/**/index.ts",
    "!src/**/*.stories.{ts,tsx}",
  ],

  coverageThresholds: {
    global: {
      branches: 60,
      functions: 60,
      lines: 70,
      statements: 70,
    },
  },

  transformIgnorePatterns: ["/node_modules/(?!(@testing-library)/)"],
};

module.exports = createJestConfig(customJestConfig);

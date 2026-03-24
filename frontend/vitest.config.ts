import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './src/test/setup.ts',
      css: true,
      coverage: {
        provider: 'v8',
        reporter: ['text', 'json', 'json-summary', 'lcov', 'html'],
        reportsDirectory: './coverage',
        include: ['src/**/*.{ts,tsx}'],
        exclude: [
          'src/test/**',
          'src/**/*.d.ts',
          'src/main.tsx',
          'src/vite-env.d.ts'
        ],
        thresholds: {
          lines: 75,
          functions: 75,
          branches: 75,
          statements: 75,
        },
      },
    },
  })
)

// ESLint 9 flat config.
//
// The repo previously had NO eslint config and no eslint dependency, so
// `npm run lint` died with `sh: 1: eslint: not found` (exit 127) — the lint
// step was decorative and could never have caught anything. This makes it real.
import js from '@eslint/js'
import tseslint from '@typescript-eslint/eslint-plugin'
import tsparser from '@typescript-eslint/parser'
import reactHooks from 'eslint-plugin-react-hooks'
import globals from 'globals'

export default [
  { ignores: ['dist/**', 'node_modules/**', 'dev-dist/**', 'coverage/**'] },
  js.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsparser,
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: { ...globals.browser, ...globals.es2021 },
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    // The codebase already carries `// eslint-disable-next-line react-hooks/...`
    // comments, so the plugin must be registered or ESLint errors with
    // "Definition for rule ... was not found" on those lines.
    plugins: { '@typescript-eslint': tseslint, 'react-hooks': reactHooks },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      // TS already catches undefined identifiers; the base rule false-positives
      // on type-only references and JSX pragmas.
      'no-undef': 'off',
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
      // Deliberate `any` at API / Chart.js boundaries where payloads are dynamic.
      '@typescript-eslint/no-explicit-any': 'off',
      'no-empty': ['error', { allowEmptyCatch: true }],
      'prefer-const': 'warn',
    },
  },
]

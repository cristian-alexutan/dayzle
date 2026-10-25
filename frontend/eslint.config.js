import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import boundaries from 'eslint-plugin-boundaries'
import pluginVue from 'eslint-plugin-vue'

export default defineConfigWithVueTs(
  {
    name: 'app/files-to-lint',
    files: ['**/*.{ts,mts,tsx,vue}'],
  },
  {
    name: 'app/files-to-ignore',
    ignores: ['**/dist/**', '**/coverage/**', 'src/api/generated/**'],
  },

  pluginVue.configs['flat/essential'],
  vueTsConfigs.recommended,

  {
    name: 'app/vue-overrides',
    rules: {
      // Timer is a component name from the agreed design; it does not clash with an HTML element.
      'vue/multi-word-component-names': ['error', { ignores: ['Timer'] }],
    },
  },

  // Architecture rules. See CONTRIBUTING.md.
  {
    name: 'app/boundaries',
    files: ['src/**/*.{ts,vue}'],
    plugins: { boundaries },
    settings: {
      'import/resolver': {
        typescript: { project: './tsconfig.app.json' },
      },
      'boundaries/elements': [
        { type: 'app', pattern: 'src/app' },
        { type: 'api', pattern: 'src/api' },
        { type: 'shared', pattern: 'src/shared' },
        { type: 'feature', pattern: 'src/features/*', capture: ['featureName'] },
        { type: 'locales', pattern: 'src/locales' },
        { type: 'tests', pattern: 'src/tests' },
      ],
    },
    rules: {
      // Imports inside the same element (e.g. within one feature) are not checked.
      'boundaries/dependencies': [
        'error',
        {
          default: 'disallow',
          message:
            'Architecture violation: features never import other features, shared code never imports features, and code outside a feature imports only its index.ts.',
          policies: [
            {
              from: { element: { type: 'app' } },
              allow: [
                { to: { element: { types: ['api', 'shared', 'locales'] } } },
                { to: { element: { type: 'feature', fileInternalPath: 'index.ts' } } },
              ],
            },
            {
              from: { element: { type: 'feature' } },
              allow: { to: { element: { types: ['api', 'shared', 'locales'] } } },
            },
            {
              from: { element: { type: 'shared' } },
              allow: { to: { element: { types: ['locales'] } } },
            },
            {
              from: { element: { type: 'tests' } },
              allow: { to: { element: { types: ['app', 'api', 'shared', 'feature', 'locales'] } } },
            },
          ],
        },
      ],
    },
  },

  // Components and views reach the backend only through their feature's api/ folder.
  {
    name: 'app/no-direct-backend-calls',
    files: ['src/features/*/components/**', 'src/features/*/views/**'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: ['@/api', '@/api/*'],
              message: "Use the feature's api/ folder (queries.ts) instead of src/api directly.",
            },
          ],
        },
      ],
    },
  },

  skipFormatting,
)

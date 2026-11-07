import { describe, expect, it } from 'vitest'

import AppButton from '@/shared/components/AppButton.vue'
import AppMessage from '@/shared/components/AppMessage.vue'
import { mountWithPlugins } from '@/tests/utils'

describe('DayzlePreset', () => {
  it("gives PrimeVue's tokens the app's colors", () => {
    mountWithPlugins(AppButton, { props: { label: 'x' } })

    const css = Array.from(document.head.querySelectorAll('style'))
      .map((style) => style.textContent)
      .join('')
    expect(css).toContain('--p-primary-color:var(--dz-primary)')
    expect(css).toContain('--p-text-color:var(--dz-text)')
  })

  it('makes error messages pink text without a background', () => {
    mountWithPlugins(AppMessage, { props: { severity: 'error' } })

    const css = Array.from(document.head.querySelectorAll('style'))
      .map((style) => style.textContent)
      .join('')
    expect(css).toContain('--p-message-error-color:var(--dz-accent-strong)')
    expect(css).toContain('--p-message-error-background:transparent')
  })
})

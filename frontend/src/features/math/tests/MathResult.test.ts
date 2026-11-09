import { flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import MathResult from '../components/MathResult.vue'
import type { MathGame } from '../types'

const exact: MathGame = {
  date: '2026-11-07',
  status: 'completed',
  target: 253,
  numbers: [1, 2, 2, 25, 50, 100],
  max_steps: 5,
  steps: [
    { left: 100, op: '*', right: 2, result: 200 },
    { left: 50, op: '+', right: 2, result: 52 },
    { left: 200, op: '+', right: 52, result: 252 },
    { left: 252, op: '+', right: 1, result: 253 },
  ],
  final_result: 253,
  distance: 0,
  operations: 4,
  solved: true,
  score: 1000,
  duration_ms: 65_000,
  solution: [
    { left: 100, op: '*', right: 2, result: 200 },
    { left: 50, op: '+', right: 2, result: 52 },
    { left: 200, op: '+', right: 52, result: 252 },
  ],
  min_operations: 3,
  difficulty: 'medium',
}

const close: MathGame = {
  ...exact,
  steps: [{ left: 100, op: '*', right: 2, result: 200 }],
  final_result: 200,
  distance: 53,
  operations: 1,
  solved: false,
  score: 0,
}

const dialog = () => document.querySelector('[role="dialog"]')
const text = (selector: string) =>
  dialog()?.querySelector(selector)?.textContent?.replace(/\s+/g, ' ').trim() ?? null

async function mountResult(game: MathGame) {
  const wrapper = mountWithPlugins(MathResult, {
    props: { game, visible: true },
    attachTo: document.body,
  })
  await flushPromises()
  return wrapper
}

afterEach(() => {
  document.body.innerHTML = ''
})

describe('MathResult', () => {
  it('celebrates an exact finish with the score, steps, difficulty and time', async () => {
    const wrapper = await mountResult(exact)

    expect(dialog()?.textContent).toContain('Ai nimerit 253!')
    expect(dialog()?.textContent).toContain('1000')
    expect(text('[data-test="score-out-of"]')).toBe('puncte din 1000')
    expect(text('[data-test="result-steps"]')).toBe('4 pași · minimul 3')
    expect(text('[data-test="result-difficulty"]')).toBe('Mediu')
    expect(dialog()?.textContent).toContain('1:05')
    wrapper.unmount()
  })

  it('says how far a close finish was from the target', async () => {
    const wrapper = await mountResult(close)

    expect(dialog()?.textContent).toContain('200 — la 53 de 253')
    expect(dialog()?.textContent).not.toContain('Ai nimerit')
    expect(text('[data-test="result-steps"]')).toBe('1 pas · minimul 3')
    wrapper.unmount()
  })

  it('shows a possible solution, in the symbols players write', async () => {
    const wrapper = await mountResult(close)

    const steps = [...dialog()!.querySelectorAll('[data-test="solution"] [data-test="step-text"]')]
    expect(steps.map((step) => step.textContent?.replace(/\s+/g, ' ').trim())).toEqual([
      '100 × 2 = 200',
      '50 + 2 = 52',
      '200 + 52 = 252',
    ])
    wrapper.unmount()
  })

  it('leaves out what the server did not send', async () => {
    const wrapper = await mountResult({ ...close, solution: null, difficulty: null })

    expect(dialog()?.querySelector('[data-test="solution"]')).toBeNull()
    expect(dialog()?.querySelector('[data-test="result-difficulty"]')).toBeNull()
    wrapper.unmount()
  })

  it('shows nothing while closed', async () => {
    const wrapper = mountWithPlugins(MathResult, {
      props: { game: exact, visible: false },
      attachTo: document.body,
    })
    await flushPromises()

    expect(dialog()).toBeNull()
    wrapper.unmount()
  })
})

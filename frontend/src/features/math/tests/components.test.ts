import { describe, expect, it } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import FloatingPi from '../components/FloatingPi.vue'
import GlitchOverlay from '../components/GlitchOverlay.vue'
import JugglingHands from '../components/JugglingHands.vue'
import MathTarget from '../components/MathTarget.vue'
import NumberTile from '../components/NumberTile.vue'
import OperatorPicker from '../components/OperatorPicker.vue'
import StepHistory from '../components/StepHistory.vue'

describe('MathTarget', () => {
  it('shows the target with its label', () => {
    const wrapper = mountWithPlugins(MathTarget, { props: { target: 253 } })

    expect(wrapper.attributes('aria-label')).toBe('Ținta: 253')
    expect(wrapper.text()).toContain('253')
  })
})

describe('NumberTile', () => {
  const starting = { id: 'n0', value: 25, computed: false }
  const computed = { id: 's0', value: 200, computed: true }

  it('shows a starting number without a badge', () => {
    const wrapper = mountWithPlugins(NumberTile, { props: { tile: starting } })

    expect(wrapper.text()).toBe('25')
    expect(wrapper.attributes('aria-label')).toBe('25')
    expect(wrapper.attributes('aria-pressed')).toBe('false')
  })

  it('marks a computed number as new, and says so to screen readers', () => {
    const wrapper = mountWithPlugins(NumberTile, { props: { tile: computed, selected: true } })

    expect(wrapper.text()).toContain('NOU')
    expect(wrapper.attributes('aria-label')).toBe('200, rezultat calculat, selectat')
    expect(wrapper.attributes('aria-pressed')).toBe('true')
    expect(wrapper.classes()).toContain('number-tile--selected')
  })

  it('shows a refused number', () => {
    const wrapper = mountWithPlugins(NumberTile, { props: { tile: starting, refused: true } })

    expect(wrapper.attributes('aria-label')).toBe('25, pas refuzat')
    expect(wrapper.classes()).toContain('number-tile--refused')
  })

  it('emits select when tapped, but not while disabled', async () => {
    const enabled = mountWithPlugins(NumberTile, { props: { tile: starting } })
    await enabled.trigger('click')
    expect(enabled.emitted('select')).toHaveLength(1)

    const disabled = mountWithPlugins(NumberTile, { props: { tile: starting, disabled: true } })
    await disabled.trigger('click')
    expect(disabled.emitted('select')).toBeUndefined()
  })
})

describe('OperatorPicker', () => {
  it('shows the four operators as players write them', () => {
    const wrapper = mountWithPlugins(OperatorPicker, { props: { selected: null } })

    expect(wrapper.findAll('button').map((button) => button.text())).toEqual(['+', '−', '×', '÷'])
    expect(wrapper.find('[data-test="operator-divide"]').attributes('aria-label')).toBe('Împărțire')
  })

  it('highlights the picked operator and emits the one tapped', async () => {
    const wrapper = mountWithPlugins(OperatorPicker, { props: { selected: '*' } })

    expect(wrapper.find('[data-test="operator-multiply"]').attributes('aria-pressed')).toBe('true')
    expect(wrapper.find('[data-test="operator-add"]').attributes('aria-pressed')).toBe('false')

    await wrapper.find('[data-test="operator-divide"]').trigger('click')
    expect(wrapper.emitted('choose')).toEqual([['/']])
  })
})

describe('StepHistory', () => {
  it('shows a hint before the first step', () => {
    const wrapper = mountWithPlugins(StepHistory, { props: { steps: [], maxSteps: 5 } })

    expect(wrapper.find('[data-test="history-count"]').text()).toBe('0 din 5 pași')
    expect(wrapper.find('[data-test="history-empty"]').text()).toContain('Încă niciun pas')
    expect(wrapper.find('ol').exists()).toBe(false)
  })

  it('lists the steps in order, with the symbols players write', () => {
    const steps = [
      { left: 100, op: '*', right: 2, result: 200 },
      { left: 50, op: '/', right: 2, result: 25 },
      { left: 200, op: '-', right: 25, result: 175 },
    ] as const

    const wrapper = mountWithPlugins(StepHistory, { props: { steps: [...steps], maxSteps: 5 } })

    expect(wrapper.find('[data-test="history-count"]').text()).toBe('3 din 5 pași')
    expect(
      wrapper.findAll('[data-test="step-text"]').map((item) => item.text().replace(/\s+/g, ' ')),
    ).toEqual(['100 × 2 = 200', '50 ÷ 2 = 25', '200 − 25 = 175'])
    expect(wrapper.find('[data-test="history-empty"]').exists()).toBe(false)
  })
})

describe('easter eggs', () => {
  it('juggling hands: two hands, the second one mirrored, hidden from screen readers', () => {
    const wrapper = mountWithPlugins(JugglingHands)

    const hands = wrapper.findAll('[data-test="hand"]')
    expect(hands).toHaveLength(2)
    expect(hands[1]!.classes()).toContain('juggling-hands__hand--right')
    expect(wrapper.attributes('aria-hidden')).toBe('true')
    expect(wrapper.attributes('style')).toContain('--egg-ms: 1600ms')
  })

  it('floating π: the symbol and its digits, hidden from screen readers', () => {
    const wrapper = mountWithPlugins(FloatingPi)

    expect(wrapper.find('[data-test="pi"]').text()).toBe('π')
    expect(wrapper.text()).toContain('3.14')
    expect(wrapper.attributes('aria-hidden')).toBe('true')
  })

  it('glitch: says the number was not found, in the player language', () => {
    const wrapper = mountWithPlugins(GlitchOverlay)

    expect(wrapper.find('[data-test="glitch-label"]').text()).toBe('404 · Număr negăsit')
    expect(wrapper.attributes('aria-hidden')).toBe('true')
  })

  it('operators juggle only while the egg plays', async () => {
    const wrapper = mountWithPlugins(OperatorPicker, { props: { selected: null } })
    expect(wrapper.classes()).not.toContain('operator-picker--juggling')

    await wrapper.setProps({ juggling: true })

    expect(wrapper.classes()).toContain('operator-picker--juggling')
  })
})

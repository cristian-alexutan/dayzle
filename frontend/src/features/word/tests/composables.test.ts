import { describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'

import { mountWithPlugins } from '@/tests/utils'

import { useGuessInput } from '../composables/useGuessInput'
import { useKeyboardState } from '../composables/useKeyboardState'

function mountInput(disabled = false) {
  const onSubmit = vi.fn()
  let input!: ReturnType<typeof useGuessInput>
  const wrapper = mountWithPlugins(
    defineComponent({
      setup() {
        input = useGuessInput({ length: 5, disabled: () => disabled, onSubmit })
        return () => h('div')
      },
    }),
  )
  return { input, onSubmit, wrapper }
}

function press(key: string, init: KeyboardEventInit = {}) {
  const event = new KeyboardEvent('keydown', { key, cancelable: true, ...init })
  window.dispatchEvent(event)
  return event
}

describe('useGuessInput', () => {
  it('types and deletes letters, stopping at the word length', () => {
    const { input, wrapper } = mountInput()

    for (const letter of 'carteee') input.addLetter(letter)
    expect(input.text.value).toBe('carte')
    expect(input.isComplete.value).toBe(true)

    input.removeLetter()
    expect(input.text.value).toBe('cart')
    wrapper.unmount()
  })

  it('accepts diacritics and turns the old cedilla forms into comma-below', () => {
    const { input, wrapper } = mountInput()

    for (const key of ['Ă', 'â', 'Î', 'ş', 'Ţ']) input.addLetter(key)

    expect(input.text.value).toBe('ăâîșț')
    wrapper.unmount()
  })

  it('works from the physical keyboard', () => {
    const { input, onSubmit, wrapper } = mountInput()

    press('c')
    press('A')
    press('x')
    press('Backspace')
    expect(input.text.value).toBe('ca')

    const enter = press('Enter')
    expect(onSubmit).toHaveBeenCalledTimes(1)
    expect(enter.defaultPrevented).toBe(true)
    wrapper.unmount()
  })

  it('ignores keys that are not letters of the alphabet and browser shortcuts', () => {
    const { input, wrapper } = mountInput()

    for (const key of ['1', 'ü', ' ', 'Shift', 'F5']) press(key)
    press('r', { ctrlKey: true })
    press('c', { metaKey: true })

    expect(input.text.value).toBe('')
    wrapper.unmount()
  })

  it('accepts letters typed with AltGr, which Windows reports as Ctrl+Alt', () => {
    const { input, wrapper } = mountInput()

    press('ș', { ctrlKey: true, altKey: true })

    expect(input.text.value).toBe('ș')
    wrapper.unmount()
  })

  it('ignores every key while disabled', () => {
    const { input, onSubmit, wrapper } = mountInput(true)

    press('c')
    press('Enter')

    expect(input.text.value).toBe('')
    expect(onSubmit).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('stops listening once unmounted', () => {
    const { input, wrapper } = mountInput()
    wrapper.unmount()

    press('c')

    expect(input.text.value).toBe('')
  })
})

describe('useKeyboardState', () => {
  it('keeps the best color of each letter: green over yellow over gray', () => {
    const colors = useKeyboardState([
      { word: 'arată', colors: ['absent', 'present', 'absent', 'absent', 'absent'] },
      { word: 'radar', colors: ['correct', 'absent', 'absent', 'present', 'absent'] },
    ])

    expect(colors.value).toMatchObject({ r: 'correct', a: 'present', t: 'absent', ă: 'absent' })
  })

  it('keeps diacritics as separate letters', () => {
    const colors = useKeyboardState([
      { word: 'câine', colors: ['absent', 'correct', 'absent', 'absent', 'absent'] },
    ])

    expect(colors.value.â).toBe('correct')
    expect(colors.value.a).toBeUndefined()
  })
})

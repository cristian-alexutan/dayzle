import { flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import HowToPlay from './HowToPlay.vue'

const sections = [
  { heading: 'Reguli', rules: [{ icon: 'pi pi-check', text: 'Ghicește cuvântul.' }] },
  { heading: 'Punctaj', rules: [{ icon: 'pi pi-star', text: 'Un indiciu costă 2 puncte.' }] },
]

afterEach(() => {
  localStorage.clear()
  document.body.innerHTML = ''
})

describe('HowToPlay', () => {
  it('opens the rules from the info button and closes them', async () => {
    const wrapper = mountWithPlugins(HowToPlay, {
      props: { sections, game: 'test', autoOpen: false },
      attachTo: document.body,
    })
    expect(document.body.querySelector('[data-test="how-to-play-rules"]')).toBeNull()

    await wrapper.find('[data-test="how-to-play"]').trigger('click')
    await flushPromises()

    const dialog = document.body.querySelector('[role="dialog"]')!
    expect(dialog.textContent).toContain('Cum se joacă')
    expect(dialog.textContent).toContain('Punctaj')
    expect(dialog.textContent).toContain('Un indiciu costă 2 puncte.')

    const close = document.body.querySelector<HTMLElement>('[data-test="how-to-play-close"]')!
    close.click()
    await flushPromises()
    expect(wrapper.emitted('update:visible')).toEqual([[true], [false]])
    wrapper.unmount()
  })

  it('opens by itself once, and remembers it per game', async () => {
    const first = mountWithPlugins(HowToPlay, {
      props: { sections, game: 'test' },
      attachTo: document.body,
    })
    await flushPromises()
    expect(first.emitted('update:visible')).toEqual([[true]])
    first.unmount()

    localStorage.setItem('dayzle.test.rulesSeen', 'yes')
    const seen = mountWithPlugins(HowToPlay, { props: { sections, game: 'test' } })
    const other = mountWithPlugins(HowToPlay, { props: { sections, game: 'other' } })
    await flushPromises()
    expect(seen.emitted('update:visible')).toBeUndefined()
    expect(other.emitted('update:visible')).toEqual([[true]])
  })

  it('waits until the game allows it, e.g. once it is known to be unfinished', async () => {
    const wrapper = mountWithPlugins(HowToPlay, {
      props: { sections, game: 'test', autoOpen: false },
    })
    await flushPromises()
    expect(wrapper.emitted('update:visible')).toBeUndefined()

    await wrapper.setProps({ autoOpen: true })
    expect(wrapper.emitted('update:visible')).toEqual([[true]])
  })
})

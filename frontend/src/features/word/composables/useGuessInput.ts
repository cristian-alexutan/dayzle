// useGuessInput: the letters being typed, from the on-screen and the physical keyboard.
import { computed, onBeforeUnmount, onMounted, ref, toValue, type MaybeRefOrGetter } from 'vue'

const ALPHABET = new Set('abcdefghijklmnopqrstuvwxyzăâîșț')

/** Lowercase a typed key, and turn the old cedilla ş/ţ some keyboards type into ș/ț. */
function normalizeLetter(key: string): string {
  return key.normalize('NFC').toLowerCase().replace('ş', 'ș').replace('ţ', 'ț')
}

interface GuessInputOptions {
  length: MaybeRefOrGetter<number>
  /** While true, every key is ignored: a guess is on its way or the game has ended. */
  disabled: MaybeRefOrGetter<boolean>
  onSubmit: () => void
}

export function useGuessInput({ length, disabled, onSubmit }: GuessInputOptions) {
  const letters = ref<string[]>([])
  const text = computed(() => letters.value.join(''))
  const isComplete = computed(() => letters.value.length === toValue(length))

  function addLetter(key: string) {
    const letter = normalizeLetter(key)
    if (toValue(disabled) || !ALPHABET.has(letter) || isComplete.value) return
    letters.value.push(letter)
  }

  function removeLetter() {
    if (!toValue(disabled)) letters.value.pop()
  }

  function submit() {
    if (!toValue(disabled)) onSubmit()
  }

  function clear() {
    letters.value = []
  }

  function onKeydown(event: KeyboardEvent) {
    // Keep browser shortcuts working, but not AltGr, which Windows reports as Ctrl+Alt.
    if (event.metaKey || (event.ctrlKey && !event.altKey)) return
    if (event.key === 'Enter') {
      // Otherwise Enter would also click the on-screen key that has the focus.
      event.preventDefault()
      submit()
    } else if (event.key === 'Backspace') {
      removeLetter()
    } else {
      addLetter(event.key)
    }
  }

  onMounted(() => window.addEventListener('keydown', onKeydown))
  onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

  return { letters, text, isComplete, addLetter, removeLetter, submit, clear }
}

import type { Answer, Question, TriviaGame } from '../types'

/** Five questions with ids 1-5; question n has choices n1-n4, and the correct one is n1. */
export const questions: Question[] = [1, 2, 3, 4, 5].map((id) => ({
  id,
  category: (['history', 'geography', 'science', 'culture', 'sports'] as const)[id - 1]!,
  text: `Question ${id}?`,
  choices: [1, 2, 3, 4].map((n) => ({ id: id * 10 + n, text: `Choice ${id}.${n}` })),
}))

export function answerTo(question: number, correct: boolean): Answer {
  const correctChoice = question * 10 + 1
  return {
    question,
    choice: correct ? correctChoice : correctChoice + 1,
    correct_choice: correctChoice,
    is_correct: correct,
  }
}

export function makeGame(overrides: Partial<TriviaGame> = {}): TriviaGame {
  return {
    date: '2026-11-11',
    status: 'in_progress',
    questions,
    answers: [],
    score: null,
    max_score: 5,
    solved: null,
    duration_ms: null,
    ...overrides,
  }
}

/** A finished quiz: the given answers right or wrong, in order. */
export function finishedGame(results: boolean[], durationMs = 83_000): TriviaGame {
  const score = results.filter(Boolean).length
  return makeGame({
    status: 'completed',
    answers: results.map((correct, index) => answerTo(index + 1, correct)),
    score,
    solved: score === 5,
    duration_ms: durationMs,
  })
}

export function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

export function errorResponse(status: number, code: string) {
  return jsonResponse(status, { error: { code, message: code, details: null } })
}

// Types of the GeoGuesser feature.
import type { components } from '@/api/generated/schema'

/**
 * The player's game. Only the current round's panorama is sent, never its coordinates: a
 * location appears in `results` once its round is guessed. `solved` and `duration_ms` stay null
 * until the fifth guess.
 */
export type GeoGame = components['schemas']['GeoGame']

/** A region the game can be played in. Its bounds limit the guess map. */
export type Region = components['schemas']['Region']

export type Bounds = components['schemas']['Bounds']

export type Point = components['schemas']['Point']

/** A guessed round: the player's point, the real one, the distance and the points. */
export type RoundResult = components['schemas']['RoundResult']

/** A guess as the player sends it: the round and a point on the map. The server scores it. */
export type GuessInput = components['schemas']['GeoGuessInput']

/** The day in the URL: `today` or a date such as `2026-11-08`. */
export type GameDay = string

/** A region's key, or undefined for the default region. */
export type RegionKey = string | undefined

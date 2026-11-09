// A stand-in for Google's Maps JavaScript API in tests: records what the game creates.
import { vi } from 'vitest'

import type { Point } from '../types'

type Listener = (event: unknown) => void

export class FakeMap {
  readonly listeners = new Map<string, Listener[]>()
  readonly fitBounds = vi.fn()
  readonly setZoom = vi.fn()
  zoom = 12

  constructor(
    readonly element: HTMLElement,
    readonly options: Record<string, unknown>,
  ) {
    fake.maps.push(this)
  }

  addListener(name: string, listener: Listener) {
    const listeners = this.listeners.get(name) ?? []
    this.listeners.set(name, [...listeners, listener])
    return {
      remove: () =>
        this.listeners.set(
          name,
          (this.listeners.get(name) ?? []).filter((other) => other !== listener),
        ),
    }
  }

  getZoom() {
    return this.zoom
  }

  /** What Google does when the player clicks the map at this point. */
  click({ lat, lng }: Point) {
    const event = { latLng: { lat: () => lat, lng: () => lng } }
    this.listeners.get('click')?.forEach((listener) => listener(event))
  }

  trigger(name: string) {
    this.listeners.get(name)?.forEach((listener) => listener(undefined))
  }
}

/** A marker, line or rectangle: on the map until setMap(null). */
export class FakeShape {
  map: unknown

  constructor(public options: Record<string, unknown>) {
    this.map = options.map ?? null
    fake.shapes.push(this)
  }

  setMap(map: unknown) {
    this.map = map
  }

  setPosition(position: Point) {
    this.options = { ...this.options, position }
  }
}

class FakeMarker extends FakeShape {
  readonly kind = 'marker'
}
class FakePolyline extends FakeShape {
  readonly kind = 'polyline'
}
class FakeRectangle extends FakeShape {
  readonly kind = 'rectangle'
}

class FakeLatLngBounds {
  readonly points: Point[] = []

  extend(point: Point) {
    this.points.push(point)
    return this
  }
}

export class FakePanorama {
  readonly setPano = vi.fn()
  readonly setPov = vi.fn()
  readonly setZoom = vi.fn()

  constructor(
    readonly element: HTMLElement,
    readonly options: Record<string, unknown>,
  ) {
    fake.panoramas.push(this)
  }
}

const libraries: Record<string, unknown> = {
  maps: { Map: FakeMap, Polyline: FakePolyline, Rectangle: FakeRectangle },
  marker: { Marker: FakeMarker },
  core: { LatLngBounds: FakeLatLngBounds, SymbolPath: { CIRCLE: 0 } },
  streetView: { StreetViewPanorama: FakePanorama },
}

export const fake = {
  maps: [] as FakeMap[],
  shapes: [] as FakeShape[],
  panoramas: [] as FakePanorama[],
  importLibrary: vi.fn(async (name: string) => libraries[name]),
}

/** The shapes of one kind still on a map. */
export function shapesOnMap(kind: 'marker' | 'polyline' | 'rectangle') {
  return fake.shapes.filter(
    (shape) => (shape as FakeShape & { kind: string }).kind === kind && shape.map !== null,
  )
}

/** Install the fake as `google` with a browser key configured. Undo with uninstallFakeGoogleMaps. */
export function installFakeGoogleMaps() {
  fake.maps.length = 0
  fake.shapes.length = 0
  fake.panoramas.length = 0
  fake.importLibrary.mockClear()
  fake.importLibrary.mockImplementation(async (name: string) => libraries[name])
  const google = { maps: { importLibrary: fake.importLibrary } }
  vi.stubGlobal('google', google)
  ;(window as { google?: unknown }).google = google
  vi.stubEnv('VITE_GOOGLE_MAPS_BROWSER_KEY', 'test-key')
}

export function uninstallFakeGoogleMaps() {
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
  delete (window as { google?: unknown }).google
}

/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_GOOGLE_CLIENT_ID: string
  /** Browser key for Street View in the GeoGuesser; Street View shows a message without it. */
  readonly VITE_GOOGLE_MAPS_BROWSER_KEY?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

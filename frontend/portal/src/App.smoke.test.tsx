/**
 * Smoke test — renders the full app tree.
 *
 * No assertions on specific UI; the test passes if (and only if):
 *   - All imports resolve (pages, components, data)
 *   - React renders without throwing
 *   - No runtime crash in the component tree
 *
 * When you add a new page/component, wire it into App.tsx and this test
 * validates it for free — no changes needed here.
 */

import { vi } from 'vitest'

// Leaflet uses browser APIs (canvas, requestAnimationFrame) not available in jsdom.
// These mocks replace only what the test environment can't provide; build output is unaffected.
vi.mock('leaflet', () => ({
  default: {
    Icon: { Default: { prototype: {}, mergeOptions: vi.fn() } },
    divIcon: vi.fn(() => ({})),
  },
}))

vi.mock('react-leaflet', () => ({
  MapContainer: () => null,
  TileLayer: () => null,
  Marker: () => null,
  Popup: () => null,
  useMap: () => ({ flyTo: vi.fn() }),
}))

import { render } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders without crashing', () => {
    const { container } = render(<App />)
    expect(container.firstChild).not.toBeNull()
  })
})

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

vi.mock('@vis.gl/react-google-maps', () => ({
  APIProvider: ({ children }: { children: React.ReactNode }) => children,
  Map: () => null,
  AdvancedMarker: () => null,
  InfoWindow: () => null,
  useMap: () => null,
}))

vi.mock('@googlemaps/markerclusterer', () => ({
  MarkerClusterer: vi.fn().mockImplementation(() => ({
    clearMarkers: vi.fn(),
    addMarkers: vi.fn(),
  })),
}))

import { render } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders without crashing', () => {
    const { container } = render(<App />)
    expect(container.firstChild).not.toBeNull()
  })
})

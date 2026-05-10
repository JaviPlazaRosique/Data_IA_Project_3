import { useEffect, useRef, useState } from 'react';
import { APIProvider, useMapsLibrary } from '@vis.gl/react-google-maps';
import { awaitConfig, getPlacesApiKey } from '../config';

interface CityAutocompleteProps {
  value: string | null;
  onSave: (name: string, lat: number, lng: number) => void;
  onClear: () => void;
}

function CityAutocompleteInner({ value, onSave, onClear }: CityAutocompleteProps) {
  const places = useMapsLibrary('places');
  const inputRef = useRef<HTMLInputElement>(null);
  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);
  const [draft, setDraft] = useState(value ?? '');
  const placeConfirmedRef = useRef(false);

  useEffect(() => {
    setDraft(value ?? '');
  }, [value]);

  useEffect(() => {
    if (!places || !inputRef.current) return;

    autocompleteRef.current = new places.Autocomplete(inputRef.current, {
      types: ['(cities)'],
      fields: ['formatted_address', 'geometry'],
    });

    const listener = autocompleteRef.current.addListener('place_changed', () => {
      const place = autocompleteRef.current!.getPlace();
      if (!place.geometry?.location || !place.formatted_address) return;
      placeConfirmedRef.current = true;
      const name = place.formatted_address;
      const lat = place.geometry.location.lat();
      const lng = place.geometry.location.lng();
      setDraft(name);
      onSave(name, lat, lng);
    });

    return () => {
      google.maps.event.removeListener(listener);
    };
  }, [places, onSave]);

  function handleBlur() {
    if (!placeConfirmedRef.current) {
      setDraft(value ?? '');
    }
    placeConfirmedRef.current = false;
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    placeConfirmedRef.current = false;
    setDraft(e.target.value);
  }

  function handleClear() {
    setDraft('');
    placeConfirmedRef.current = false;
    onClear();
  }

  return (
    <div className="bg-surface-container-lowest flex items-center gap-3 p-3 rounded-xl">
      <span className="material-symbols-outlined text-secondary">location_on</span>
      <input
        ref={inputRef}
        type="text"
        value={draft}
        onChange={handleChange}
        onBlur={handleBlur}
        placeholder="Ej. Madrid, Valencia (España)…"
        className="flex-1 bg-transparent text-sm font-medium focus:outline-none placeholder:text-on-surface-variant/40"
      />
      {draft && (
        <button
          onMouseDown={(e) => e.preventDefault()}
          onClick={handleClear}
          className="text-on-surface-variant/40 hover:text-on-surface-variant transition-colors"
        >
          <span className="material-symbols-outlined text-base">close</span>
        </button>
      )}
    </div>
  );
}

export default function CityAutocomplete(props: CityAutocompleteProps) {
  const [apiKey, setApiKey] = useState('');

  useEffect(() => {
    awaitConfig().then(() => setApiKey(getPlacesApiKey()));
  }, []);

  if (!apiKey) return null;

  return (
    <APIProvider apiKey={apiKey}>
      <CityAutocompleteInner {...props} />
    </APIProvider>
  );
}

// ############################################################################
// AI_HEADER: MODULE_GEO_FIELD
// ROLE: GeoNames autocomplete input with hidden coordinates.
// DEPENDENCIES: /api/geo/autocomplete, /api/geo/timezone.
// GRACE_ANCHORS: [GEO_STATE, GEO_LOOKUP]
// ############################################################################

"use client";

import { useEffect, useMemo, useState } from "react";

type GeoSuggestion = {
  id: string;
  name: string;
  admin1?: string | null;
  country?: string | null;
  lat: number;
  lon: number;
  label: string;
};

type GeoFieldProps = {
  namePrefix: string;
  label: string;
  placeholder?: string;
  required?: boolean;
  initialLabel?: string;
  initialLat?: number | null;
  initialLon?: number | null;
  initialPlaceId?: string | null;
  initialTimezone?: string | null;
};

export default function GeoField({
  namePrefix,
  label,
  placeholder,
  required,
  initialLabel,
  initialLat,
  initialLon,
  initialPlaceId,
  initialTimezone,
}: GeoFieldProps) {
  const [query, setQuery] = useState(initialLabel || "");
  const [selected, setSelected] = useState<GeoSuggestion | null>(
    initialLat != null && initialLon != null
      ? {
          id: initialPlaceId || "",
          name: initialLabel || "",
          admin1: null,
          country: null,
          lat: initialLat,
          lon: initialLon,
          label: initialLabel || "",
        }
      : null
  );
  const [suggestions, setSuggestions] = useState<GeoSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [geoError, setGeoError] = useState<string | null>(null);
  const [timezone, setTimezone] = useState(initialTimezone || "");
  const [tzError, setTzError] = useState<string | null>(null);
  const isSelectedQuery = Boolean(selected && selected.label === query);

  useEffect(() => {
    if (isSelectedQuery) {
      setSuggestions([]);
      setGeoError(null);
      return;
    }

    if (query.trim().length < 2) {
      setSuggestions([]);
      setGeoError(null);
      return;
    }

    const handle = window.setTimeout(async () => {
      setIsLoading(true);
      setGeoError(null);
      try {
        const response = await fetch(`/api/geo/autocomplete?q=${encodeURIComponent(query)}`, {
          cache: "no-store",
        });
        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          const message = payload?.detail || `Geo API: ${response.status}`;
          throw new Error(message);
        }
        const data = (await response.json()) as GeoSuggestion[];
        setSuggestions(data);
      } catch (error) {
        setGeoError(error instanceof Error ? error.message : "Geo API error");
        setSuggestions([]);
      } finally {
        setIsLoading(false);
      }
    }, 350);

    return () => window.clearTimeout(handle);
  }, [isSelectedQuery, query]);

  const showSuggestions = useMemo(
    () =>
      !isSelectedQuery &&
      query.trim().length >= 2 &&
      (suggestions.length > 0 || isLoading || geoError),
    [geoError, isLoading, isSelectedQuery, query, suggestions.length]
  );

  const handlePick = (item: GeoSuggestion) => {
    setSelected(item);
    setQuery(item.label);
    setSuggestions([]);
    setTimezone("");
    setTzError(null);
    void fetch(`/api/geo/timezone?lat=${encodeURIComponent(item.lat)}&lon=${encodeURIComponent(item.lon)}`, {
      cache: "no-store",
    })
      .then(async (response) => {
        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          const message = payload?.detail || `TZ API: ${response.status}`;
          throw new Error(message);
        }
        return response.json();
      })
      .then((data) => {
        const tz = typeof data?.timezone_id === "string" ? data.timezone_id : "";
        setTimezone(tz);
      })
      .catch((error) => {
        setTzError(error instanceof Error ? error.message : "TZ API error");
      });
  };

  return (
    <div className="field">
      <label className="label" htmlFor={`${namePrefix}_location`}>{label}</label>
      <input
        id={`${namePrefix}_location`}
        name={`${namePrefix}_location`}
        className="input"
        placeholder={placeholder}
        value={query}
        onChange={(event) => {
          setQuery(event.target.value);
          setSelected(null);
          setTimezone("");
          setTzError(null);
        }}
        autoComplete="off"
        required={required}
      />
      {showSuggestions ? (
        <div className="suggestions">
          {isLoading ? (
            <div className="suggestion muted">Поиск...</div>
          ) : null}
          {geoError ? (
            <div className="suggestion error">{geoError}</div>
          ) : null}
          {!isLoading && !geoError && suggestions.length === 0 ? (
            <div className="suggestion muted">Ничего не найдено</div>
          ) : null}
          {!geoError
            ? suggestions.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className="suggestion"
                  onClick={() => handlePick(item)}
                >
                  {item.label}
                </button>
              ))
            : null}
        </div>
      ) : null}
      {timezone ? (
        <div className="subtle text-xs">TZ: {timezone}</div>
      ) : null}
      {tzError ? (
        <div className="text-xs text-[var(--accent-3)]">{tzError}</div>
      ) : null}
      <input type="hidden" name={`${namePrefix}_lat`} value={selected?.lat ?? ""} />
      <input type="hidden" name={`${namePrefix}_lon`} value={selected?.lon ?? ""} />
      <input type="hidden" name={`${namePrefix}_place_id`} value={selected?.id ?? ""} />
      <input type="hidden" name={`${namePrefix}_timezone`} value={timezone} />
    </div>
  );
}

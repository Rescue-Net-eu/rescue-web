"use client";

// A dependency-free SVG mini-map. It plots points relative to a center using a
// simple local equirectangular projection — enough to visualize responder
// positions around an incident without a tile provider. A future increment can
// swap this for Leaflet/MapLibre with real basemap tiles.

export interface LatLng {
  lat: number;
  lng: number;
}

export function MiniMap({
  center,
  points = [],
  selfPoints = [],
  height = 240,
}: {
  center: LatLng;
  points?: LatLng[];
  selfPoints?: LatLng[];
  height?: number;
}) {
  const all = [center, ...points, ...selfPoints];

  // Meters-per-degree scaling so lat/lng look roughly proportional.
  const latScale = 111_320;
  const lngScale = 111_320 * Math.cos((center.lat * Math.PI) / 180);

  const xs = all.map((p) => (p.lng - center.lng) * lngScale);
  const ys = all.map((p) => (p.lat - center.lat) * latScale);
  const maxAbs = Math.max(1, ...xs.map(Math.abs), ...ys.map(Math.abs)) * 1.2;

  const W = 100;
  const H = 100;
  const project = (p: LatLng) => {
    const x = ((p.lng - center.lng) * lngScale) / maxAbs;
    const y = ((p.lat - center.lat) * latScale) / maxAbs;
    return { cx: W / 2 + (x * W) / 2, cy: H / 2 - (y * H) / 2 };
  };

  const c = project(center);

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      style={{
        width: "100%",
        height,
        background: "#eef2f5",
        border: "1px solid var(--border)",
        borderRadius: 8,
      }}
    >
      {/* grid */}
      {[25, 50, 75].map((g) => (
        <g key={g} stroke="#dde3e8" strokeWidth={0.3}>
          <line x1={g} y1={0} x2={g} y2={H} />
          <line x1={0} y1={g} x2={W} y2={g} />
        </g>
      ))}
      {/* incident center + radius ring */}
      <circle cx={c.cx} cy={c.cy} r={W / 2 - 2} fill="rgba(176,0,32,0.05)" stroke="rgba(176,0,32,0.3)" strokeWidth={0.4} strokeDasharray="2 1.5" />
      <circle cx={c.cx} cy={c.cy} r={2.2} fill="var(--brand)" />

      {/* responder candidate points */}
      {points.map((p, i) => {
        const { cx, cy } = project(p);
        return <circle key={`p${i}`} cx={cx} cy={cy} r={1.6} fill="#1f6feb" />;
      })}
      {/* live (self-reported) points */}
      {selfPoints.map((p, i) => {
        const { cx, cy } = project(p);
        return <circle key={`s${i}`} cx={cx} cy={cy} r={1.8} fill="var(--ok)" />;
      })}
    </svg>
  );
}

import { useMemo } from "react";
import {
  Eye,
  Layers,
  CheckCircle2,
  Loader2,
  HelpCircle,
  ExternalLink,
  LineChart,
} from "lucide-react";

/* ---------------------------------------------------------------------------
   THEME — lifted straight from your skin. One place to retune the look.
--------------------------------------------------------------------------- */
const C = {
  bg: "#0d0c11",
  card: "#16151d",
  panel: "#131219",
  groupHead: "#191822",
  hairline: "rgba(255,255,255,0.05)",
  ink: "#e7e7ec",
  inkDim: "#b8b8c2",
  mute: "#7c7c8c",
  mute2: "#6a6a78",
  mute3: "#56566a",
  mute4: "#5d5d6a",
  green: "#2dd4a7",
  amber: "#f0a93b",
  red: "#e5484d",
  grey: "#56566a",
  violet: "#9d7bf5",
};

const MONO = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace';

/* Status is the single source of truth. "unknown" reads grey on purpose —
   a missing signal is a different fact from a failure, and must never wear
   green or red. */
const STATUS = {
  healthy:  { color: C.green, glow: "rgba(45,212,167,0.6)",  deploy: "success",  badge: "HEALTHY" },
  building: { color: C.amber, glow: "rgba(240,169,59,0.5)",  deploy: "building", badge: "BUILDING" },
  down:     { color: C.red,   glow: "rgba(229,72,77,0.55)",  deploy: "failed",   badge: "DOWN" },
  unknown:  { color: C.grey,  glow: "transparent",           deploy: "unknown",  badge: "UNKNOWN" },
};

/* Rollup: worst child wins. Later in the list = more urgent. */
const SEVERITY = ["healthy", "unknown", "building", "down"];
const worst = (arr) =>
  arr.reduce((acc, s) => (SEVERITY.indexOf(s) > SEVERITY.indexOf(acc) ? s : acc), "healthy");

/* ------------------------------------------------------------------ atoms */
function Dot({ status, size = 7 }) {
  const s = STATUS[status] ?? STATUS.unknown;
  return (
    <span
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        background: s.color,
        boxShadow: s.glow === "transparent" ? "none" : `0 0 7px ${s.glow}`,
        flexShrink: 0,
      }}
    />
  );
}

function StatCard({ label, children, tone }) {
  const accent =
    tone === "green" ? C.green : tone === "amber" ? C.amber : null;
  return (
    <div
      style={{
        background: accent ? `${accent}12` : C.card,
        border: `1px solid ${accent ? `${accent}38` : C.hairline}`,
        borderRadius: 11,
        padding: "11px 12px",
      }}
    >
      <p style={{ fontSize: 10, letterSpacing: "0.12em", color: accent ?? C.mute4, margin: "0 0 7px" }}>
        {label}
      </p>
      {children}
    </div>
  );
}

/* --------------------------------------------------------------- service row */
function ServiceRow({ svc, onSelect }) {
  const s = STATUS[svc.status] ?? STATUS.unknown;
  return (
    <div
      className="vig-row"
      onClick={() => onSelect?.(svc)}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 11,
        padding: "12px 14px 12px 32px",
        borderTop: `1px solid rgba(255,255,255,0.04)`,
        cursor: "pointer",
        transition: "background .12s",
      }}
    >
      <Dot status={svc.status} />
      <span style={{ fontSize: 12, minWidth: 62 }}>{svc.name}</span>
      <span style={{ fontSize: 11, color: C.mute2 }}>
        {svc.source ? svc.source : `${svc.ref} · ${svc.branch}`}
      </span>
      <span style={{ fontSize: 11, color: s.color, marginLeft: "auto" }}>{s.deploy}</span>
      <span style={{ fontSize: 11, color: C.mute3, minWidth: 36, textAlign: "right" }}>{svc.age}</span>
      <ExternalLink size={13} color={C.violet} />
    </div>
  );
}

/* ------------------------------------------------------------ project group */
function ComponentGroup({ project, onSelect, first }) {
  // Project not found on Railway: a single honest grey row, no fake green.
  if (project.found === false) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 9,
          padding: "11px 14px",
          background: "#161520",
          borderTop: first ? "none" : `1px solid ${C.hairline}`,
        }}
      >
        <HelpCircle size={14} color={C.mute3} />
        <span style={{ fontSize: 12, fontWeight: 500, color: C.mute }}>{project.name}</span>
        <span style={{ fontSize: 10, color: C.mute3, marginLeft: "auto" }}>{project.note}</span>
      </div>
    );
  }

  const rollup = worst(project.services.map((s) => s.status));
  const badge = STATUS[rollup];

  return (
    <>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 9,
          padding: "9px 14px",
          background: C.groupHead,
          borderTop: first ? "none" : `1px solid ${C.hairline}`,
        }}
      >
        <Layers size={14} color={C.mute} />
        <span style={{ fontSize: 12, fontWeight: 500 }}>{project.name}</span>
        {project.domain && (
          <span style={{ fontSize: 10, color: C.mute2, marginLeft: 6 }}>{project.domain}</span>
        )}
        <span style={{ fontSize: 10, color: badge.color, marginLeft: "auto", letterSpacing: "0.04em" }}>
          {badge.badge}
        </span>
      </div>
      {project.services.map((svc) => (
        <ServiceRow key={svc.id} svc={svc} onSelect={onSelect} />
      ))}
    </>
  );
}

/* ------------------------------------------------------------- activity feed */
function ActivityFeed({ events }) {
  return (
    <div style={{ padding: "0 4px" }}>
      {events.map((e, i) => {
        const color = STATUS[e.status]?.color ?? C.grey;
        const last = i === events.length - 1;
        const dim = e.status === "healthy" && e.verb === "deployed" && last;
        return (
          <div key={e.id} style={{ display: "flex", gap: 12 }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", flexShrink: 0 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: color, marginTop: 3 }} />
              {!last && (
                <span style={{ width: 1.5, flex: 1, background: "rgba(255,255,255,0.07)", minHeight: 24 }} />
              )}
            </div>
            <div style={{ paddingBottom: last ? 0 : 13 }}>
              <p style={{ fontSize: 12, margin: 0, color: dim ? C.inkDim : C.ink }}>
                {e.target}{" "}
                <span style={{ color: dim ? C.mute : color }}>{e.verb}</span>
              </p>
              <p style={{ fontSize: 11, color: C.mute3, margin: "3px 0 0" }}>{e.meta}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ===================================================================== shell */
export default function Vigia({ data = SAMPLE, onSelectService }) {
  const stats = useMemo(() => {
    const found = data.projects.filter((p) => p.found !== false);
    const services = found.flatMap((p) => p.services);
    const previews = found.flatMap((p) => p.previews ?? []);
    const downCount = services.filter((s) => s.status === "down").length;
    const buildingPreviews = previews.filter((p) => p.status === "building").length;
    return {
      systems: data.projects.length,
      components: services.length,
      prodGreen: downCount === 0,
      downCount,
      buildingPreviews,
    };
  }, [data]);

  return (
    <div
      style={{
        background: C.bg,
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: 18,
        padding: "18px 18px 22px",
        fontFamily: MONO,
        color: C.ink,
        maxWidth: 560,
        margin: "0 auto",
      }}
    >
      <style>{`
        @keyframes vigpulse { 0%,100%{opacity:1} 50%{opacity:.35} }
        @keyframes vigspin { to { transform: rotate(360deg) } }
        .vig-row:hover { background:#1c1b24; }
        .vig-pulse { animation: vigpulse 2s ease-in-out infinite; }
        .vig-spin  { animation: vigspin 1s linear infinite; }
      `}</style>

      {/* header */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "2px 4px 16px", borderBottom: `1px solid ${C.hairline}` }}>
        <span style={{ width: 26, height: 26, borderRadius: 7, background: "linear-gradient(135deg,#9d7bf5,#6f54d6)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Eye size={15} color="#fff" />
        </span>
        <span style={{ fontSize: 14, fontWeight: 500, letterSpacing: "0.04em" }}>vigia</span>
        <span style={{ display: "flex", alignItems: "center", gap: 6, marginLeft: "auto", fontSize: 11, color: C.mute2 }}>
          <span className="vig-pulse" style={{ width: 7, height: 7, borderRadius: "50%", background: C.green }} />
          live · {data.refreshedAgo}
        </span>
      </div>

      {/* summary */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 9, margin: "16px 0 18px" }}>
        <StatCard label="SYSTEMS"><p style={{ fontSize: 22, fontWeight: 500, margin: 0 }}>{stats.systems}</p></StatCard>
        <StatCard label="COMPONENTS"><p style={{ fontSize: 22, fontWeight: 500, margin: 0 }}>{stats.components}</p></StatCard>
        <StatCard label="PRODUCTION" tone={stats.prodGreen ? "green" : undefined}>
          <p style={{ fontSize: 13, fontWeight: 500, margin: 0, color: stats.prodGreen ? C.green : C.red, display: "flex", alignItems: "center", gap: 5 }}>
            {stats.prodGreen ? <CheckCircle2 size={14} /> : null}
            {stats.prodGreen ? "all green" : `${stats.downCount} down`}
          </p>
        </StatCard>
        <StatCard label="PREVIEWS" tone={stats.buildingPreviews ? "amber" : undefined}>
          <p style={{ fontSize: 13, fontWeight: 500, margin: 0, color: stats.buildingPreviews ? C.amber : C.mute2, display: "flex", alignItems: "center", gap: 5 }}>
            {stats.buildingPreviews ? <Loader2 className="vig-spin" size={14} /> : null}
            {stats.buildingPreviews ? `${stats.buildingPreviews} building` : "idle"}
          </p>
        </StatCard>
      </div>

      {/* components */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", margin: "0 4px 9px" }}>
        <span style={{ fontSize: 10, letterSpacing: "0.16em", color: C.mute4 }}>COMPONENTS</span>
        <span style={{ fontSize: 10, letterSpacing: "0.06em", color: "#48485a" }}>production · previews collapsed</span>
      </div>
      <div style={{ background: C.panel, border: `1px solid ${C.hairline}`, borderRadius: 13, overflow: "hidden", margin: "0 0 20px" }}>
        {data.projects.map((p, i) => (
          <ComponentGroup key={p.id} project={p} first={i === 0} onSelect={onSelectService} />
        ))}
      </div>

      {/* activity */}
      <div style={{ margin: "0 4px 11px" }}>
        <span style={{ fontSize: 10, letterSpacing: "0.16em", color: C.mute4 }}>RECENT ACTIVITY</span>
      </div>
      <ActivityFeed events={data.activity} />

      {/* v2 stub — honest about what isn't built yet */}
      <div style={{ margin: "18px 4px 0", border: "1px dashed rgba(255,255,255,0.12)", borderRadius: 11, padding: "11px 13px", display: "flex", alignItems: "center", gap: 10 }}>
        <LineChart size={16} color={C.mute3} />
        <div>
          <p style={{ fontSize: 12, margin: 0, color: "#9a9aa6" }}>deploy frequency · build duration</p>
          <p style={{ fontSize: 10, color: C.mute3, margin: "3px 0 0", letterSpacing: "0.04em" }}>needs stored history — v2</p>
        </div>
      </div>
    </div>
  );
}

/* ----------------------------------------------- sample data: swap for fetch */
const SAMPLE = {
  refreshedAgo: "18s ago",
  projects: [
    {
      id: "partida",
      name: "partida",
      domain: "partida.me",
      found: true,
      services: [
        { id: "p-web", name: "web", status: "healthy", ref: "fdbff05", branch: "main", age: "16d", url: "#" },
        { id: "p-db", name: "postgres", status: "healthy", source: "managed", age: "16d", url: "#" },
      ],
      previews: [{ id: "p-prev", name: "web", status: "building" }],
    },
    {
      id: "hunterprotocol",
      name: "hunterprotocol",
      found: true,
      services: [
        { id: "h-api", name: "api", status: "healthy", ref: "a1b9e02", branch: "main", age: "3d", url: "#" },
        { id: "h-db", name: "postgres", status: "healthy", source: "managed", age: "3d", url: "#" },
      ],
    },
    {
      id: "kaus",
      name: "kaus editions",
      found: false,
      note: "not found on railway — verify source",
    },
  ],
  activity: [
    { id: "a1", status: "building", target: "partida / web", verb: "building", meta: "pr-42 · 7c1d4a · ausbernard · 4m ago" },
    { id: "a2", status: "healthy", target: "hunterprotocol / api", verb: "deployed", meta: "production · a1b9e02 · main · 3d ago" },
    { id: "a3", status: "healthy", target: "partida / web", verb: "deployed", meta: "production · fdbff05 · main · 16d ago" },
  ],
};

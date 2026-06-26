import { useEffect, useState } from "react";
import { LayoutGrid, CheckCircle2, RefreshCw, AlertCircle, AlertTriangle, CircleDashed } from "lucide-react";


const API_URL = import.meta.env.VITE_API_URL ?? "";


export default function Dashboard() {
  const [data, setData] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const refresh = () => {
    setRefreshing(true);
    const started = Date.now();

    fetch(`${API_URL}/api/state`)
    .then((res) => res.json())
    .then((json) => {
      setData(json);
    })
    .finally(() => {
      const elapsed = Date.now() - started;
      const remaining = Math.max(0, 900 - elapsed);
      setTimeout(() => setRefreshing(false), remaining)
    });
  };

  useEffect(() => {
    refresh();
  }, []);

  if (!data) return <div>loading...</div>;

  const stats = [
    { label: "Services",  value: data.summary.total,    color: "#FFFFFF", icon: LayoutGrid },
    { label: "Healthy",  value: data.summary.healthy,  color: "#34d399", icon: CheckCircle2 },
    { label: "Deploying", value: data.summary.building, color: "#fbbf24", icon: RefreshCw },
    { label: "Down",     value: data.summary.down,     color: "#f87171", icon: AlertTriangle },
    // { label: "Degraded", value: data.summary.degraded, color: "#fbbf24", icon: AlertCircle },
    // { label: "Missing",  value: data.summary.missing,  color: "#71717a", icon: CircleDashed },
  ];

  const statusColor = (status) => ({
  healthy: "#34d399",
  degraded: "#e47921",
  building: "#fbbf24",
  down: "#f87171",
  missing: "#71717a",
  }[status] ?? "#71717a");

  const StatusPill = ({ status }) => (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      fontSize: 12, color: statusColor(status),
      border: "1px solid #27272a", borderRadius: 999, padding: "3px 10px",
    }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: statusColor(status) }} />
      {status}
    </span>
  );

  const cardStyle = {
    border: "1px solid #27272a",
    background: "rgba(24,24,27,0.4)",
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
  };

  const projectHeader = {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  };

  const statusPill = {
    display: "inline-flex", alignItems: "center",
    fontSize: 12, border: "1px solid", borderRadius: 999, padding: "3px 10px",
  };

  return (
    <div style= {{ padding: "24px 24px 0" }}>
      {/* HEADER __ NAVIGATION */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        paddingBottom: 16,
        marginBottom: 24,
        borderBottom: "1px solid #27272a",
      }}>
      {/* left: logo */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style={{ display: "block" }}>
          <circle cx="12" cy="12" r="10" stroke="#34d399" strokeWidth="2" />
          <circle cx="12" cy="12" r="5.5" stroke="#34d399" strokeWidth="2" />
          <circle cx="12" cy="12" r="2" fill="#34d399" />
        </svg>
        <span style={{ fontSize: 18, fontWeight: 600, color: "#fafafa" }}>vigia</span>
        {/* <span style={{ fontSize: 13, color: "#71717a" }}>deployment health</span> */}
      </div>

        {/* right: controls */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            height: 32, boxSizing: "border-box",
            fontSize: 13, color: "#ffffff",
            background: "transparent", border: "1px solid #27272a",
            borderRadius: 8, padding: "0 12px", cursor: "pointer",
          }}>
            auto off
          </button>
          <button onClick={refresh} style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            height: 32, boxSizing: "border-box",
            fontSize: 13, color: "#000000", fontWeight: 500,
            background: "#ffffff", border: "1px solid #27272a",
            borderRadius: 8, padding: "0 12px", cursor: "pointer",
          }}>
          <RefreshCw size={15} style={{
            animation: refreshing ? "spin 1.2s linear infinite" : "none",
            transformOrigin: "center",
            transition: "transform 0.4s ease-out",
          }} />
          </button>
        </div>
      </div>

      {/* SUMMARY __ CARDS */}
      <div className="stat-row">
        {stats.map((stat) => (
          <div key={stat.label} className="stat-card" style={{
            border: "1px solid #27272a",
            background: "rgba(24,24,27,0.4)",
            borderRadius: 12,
            padding: 16,
          }}>

          {/* ICONS */}
          <div style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}>
            <span style={{ fontSize: 11, letterSpacing: 1, textTransform: "uppercase", color: "#71717a" }}>
              {stat.label}
            </span>
            <stat.icon size={15} color={stat.color} strokeWidth={2} />
          </div>
          <div style={{ fontSize: 26, fontWeight: 600, color: stat.color, marginTop: 6}}>
            {stat.value}
          </div>
        </div>
      ))}
    </div>

    {/* PROJECT__CARDS */}
      <div style={{ marginTop: 24 }}>
        {data.projects.map((project) => {
          // BRANCH 1: not found on Railway (but in configuration)
          if (!project.found) {
            return (
              <div key={project.id} style={cardStyle}>
                <div style={projectHeader}>
                  <span style={{ fontSize: 16, fontWeight: 600, color: "#fafafa" }}><LayoutGrid size={15} /> {project.name}</span>
                  <span style={{ ...statusPill, color: "#71717a", borderColor: "#27272a" }}>not found</span>
                </div>
                <div style={{ fontSize: 13, color: "#71717a", marginTop: 10 }}>{project.note}</div>
              </div>
            );
          }

          // BRANCH 2: project found but empty (services)
          if (project.empty) {
            return (
              <div key={project.id} style={cardStyle}>
                <div style={projectHeader}>
                  <span style={{ fontSize: 16, fontWeight: 600, color: "#fafafa" }}><LayoutGrid size={15} /> {project.name}</span>
                  <StatusPill status={project.status} />
                </div>
                <div style={{ fontSize: 13, color: "#71717a", marginTop: 10 }}>No services deployed</div>
              </div>
            );
          }

          //BRANCH 3: project found with services
          return (
            <div key={project.id} style={cardStyle}>
              <div style={projectHeader}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: 16, fontWeight: 600, color: "#fafafa" }}> <LayoutGrid size={15} /> {project.name}</span>
                  {project.domain && (
                    <span style={{ fontSize: 13, color: "#71717a" }}>{project.domain}</span>
                  )}
                </div>
                <StatusPill status={project.status} />
              </div>

              <div style={{ marginTop: 14, display: "flex", flexDirection: "column", gap: 10 }}>
                {project.services.map((service) => (
                  <div key={service.id} style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    paddingTop: 10, borderTop: "1px solid #1c1c1f",
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span style={{
                        width: 7, height: 7, borderRadius: "50%",
                        background: statusColor(service.status),
                      }} />
                      <span style={{ fontSize: 14, color: "#e4e4e7", fontFamily: "var(--mono)" }}>
                        {service.name}
                      </span>
                      {service.environment && (
                        <span style={{
                          fontSize: 11, color: "#a1a1aa",
                          border: "1px solid #27272a", borderRadius: 6,
                          padding: "2px 7px",
                        }}>
                          {service.environment}
                        </span>
                      )}
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 12, color: "#71717a" }}>
                      {service.ref && <span style={{ fontFamily: "var(--mono)" }}>{service.ref}</span>}
                      <span>{service.branch ?? service.source}</span>
                      {service.age && <span>{service.age}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
  </div>
  ); 
}
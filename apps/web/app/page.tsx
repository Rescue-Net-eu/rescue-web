import { ApiStatus } from "./components/api-status";

export default function HomePage() {
  return (
    <main style={{ maxWidth: 760, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <header style={{ borderBottom: "1px solid #e5e5e5", paddingBottom: "1rem" }}>
        <h1 style={{ marginBottom: "0.25rem" }}>rescue-net.eu</h1>
        <p style={{ color: "#555", marginTop: 0 }}>Dispatcher console — MVP skeleton</p>
      </header>

      <section
        style={{
          background: "#fff8e1",
          border: "1px solid #f0d480",
          borderRadius: 8,
          padding: "0.75rem 1rem",
          margin: "1.5rem 0",
          fontSize: "0.9rem",
        }}
      >
        rescue-net.eu is a volunteer coordination platform. In life-threatening
        emergencies, contact your official emergency number (e.g. 112) first.
      </section>

      <ApiStatus />

      <section style={{ marginTop: "2rem" }}>
        <h2>Next steps</h2>
        <p style={{ color: "#555" }}>
          This is the console skeleton. Incident creation, mission monitoring and
          the live map are implemented following the development priorities in the{" "}
          <a href="https://github.com/Rescue-Net-eu/rescue-web/blob/main/docs/project-manual.md">
            project manual
          </a>
          .
        </p>
      </section>
    </main>
  );
}

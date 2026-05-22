from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.services.metrics_reader import read_training_metrics

router = APIRouter()


@router.get("/api/jobs/{job_id}/metrics")
def get_job_metrics(job_id: str) -> dict:
    return read_training_metrics(job_id)


@router.get("/jobs/{job_id}/metrics-view", response_class=HTMLResponse)
def get_job_metrics_view(job_id: str) -> str:
    metrics_url = f"/api/jobs/{job_id}/metrics"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Training Loss - {job_id}</title>
  <style>
    :root {{
      color-scheme: dark;
      font-family: Inter, Segoe UI, Arial, sans-serif;
      background: #111318;
      color: #e6e8ee;
    }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr;
    }}
    header {{
      padding: 18px 22px;
      border-bottom: 1px solid #2b303b;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
    }}
    h1 {{
      font-size: 18px;
      margin: 0;
      font-weight: 650;
    }}
    .stats {{
      display: flex;
      gap: 18px;
      color: #b8bfcc;
      font-size: 13px;
      flex-wrap: wrap;
    }}
    main {{
      padding: 18px 22px 24px;
      display: grid;
      gap: 14px;
    }}
    .chart {{
      min-height: 420px;
      border: 1px solid #2b303b;
      background: #171a21;
      border-radius: 8px;
      overflow: hidden;
    }}
    svg {{
      display: block;
      width: 100%;
      height: 420px;
    }}
    .axis {{
      stroke: #465062;
      stroke-width: 1;
    }}
    .grid {{
      stroke: #27303d;
      stroke-width: 1;
    }}
    .line {{
      fill: none;
      stroke: #59c2ff;
      stroke-width: 2.2;
    }}
    .empty {{
      color: #8992a3;
      padding: 28px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Training Loss</h1>
    <div class="stats">
      <span>Job: <strong id="job">{job_id}</strong></span>
      <span>Step: <strong id="step">-</strong></span>
      <span>Loss: <strong id="loss">-</strong></span>
      <span>Progress: <strong id="progress">0%</strong></span>
    </div>
  </header>
  <main>
    <div class="chart" id="chart"><div class="empty">Waiting for OpenSplat loss output...</div></div>
  </main>
  <script>
    const metricsUrl = "{metrics_url}";
    const chart = document.getElementById("chart");
    const stepEl = document.getElementById("step");
    const lossEl = document.getElementById("loss");
    const progressEl = document.getElementById("progress");

    function formatLoss(value) {{
      return value == null ? "-" : Number(value).toFixed(6);
    }}

    function render(points) {{
      if (!points.length) {{
        chart.innerHTML = '<div class="empty">Waiting for OpenSplat loss output...</div>';
        return;
      }}

      const width = 1000;
      const height = 420;
      const pad = {{ left: 54, right: 20, top: 24, bottom: 38 }};
      const xs = points.map(p => p.step);
      const ys = points.map(p => p.loss);
      const minX = Math.min(...xs);
      const maxX = Math.max(...xs);
      const minY = Math.min(...ys);
      const maxY = Math.max(...ys);
      const rangeX = Math.max(1, maxX - minX);
      const rangeY = Math.max(1e-9, maxY - minY);
      const x = value => pad.left + ((value - minX) / rangeX) * (width - pad.left - pad.right);
      const y = value => height - pad.bottom - ((value - minY) / rangeY) * (height - pad.top - pad.bottom);
      const path = points.map((p, i) => `${{i ? "L" : "M"}} ${{x(p.step).toFixed(2)}} ${{y(p.loss).toFixed(2)}}`).join(" ");
      const grid = [0, 1, 2, 3, 4].map(i => {{
        const gy = pad.top + i * ((height - pad.top - pad.bottom) / 4);
        return `<line class="grid" x1="${{pad.left}}" y1="${{gy}}" x2="${{width - pad.right}}" y2="${{gy}}" />`;
      }}).join("");
      chart.innerHTML = `<svg viewBox="0 0 ${{width}} ${{height}}" preserveAspectRatio="none">
        ${{grid}}
        <line class="axis" x1="${{pad.left}}" y1="${{height - pad.bottom}}" x2="${{width - pad.right}}" y2="${{height - pad.bottom}}" />
        <line class="axis" x1="${{pad.left}}" y1="${{pad.top}}" x2="${{pad.left}}" y2="${{height - pad.bottom}}" />
        <path class="line" d="${{path}}" />
      </svg>`;
    }}

    async function refresh() {{
      const response = await fetch(metricsUrl, {{ cache: "no-store" }});
      const metrics = await response.json();
      stepEl.textContent = metrics.latest_step ?? "-";
      lossEl.textContent = formatLoss(metrics.latest_loss);
      progressEl.textContent = `${{metrics.progress ?? 0}}%`;
      render(metrics.points ?? []);
    }}

    refresh().catch(console.error);
    setInterval(() => refresh().catch(console.error), 2000);
  </script>
</body>
</html>"""


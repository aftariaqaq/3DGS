from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.services import scene_store
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
    .tick {{
      stroke: #465062;
      stroke-width: 1;
    }}
    .tick-label {{
      fill: #aeb7c6;
      font-size: 12px;
    }}
    .axis-label {{
      fill: #d4dae5;
      font-size: 13px;
      font-weight: 650;
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
    <div class="chart" id="chart"><div class="empty">Waiting for training loss output...</div></div>
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
        chart.innerHTML = '<div class="empty">Waiting for training loss output...</div>';
        return;
      }}

      const width = 1000;
      const height = 420;
      const pad = {{ left: 72, right: 28, top: 28, bottom: 58 }};
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
      const xTicks = [0, 1, 2, 3, 4].map(i => Math.round(minX + (i / 4) * rangeX));
      const yTicks = [0, 1, 2, 3, 4].map(i => maxY - (i / 4) * rangeY);
      const grid = yTicks.map(value => {{
        const gy = y(value);
        return `<line class="grid" x1="${{pad.left}}" y1="${{gy.toFixed(2)}}" x2="${{width - pad.right}}" y2="${{gy.toFixed(2)}}" />`;
      }}).join("");
      const xAxisTicks = xTicks.map(value => {{
        const tx = x(value);
        return `<g>
          <line class="tick" x1="${{tx.toFixed(2)}}" y1="${{height - pad.bottom}}" x2="${{tx.toFixed(2)}}" y2="${{height - pad.bottom + 6}}" />
          <text class="tick-label" x="${{tx.toFixed(2)}}" y="${{height - pad.bottom + 22}}" text-anchor="middle">${{value}}</text>
        </g>`;
      }}).join("");
      const yAxisTicks = yTicks.map(value => {{
        const ty = y(value);
        return `<g>
          <line class="tick" x1="${{pad.left - 6}}" y1="${{ty.toFixed(2)}}" x2="${{pad.left}}" y2="${{ty.toFixed(2)}}" />
          <text class="tick-label" x="${{pad.left - 10}}" y="${{(ty + 4).toFixed(2)}}" text-anchor="end">${{formatLoss(value)}}</text>
        </g>`;
      }}).join("");
      chart.innerHTML = `<svg viewBox="0 0 ${{width}} ${{height}}" preserveAspectRatio="none">
        ${{grid}}
        <line class="axis" x1="${{pad.left}}" y1="${{height - pad.bottom}}" x2="${{width - pad.right}}" y2="${{height - pad.bottom}}" />
        <line class="axis" x1="${{pad.left}}" y1="${{pad.top}}" x2="${{pad.left}}" y2="${{height - pad.bottom}}" />
        ${{xAxisTicks}}
        ${{yAxisTicks}}
        <text class="axis-label" x="${{(pad.left + width - pad.right) / 2}}" y="${{height - 14}}" text-anchor="middle">Step</text>
        <text class="axis-label" transform="translate(18 ${{(pad.top + height - pad.bottom) / 2}}) rotate(-90)" text-anchor="middle">Loss</text>
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


@router.get("/scenes/{scene_id}/viewer", response_class=HTMLResponse)
def get_scene_viewer(scene_id: str) -> str:
    scene = scene_store.read_scene(scene_id)
    model_url = scene["model_url"]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Scene Viewer - {scene_id}</title>
  <style>
    :root {{
      color-scheme: dark;
      font-family: Inter, Segoe UI, Arial, sans-serif;
      background: #101216;
      color: #e8ecf3;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      min-height: 100vh;
      overflow: hidden;
    }}
    header {{
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 4;
      padding: 14px 18px;
      border-bottom: 1px solid #29313d;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
      background: rgba(16, 18, 22, 0.9);
      backdrop-filter: blur(12px);
    }}
    h1 {{
      margin: 0;
      font-size: 17px;
      font-weight: 650;
    }}
    .meta {{
      color: #aeb8c7;
      font-size: 13px;
    }}
    main {{
      position: relative;
      width: 100vw;
      height: 100vh;
      background: #11151d;
    }}
    #viewer-root {{
      width: 100%;
      height: 100%;
      position: absolute;
      inset: 0;
    }}
    .status {{
      position: absolute;
      left: 16px;
      bottom: 16px;
      z-index: 5;
      padding: 8px 10px;
      border: 1px solid #344052;
      background: rgba(16, 18, 22, 0.82);
      border-radius: 6px;
      color: #c7d0df;
      font-size: 12px;
      max-width: min(520px, calc(100vw - 32px));
    }}
    .controls {{
      position: absolute;
      left: 16px;
      top: 72px;
      z-index: 5;
      width: 240px;
      border: 1px solid #303846;
      border-radius: 8px;
      background: rgba(18, 22, 30, 0.82);
      box-shadow: 0 18px 48px rgba(0, 0, 0, 0.22);
      overflow: hidden;
      backdrop-filter: blur(12px);
    }}
    .controls h2 {{
      margin: 0;
      padding: 12px 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      font-size: 13px;
      font-weight: 560;
      color: #aab4c3;
    }}
    .controls dl {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 9px 14px;
      margin: 0;
      padding: 14px;
      font-size: 12px;
    }}
    .controls dt {{
      color: #e4e9f2;
    }}
    .controls dd {{
      margin: 0;
      color: #9da8b8;
    }}
    .error {{
      color: #ffb4b4;
      border-color: rgba(255, 100, 100, 0.45);
    }}
  </style>
</head>
<body>
  <header>
    <h1>3DGS Viewer</h1>
    <div class="meta">Scene: <strong>{scene_id}</strong></div>
  </header>
  <main>
    <div id="viewer-root"></div>
    <section class="controls" aria-label="Controls">
      <h2>Controls</h2>
      <dl>
        <dt>Left Drag</dt><dd>Rotate</dd>
        <dt>Scroll</dt><dd>Zoom</dd>
        <dt>Right Drag</dt><dd>Pan</dd>
        <dt>Space</dt><dd>Reset</dd>
      </dl>
    </section>
    <div class="status" id="status">Loading Gaussian splats...</div>
  </main>
  <script type="module">
    import * as GaussianSplats3D from "https://esm.sh/@mkkellogg/gaussian-splats-3d@0.4.7?deps=three@0.184.0";

    const modelUrl = "{model_url}";
    const root = document.getElementById("viewer-root");
    const statusEl = document.getElementById("status");

    async function main() {{
      const viewer = new GaussianSplats3D.Viewer({{
        rootElement: root,
        cameraUp: [0, -1, -0.6],
        initialCameraPosition: [-1, -4, 6],
        initialCameraLookAt: [0, 4, 0],
        sharedMemoryForWorkers: false,
        gpuAcceleratedSort: false,
        useBuiltInControls: true
      }});

      await viewer.addSplatScene(modelUrl, {{
        format: GaussianSplats3D.SceneFormat.Ply,
        splatAlphaRemovalThreshold: 5,
        showLoadingUI: true,
        progressiveLoad: false,
        position: [0, 1, 0],
        rotation: [0, 0, 0, 1],
        scale: [1.5, 1.5, 1.5]
      }});
      viewer.start();
      statusEl.textContent = `Loaded Gaussian splats from ${{modelUrl}}`;
    }}

    main().catch(error => {{
      console.error(error);
      statusEl.classList.add("error");
      statusEl.textContent = error.message;
    }});
  </script>
</body>
</html>"""

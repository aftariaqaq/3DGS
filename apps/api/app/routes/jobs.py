from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.services import scene_store
from app.services.colmap_metrics_reader import read_colmap_metrics
from app.services.metrics_reader import read_training_metrics

router = APIRouter()


@router.get("/api/jobs/{job_id}/metrics")
def get_job_metrics(job_id: str) -> dict:
    return read_training_metrics(job_id)


@router.get("/api/jobs/{job_id}/colmap-metrics")
def get_job_colmap_metrics(job_id: str) -> dict:
    return read_colmap_metrics(job_id)


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
    <div class="chart" id="chart"><div class="empty">Waiting for training scalar output...</div></div>
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
        chart.innerHTML = '<div class="empty">Waiting for TensorBoard training scalar output...</div>';
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


@router.get("/jobs/{job_id}/colmap-view", response_class=HTMLResponse)
def get_job_colmap_view(job_id: str) -> str:
    metrics_url = f"/api/jobs/{job_id}/colmap-metrics"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>COLMAP Monitor - {job_id}</title>
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
      flex-wrap: wrap;
    }}
    h1 {{
      font-size: 18px;
      margin: 0;
      font-weight: 650;
    }}
    main {{
      padding: 18px 22px 24px;
      display: grid;
      gap: 14px;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
    }}
    .metric {{
      border: 1px solid #2b303b;
      background: #171a21;
      border-radius: 8px;
      padding: 14px;
    }}
    .label {{
      color: #9aa4b5;
      font-size: 12px;
      margin-bottom: 8px;
    }}
    .value {{
      font-size: 20px;
      font-weight: 650;
    }}
    .bar {{
      height: 8px;
      background: #252b35;
      border-radius: 999px;
      overflow: hidden;
      margin-top: 10px;
    }}
    .fill {{
      height: 100%;
      width: 0%;
      background: #59c2ff;
    }}
    pre {{
      margin: 0;
      min-height: 340px;
      max-height: 560px;
      overflow: auto;
      border: 1px solid #2b303b;
      background: #0e1015;
      border-radius: 8px;
      padding: 14px;
      color: #c5cbd6;
      white-space: pre-wrap;
      font-size: 12px;
      line-height: 1.45;
    }}
  </style>
</head>
<body>
  <header>
    <h1>COLMAP Monitor</h1>
    <div>Job: <strong>{job_id}</strong></div>
  </header>
  <main>
    <section class="stats">
      <div class="metric"><div class="label">Stage</div><div class="value" id="stage">-</div></div>
      <div class="metric"><div class="label">Images</div><div class="value" id="images">0</div></div>
      <div class="metric"><div class="label">Registered Images</div><div class="value" id="registered">0</div></div>
      <div class="metric"><div class="label">Sparse Points</div><div class="value" id="points">0</div></div>
      <div class="metric">
        <div class="label">Feature Extraction</div><div class="value" id="feature">0%</div>
        <div class="bar"><div class="fill" id="feature-fill"></div></div>
      </div>
      <div class="metric">
        <div class="label">Matching</div><div class="value" id="matching">0%</div>
        <div class="bar"><div class="fill" id="matching-fill"></div></div>
      </div>
    </section>
    <pre id="recent-log"></pre>
  </main>
  <script>
    const metricsUrl = "{metrics_url}";
    const ids = ["stage", "images", "registered", "points", "feature", "matching", "feature-fill", "matching-fill", "recent-log"];
    const el = Object.fromEntries(ids.map(id => [id, document.getElementById(id)]));

    function setProgress(name, progress) {{
      const percent = progress?.percent ?? 0;
      el[name].textContent = `${{percent}}%`;
      el[`${{name}}-fill`].style.width = `${{percent}}%`;
    }}

    async function refresh() {{
      const response = await fetch(metricsUrl, {{ cache: "no-store" }});
      const metrics = await response.json();
      el.stage.textContent = metrics.stage ?? "-";
      el.images.textContent = metrics.images_total ?? 0;
      el.registered.textContent = metrics.registered_images ?? 0;
      el.points.textContent = metrics.sparse_points ?? 0;
      setProgress("feature", metrics.feature_progress);
      setProgress("matching", metrics.matching_progress);
      el["recent-log"].textContent = metrics.recent_log || "Waiting for COLMAP logs...";
    }}

    refresh().catch(console.error);
    setInterval(() => refresh().catch(console.error), 2000);
  </script>
</body>
</html>"""


@router.get("/scenes/{scene_id}/viewer", response_class=HTMLResponse)
def get_scene_viewer(scene_id: str) -> str:
    scene = scene_store.read_scene(scene_id)
    model_url = scene.get("source_model_url", scene["model_url"])
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
    .orientation {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 6px;
      padding: 0 14px 14px;
    }}
    .orientation button {{
      border: 1px solid #3a4555;
      border-radius: 6px;
      background: rgba(31, 38, 50, 0.9);
      color: #cbd4e3;
      padding: 7px 6px;
      font: inherit;
      cursor: pointer;
    }}
    .orientation button.active {{
      border-color: #78b7ff;
      color: #ffffff;
      background: rgba(70, 124, 190, 0.42);
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
      <div class="orientation">
        <button type="button" data-orientation="nerfstudio">Upright</button>
        <button type="button" data-orientation="raw">Raw</button>
        <button type="button" data-orientation="roll180">Roll 180</button>
      </div>
    </section>
    <div class="status" id="status">Loading Gaussian splats...</div>
  </main>
  <script type="module">
    import * as GaussianSplats3D from "https://esm.sh/@mkkellogg/gaussian-splats-3d@0.4.7?deps=three@0.184.0";

    const modelUrl = "{model_url}";
    const root = document.getElementById("viewer-root");
    const statusEl = document.getElementById("status");
    const orientationPresets = {{
      nerfstudio: {{ rotation: [1, 0, 0, 0] }},
      raw: {{ rotation: [0, 0, 0, 1] }},
      roll180: {{ rotation: [0, 0, 1, 0] }}
    }};
    const params = new URLSearchParams(window.location.search);
    const orientation = orientationPresets[params.get("orientation")] ? params.get("orientation") : "nerfstudio";
    const preset = orientationPresets[orientation];

    document.querySelectorAll("[data-orientation]").forEach(button => {{
      button.classList.toggle("active", button.dataset.orientation === orientation);
      button.addEventListener("click", () => {{
        const next = new URL(window.location.href);
        next.searchParams.set("orientation", button.dataset.orientation);
        window.location.href = next.toString();
      }});
    }});

    async function main() {{
      const viewer = new GaussianSplats3D.Viewer({{
        rootElement: root,
        cameraUp: [0, 1, 0],
        initialCameraPosition: [0, -4, 2],
        initialCameraLookAt: [0, 0, 0],
        sharedMemoryForWorkers: false,
        gpuAcceleratedSort: true,
        useBuiltInControls: true
      }});

      await viewer.addSplatScene(modelUrl, {{
        format: GaussianSplats3D.SceneFormat.Ply,
        splatAlphaRemovalThreshold: 5,
        showLoadingUI: true,
        progressiveLoad: true,
        position: [0, 0, 0],
        rotation: preset.rotation,
        scale: [1, 1, 1]
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


@router.get("/scenes/{scene_id}/supersplat", response_class=HTMLResponse)
def get_supersplat_viewer(scene_id: str) -> str:
    scene = scene_store.read_scene(scene_id)
    viewer_url = scene.get("supersplat_viewer_url", f"/static/scenes/{scene_id}/supersplat.html")
    fallback_url = scene.get("fallback_viewer_url", f"/scenes/{scene_id}/viewer")
    model_url = scene["model_url"]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SuperSplat Viewer - {scene_id}</title>
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
      background: #101216;
    }}
    header {{
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 3;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      padding: 0 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      background: rgba(16, 18, 22, 0.86);
      backdrop-filter: blur(10px);
    }}
    h1 {{
      margin: 0;
      font-size: 15px;
      font-weight: 650;
    }}
    .meta, a {{
      color: #c1cad8;
      font-size: 12px;
    }}
    iframe {{
      position: fixed;
      inset: 0;
      width: 100vw;
      height: 100vh;
      border: 0;
      background: #05070a;
    }}
    .status {{
      position: fixed;
      left: 16px;
      bottom: 16px;
      z-index: 3;
      padding: 8px 10px;
      border: 1px solid #344052;
      border-radius: 6px;
      background: rgba(16, 18, 22, 0.82);
      color: #c7d0df;
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <iframe src="{viewer_url}" title="SuperSplat Viewer"></iframe>
  <header>
    <h1>SuperSplat Viewer</h1>
    <div class="meta">Scene: <strong>{scene_id}</strong> · <a href="{fallback_url}">fallback viewer</a></div>
  </header>
  <div class="status">No browser-side conversion is performed. Loaded converted model: {model_url}</div>
</body>
</html>"""

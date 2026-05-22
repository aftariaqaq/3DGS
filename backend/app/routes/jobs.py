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
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr;
    }}
    header {{
      padding: 14px 18px;
      border-bottom: 1px solid #29313d;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
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
      min-height: 0;
      background: #151922;
    }}
    canvas {{
      display: block;
      width: 100%;
      height: 100%;
      min-height: calc(100vh - 52px);
      cursor: grab;
    }}
    canvas:active {{
      cursor: grabbing;
    }}
    .status {{
      position: absolute;
      left: 16px;
      bottom: 16px;
      padding: 8px 10px;
      border: 1px solid #344052;
      background: rgba(16, 18, 22, 0.82);
      border-radius: 6px;
      color: #c7d0df;
      font-size: 12px;
      max-width: min(520px, calc(100vw - 32px));
    }}
  </style>
</head>
<body>
  <header>
    <h1>Scene Viewer</h1>
    <div class="meta">Scene: <strong>{scene_id}</strong></div>
  </header>
  <main>
    <canvas id="viewer"></canvas>
    <div class="status" id="status">Loading scene...</div>
  </main>
  <script>
    const modelUrl = "{model_url}";
    const canvas = document.getElementById("viewer");
    const statusEl = document.getElementById("status");

    const typeSizes = {{
      char: 1, uchar: 1, int8: 1, uint8: 1,
      short: 2, ushort: 2, int16: 2, uint16: 2,
      int: 4, uint: 4, int32: 4, uint32: 4,
      float: 4, float32: 4, double: 8, float64: 8
    }};

    function readValue(view, offset, type) {{
      switch (type) {{
        case "char":
        case "int8": return view.getInt8(offset);
        case "uchar":
        case "uint8": return view.getUint8(offset);
        case "short":
        case "int16": return view.getInt16(offset, true);
        case "ushort":
        case "uint16": return view.getUint16(offset, true);
        case "int":
        case "int32": return view.getInt32(offset, true);
        case "uint":
        case "uint32": return view.getUint32(offset, true);
        case "double":
        case "float64": return view.getFloat64(offset, true);
        default: return view.getFloat32(offset, true);
      }}
    }}

    function clamp01(value) {{
      return Math.max(0, Math.min(1, value));
    }}

    function dcToColor(value) {{
      return clamp01(0.5 + 0.2820947918 * value);
    }}

    function parsePly(buffer) {{
      const bytes = new Uint8Array(buffer);
      const marker = new TextEncoder().encode("end_header\\n");
      let headerEnd = -1;
      for (let i = 0; i <= bytes.length - marker.length; i++) {{
        let found = true;
        for (let j = 0; j < marker.length; j++) {{
          if (bytes[i + j] !== marker[j]) {{
            found = false;
            break;
          }}
        }}
        if (found) {{
          headerEnd = i + marker.length;
          break;
        }}
      }}
      if (headerEnd < 0) {{
        throw new Error("Invalid PLY: missing header terminator");
      }}

      const header = new TextDecoder().decode(bytes.slice(0, headerEnd));
      if (!header.includes("format binary_little_endian")) {{
        throw new Error("Only binary_little_endian PLY is supported in this viewer");
      }}

      const lines = header.split(/\\r?\\n/);
      let vertexCount = 0;
      const properties = [];
      let inVertex = false;
      for (const line of lines) {{
        const parts = line.trim().split(/\\s+/);
        if (parts[0] === "element") {{
          inVertex = parts[1] === "vertex";
          if (inVertex) {{
            vertexCount = Number(parts[2]);
          }}
        }} else if (inVertex && parts[0] === "property" && parts.length >= 3) {{
          properties.push({{ type: parts[1], name: parts[2] }});
        }}
      }}

      const stride = properties.reduce((sum, prop) => sum + (typeSizes[prop.type] || 4), 0);
      const propOffsets = new Map();
      let propOffset = 0;
      for (const prop of properties) {{
        propOffsets.set(prop.name, {{ offset: propOffset, type: prop.type }});
        propOffset += typeSizes[prop.type] || 4;
      }}

      const view = new DataView(buffer, headerEnd);
      const positions = new Float32Array(vertexCount * 3);
      const colors = new Float32Array(vertexCount * 3);
      let minX = Infinity, minY = Infinity, minZ = Infinity;
      let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;

      function readProp(base, name, fallback = 0) {{
        const prop = propOffsets.get(name);
        if (!prop) return fallback;
        return readValue(view, base + prop.offset, prop.type);
      }}

      for (let i = 0; i < vertexCount; i++) {{
        const base = i * stride;
        const x = readProp(base, "x");
        const y = readProp(base, "y");
        const z = readProp(base, "z");
        positions[i * 3] = x;
        positions[i * 3 + 1] = y;
        positions[i * 3 + 2] = z;
        minX = Math.min(minX, x); minY = Math.min(minY, y); minZ = Math.min(minZ, z);
        maxX = Math.max(maxX, x); maxY = Math.max(maxY, y); maxZ = Math.max(maxZ, z);

        if (propOffsets.has("red")) {{
          colors[i * 3] = readProp(base, "red") / 255;
          colors[i * 3 + 1] = readProp(base, "green") / 255;
          colors[i * 3 + 2] = readProp(base, "blue") / 255;
        }} else {{
          colors[i * 3] = dcToColor(readProp(base, "f_dc_0"));
          colors[i * 3 + 1] = dcToColor(readProp(base, "f_dc_1"));
          colors[i * 3 + 2] = dcToColor(readProp(base, "f_dc_2"));
        }}
      }}

      const cx = (minX + maxX) / 2;
      const cy = (minY + maxY) / 2;
      const cz = (minZ + maxZ) / 2;
      const scale = 2 / Math.max(maxX - minX, maxY - minY, maxZ - minZ, 1e-6);
      for (let i = 0; i < vertexCount; i++) {{
        positions[i * 3] = (positions[i * 3] - cx) * scale;
        positions[i * 3 + 1] = (positions[i * 3 + 1] - cy) * scale;
        positions[i * 3 + 2] = (positions[i * 3 + 2] - cz) * scale;
      }}

      return {{ positions, colors, vertexCount }};
    }}

    function mat4Perspective(out, fovy, aspect, near, far) {{
      const f = 1 / Math.tan(fovy / 2);
      out.set([f / aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, (far + near) / (near - far), -1, 0, 0, (2 * far * near) / (near - far), 0]);
      return out;
    }}

    function mat4View(out, yaw, pitch, distance) {{
      const cy = Math.cos(yaw), sy = Math.sin(yaw);
      const cp = Math.cos(pitch), sp = Math.sin(pitch);
      out.set([
        cy, sy * sp, sy * cp, 0,
        0, cp, -sp, 0,
        -sy, cy * sp, cy * cp, 0,
        0, 0, -distance, 1
      ]);
      return out;
    }}

    function mat4Multiply(out, a, b) {{
      const r = new Float32Array(16);
      for (let row = 0; row < 4; row++) {{
        for (let col = 0; col < 4; col++) {{
          r[col * 4 + row] = a[row] * b[col * 4] + a[4 + row] * b[col * 4 + 1] + a[8 + row] * b[col * 4 + 2] + a[12 + row] * b[col * 4 + 3];
        }}
      }}
      out.set(r);
      return out;
    }}

    async function main() {{
      const response = await fetch(modelUrl, {{ cache: "no-store" }});
      if (!response.ok) throw new Error(`Failed to load model: ${{response.status}}`);
      const scene = parsePly(await response.arrayBuffer());
      statusEl.textContent = `Loaded ${{scene.vertexCount.toLocaleString()}} points from ${{modelUrl}}`;

      const gl = canvas.getContext("webgl", {{ antialias: true }});
      if (!gl) throw new Error("WebGL is not available");

      const vs = `
        attribute vec3 position;
        attribute vec3 color;
        uniform mat4 mvp;
        uniform float pointSize;
        varying vec3 vColor;
        void main() {{
          gl_Position = mvp * vec4(position, 1.0);
          gl_PointSize = pointSize;
          vColor = color;
        }}
      `;
      const fs = `
        precision mediump float;
        varying vec3 vColor;
        void main() {{
          vec2 d = gl_PointCoord - vec2(0.5);
          if (dot(d, d) > 0.25) discard;
          gl_FragColor = vec4(vColor, 0.92);
        }}
      `;
      function compile(type, source) {{
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader));
        return shader;
      }}
      const program = gl.createProgram();
      gl.attachShader(program, compile(gl.VERTEX_SHADER, vs));
      gl.attachShader(program, compile(gl.FRAGMENT_SHADER, fs));
      gl.linkProgram(program);
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
      gl.useProgram(program);

      function bindAttribute(name, data) {{
        const buffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
        gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
        const location = gl.getAttribLocation(program, name);
        gl.enableVertexAttribArray(location);
        gl.vertexAttribPointer(location, 3, gl.FLOAT, false, 0, 0);
      }}
      bindAttribute("position", scene.positions);
      bindAttribute("color", scene.colors);

      const mvpLocation = gl.getUniformLocation(program, "mvp");
      const pointSizeLocation = gl.getUniformLocation(program, "pointSize");
      let yaw = 0.6, pitch = -0.35, distance = 3.3;
      let dragging = false, lastX = 0, lastY = 0;

      canvas.addEventListener("pointerdown", event => {{
        dragging = true;
        lastX = event.clientX;
        lastY = event.clientY;
        canvas.setPointerCapture(event.pointerId);
      }});
      canvas.addEventListener("pointermove", event => {{
        if (!dragging) return;
        yaw += (event.clientX - lastX) * 0.006;
        pitch = Math.max(-1.45, Math.min(1.45, pitch + (event.clientY - lastY) * 0.006));
        lastX = event.clientX;
        lastY = event.clientY;
      }});
      canvas.addEventListener("pointerup", () => dragging = false);
      canvas.addEventListener("wheel", event => {{
        event.preventDefault();
        distance = Math.max(1.2, Math.min(9, distance * (1 + event.deltaY * 0.001)));
      }}, {{ passive: false }});

      function render() {{
        const dpr = window.devicePixelRatio || 1;
        const width = Math.floor(canvas.clientWidth * dpr);
        const height = Math.floor(canvas.clientHeight * dpr);
        if (canvas.width !== width || canvas.height !== height) {{
          canvas.width = width;
          canvas.height = height;
        }}
        gl.viewport(0, 0, canvas.width, canvas.height);
        gl.clearColor(0.082, 0.098, 0.133, 1);
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
        gl.enable(gl.BLEND);
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

        const projection = mat4Perspective(new Float32Array(16), Math.PI / 3, canvas.width / canvas.height, 0.01, 100);
        const view = mat4View(new Float32Array(16), yaw, pitch, distance);
        const mvp = mat4Multiply(new Float32Array(16), projection, view);
        gl.uniformMatrix4fv(mvpLocation, false, mvp);
        gl.uniform1f(pointSizeLocation, Math.max(1.5, 2.4 * dpr));
        gl.drawArrays(gl.POINTS, 0, scene.vertexCount);
        requestAnimationFrame(render);
      }}
      render();
    }}

    main().catch(error => {{
      console.error(error);
      statusEl.textContent = error.message;
    }});
  </script>
</body>
</html>"""

import "./style.css";

type Outputs = {
  composite: string;
  shadow: string;
  mask: string;
};

function buildOutputsUrl(ts: number): Outputs {
  // Cache-bust with ?t=...
  return {
    composite: `/output/composite.png?t=${ts}`,
    shadow: `/output/shadow_only.png?t=${ts}`,
    mask: `/output/mask_debug.png?t=${ts}`,
  };
}

function renderApp() {
  const app = document.querySelector<HTMLDivElement>("#app");
  if (!app) return;

  let angle = 60;
  let elev = 30;
  let urls = buildOutputsUrl(Date.now());

  app.innerHTML = `
    <div class="container">
      <h1>Realistic Shadow Generator — Output Viewer (TypeScript)</h1>

      <div class="controls">
        <div class="control">
          <label>Light Angle (0–360): <span class="value" id="angleValue">${angle}</span>°</label>
          <input id="angle" type="range" min="0" max="360" value="${angle}" />
        </div>

        <div class="control">
          <label>Elevation (0–90): <span class="value" id="elevValue">${elev}</span>°</label>
          <input id="elev" type="range" min="0" max="90" value="${elev}" />
        </div>

        <button id="refresh">Refresh Images</button>
      </div>

      <div class="grid">
        <div class="card">
          <h2>composite.png</h2>
          <img id="imgComposite" src="${urls.composite}" alt="composite" />
        </div>

        <div class="card">
          <h2>shadow_only.png</h2>
          <img id="imgShadow" src="${urls.shadow}" alt="shadow only" />
        </div>

        <div class="card">
          <h2>mask_debug.png</h2>
          <img id="imgMask" src="${urls.mask}" alt="mask debug" />
        </div>
      </div>

      <p style="margin-top:12px; font-size:13px; color:#555;">
        Note: Sliders are for viewing/debug UI. Generate new images using Python, then copy them into <code>ts-viewer/public/output</code>, and click “Refresh Images”.
      </p>
    </div>
  `;

  const angleEl = document.getElementById("angle") as HTMLInputElement | null;
  const elevEl = document.getElementById("elev") as HTMLInputElement | null;
  const angleValueEl = document.getElementById("angleValue");
  const elevValueEl = document.getElementById("elevValue");

  const imgComposite = document.getElementById("imgComposite") as HTMLImageElement | null;
  const imgShadow = document.getElementById("imgShadow") as HTMLImageElement | null;
  const imgMask = document.getElementById("imgMask") as HTMLImageElement | null;

  function setSrc(img: HTMLImageElement | null, src: string) {
    if (!img) return;
    img.src = "";              // clear first
    img.src = src;             // then set new url
  }
  
  function refreshImages() {
    urls = buildOutputsUrl(Date.now());
    setSrc(imgComposite, urls.composite);
    setSrc(imgShadow, urls.shadow);
    setSrc(imgMask, urls.mask);
  }

  angleEl?.addEventListener("input", () => {
    angle = Number(angleEl.value);
    if (angleValueEl) angleValueEl.textContent = String(angle);
  });

  elevEl?.addEventListener("input", () => {
    elev = Number(elevEl.value);
    if (elevValueEl) elevValueEl.textContent = String(elev);
  });

  document.getElementById("refresh")?.addEventListener("click", refreshImages);
}

renderApp();

import * as THREE from "three";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import "./style.css";

gsap.registerPlugin(ScrollTrigger);

document.querySelector("#app").innerHTML = `
  <header class="site-header">
    <a class="brand" href="#top" aria-label="IFlow, back to top"><span class="brand-symbol">I<span class="brand-dot">●</span></span>FLOW</a>
    <span class="header-note">FINANCIAL INTELLIGENCE <span class="header-separator">/</span> CONCEPT 2026</span>
    <a class="header-link" href="#about">ABOUT THE EXPERIENCE <span aria-hidden="true">↗</span></a>
  </header>

  <main id="top">
    <section class="story" aria-label="Interactive scroll story">
      <div class="stage">
        <canvas id="scene" aria-hidden="true"></canvas>
        <div class="stage-grain" aria-hidden="true"></div>
        <div class="stage-frame" aria-hidden="true"><span></span><span></span><span></span><span></span></div>

        <div class="side-label side-label-left" aria-hidden="true">I/F — EXPERIMENT 001</div>
        <div class="side-label side-label-right" aria-hidden="true">SCROLL TO SHAPE THE STORY</div>

        <article class="chapter chapter-one" data-chapter="1">
          <div class="eyebrow"><span class="eyebrow-line"></span> INTRODUCING IFLOW</div>
          <h1>See the flow.<br/><em>See ahead.</em></h1>
          <p>A concept for bank teams and analysts to explore financial signals through a clearer lens.</p>
          <div class="chapter-index">01 <span>/</span> 03</div>
        </article>

        <article class="chapter chapter-two" data-chapter="2" aria-hidden="true">
          <div class="eyebrow"><span class="eyebrow-line"></span> FROM DATA TO SIGNAL</div>
          <h2>Patterns<br/><em>take shape.</em></h2>
          <p>Bring movement, context, and anomalies into one view. Follow the story behind the numbers.</p>
          <div class="chapter-index">02 <span>/</span> 03</div>
        </article>

        <article class="chapter chapter-three" data-chapter="3" aria-hidden="true">
          <div class="eyebrow"><span class="eyebrow-line"></span> INFORMED DECISIONS</div>
          <h2>Move with<br/><em>confidence.</em></h2>
          <p>Turn complex financial movement into a direction your team can understand and investigate.</p>
          <div class="chapter-index">03 <span>/</span> 03</div>
        </article>

        <div class="stage-bottom">
          <div class="scroll-hint"><span class="mouse-icon" aria-hidden="true"><span></span></span><span>SCROLL TO EXPLORE</span></div>
          <nav class="chapter-nav" aria-label="Story chapters">
            <button type="button" data-go="0" aria-label="Go to chapter one" class="is-current"><span>01</span></button>
            <button type="button" data-go="1" aria-label="Go to chapter two"><span>02</span></button>
            <button type="button" data-go="2" aria-label="Go to chapter three"><span>03</span></button>
          </nav>
          <span class="stage-time">00 : 03</span>
        </div>
        <div class="progress-track" aria-hidden="true"><div class="progress-bar"></div></div>
      </div>
    </section>

    <section class="outro" id="about">
      <div class="outro-kicker">BEYOND THE FRAME <span>↘</span></div>
      <h2>Clarity moves<br/><em>decisions.</em></h2>
      <div class="outro-bottom"><p>An interactive visual concept for IFlow, imagined for banks and financial analysts. Product features are ready to be defined by the team.</p><a href="#top">BACK TO THE BEGINNING <span>↑</span></a></div>
    </section>
  </main>
  <footer><span>© 2026 IFLOW</span><span>FINANCIAL INTELLIGENCE IN MOTION</span><span>01 — ∞</span></footer>
`;

const canvas = document.querySelector("#scene");
const stage = document.querySelector(".stage");
const chapters = [...document.querySelectorAll(".chapter")];
const navButtons = [...document.querySelectorAll("[data-go]")];
const progressBar = document.querySelector(".progress-bar");
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
camera.position.set(0, 0, 13);

let renderer;
try {
  renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
    powerPreference: "high-performance",
  });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.45;
} catch (error) {
  console.warn("WebGL is unavailable; displaying the CSS fallback.", error);
  stage.classList.add("no-webgl");
}

const sculpture = new THREE.Group();
scene.add(sculpture);

const sphereGeometry = new THREE.SphereGeometry(2.03, 96, 64);
const positions = sphereGeometry.attributes.position;
const vertex = new THREE.Vector3();
for (let i = 0; i < positions.count; i += 1) {
  vertex.fromBufferAttribute(positions, i);
  const unit = vertex.clone().normalize();
  const latitude = Math.atan2(unit.z, unit.x);
  const longitude = Math.acos(unit.y);
  const wave =
    1 +
    0.115 * Math.sin(4 * latitude + 2.1 * longitude) +
    0.065 * Math.sin(7 * longitude - 3 * latitude) +
    0.028 * Math.cos(11 * latitude + 5 * longitude);
  vertex.multiplyScalar(wave);
  positions.setXYZ(i, vertex.x, vertex.y, vertex.z);
}
sphereGeometry.computeVertexNormals();

const gold = new THREE.MeshPhysicalMaterial({
  color: 0xd49b4b,
  metalness: 0.78,
  roughness: 0.19,
  clearcoat: 0.75,
  clearcoatRoughness: 0.15,
});
const core = new THREE.Mesh(sphereGeometry, gold);
sculpture.add(core);

const ringMaterial = new THREE.MeshStandardMaterial({
  color: 0x986130,
  metalness: 0.9,
  roughness: 0.24,
  transparent: true,
  opacity: 0.8,
});
const ringA = new THREE.Mesh(
  new THREE.TorusGeometry(2.83, 0.018, 8, 180),
  ringMaterial,
);
const ringB = new THREE.Mesh(
  new THREE.TorusGeometry(3.15, 0.011, 8, 180),
  ringMaterial.clone(),
);
ringA.rotation.set(0.37, 0.59, 0.45);
ringB.rotation.set(-0.6, 0.25, -0.5);
sculpture.add(ringA, ringB);

const satelliteMaterial = new THREE.MeshPhysicalMaterial({
  color: 0xf1c477,
  metalness: 0.85,
  roughness: 0.18,
});
const satellites = [
  [-3.0, 1.5, 0.25, 0.13],
  [2.7, -1.7, 0.7, 0.085],
  [3.15, 1.8, -0.5, 0.06],
].map(([x, y, z, size]) => {
  const mesh = new THREE.Mesh(
    new THREE.SphereGeometry(size, 20, 16),
    satelliteMaterial,
  );
  mesh.position.set(x, y, z);
  sculpture.add(mesh);
  return mesh;
});

scene.add(new THREE.AmbientLight(0xffffff, 1.45));
const keyLight = new THREE.DirectionalLight(0xffe7bb, 4.6);
keyLight.position.set(-3, 5, 6);
scene.add(keyLight);
const rimLight = new THREE.DirectionalLight(0x8bafff, 3.5);
rimLight.position.set(5, -2, -4);
scene.add(rimLight);
const fillLight = new THREE.PointLight(0xffffff, 65);
fillLight.position.set(4, 2, 4);
scene.add(fillLight);

const cream = new THREE.Color("#f3eee4");
const blue = new THREE.Color("#0746c9");
const warm = new THREE.Color("#e7ddc9");
const bgColor = new THREE.Color();
const clamp = THREE.MathUtils.clamp;
const smooth = (a, b, x) => {
  const t = clamp((x - a) / (b - a), 0, 1);
  return t * t * (3 - 2 * t);
};
const mix = (a, b, t) => a + (b - a) * t;

function resize() {
  if (!renderer) return;
  const { clientWidth: width, clientHeight: height } = stage;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.fov = width < 680 ? 47 : 35;
  camera.updateProjectionMatrix();
  draw(currentProgress);
}

function draw(p) {
  const motion = reducedMotion.matches ? 0 : p;
  const toBlue = smooth(0.26, 0.43, p);
  const toWarm = smooth(0.66, 0.81, p);
  bgColor.copy(cream).lerp(blue, toBlue).lerp(warm, toWarm);
  stage.style.backgroundColor = `#${bgColor.getHexString()}`;
  stage.classList.toggle("is-blue", toBlue > 0.52 && toWarm < 0.52);

  const tilt = smooth(0.16, 0.49, p);
  const unwind = smooth(0.51, 0.91, p);
  sculpture.rotation.set(
    reducedMotion.matches ? -0.18 : mix(-0.18, 0.51, tilt) - 0.4 * unwind,
    0.36 + 3.6 * motion,
    reducedMotion.matches ? -0.19 : -0.19 + 0.42 * tilt - 0.7 * unwind,
  );
  const dramaticZoom = reducedMotion.matches
    ? 1
    : 1 + 0.72 * Math.sin(Math.PI * smooth(0.23, 0.53, p));
  const scale =
    dramaticZoom *
    mix(1, 0.83, smooth(0.67, 1, p)) *
    (window.innerWidth < 680 ? 0.65 : 1);
  sculpture.scale.setScalar(scale);
  sculpture.position.set(
    window.innerWidth < 680
      ? 0.4 + 0.15 * tilt - 0.5 * unwind
      : mix(2.12, 2.65, tilt) - 0.4 * unwind,
    window.innerWidth < 680 ? 1.85 : -0.12 + 0.38 * Math.sin(p * Math.PI * 2),
    0,
  );
  core.rotation.z = 0.28 * motion;
  ringA.rotation.y = 0.59 + 2.7 * motion;
  ringB.rotation.x = -0.6 + 2.2 * motion;
  ringMaterial.opacity = 0.8 - 0.22 * smooth(0.65, 0.85, p);
  satellites[0].position.x = -3 + 0.9 * p;
  gold.color
    .set("#d49b4b")
    .lerp(new THREE.Color("#f0bc70"), toBlue * (1 - toWarm));
  if (renderer) renderer.render(scene, camera);
}

function update(p) {
  currentProgress = p;
  const first = 1 - smooth(0.26, 0.36, p);
  const second = smooth(0.31, 0.43, p) * (1 - smooth(0.62, 0.72, p));
  const third = smooth(0.68, 0.8, p);
  const opacities = [first, second, third];
  const chapter = p < 0.37 ? 0 : p < 0.7 ? 1 : 2;
  chapters.forEach((element, i) => {
    element.style.opacity = opacities[i];
    element.style.transform = `translate3d(0, ${mix(30, 0, opacities[i])}px, 0)`;
    element.style.pointerEvents = i === chapter ? "auto" : "none";
    element.setAttribute("aria-hidden", i === chapter ? "false" : "true");
  });
  navButtons.forEach((button, i) =>
    button.classList.toggle("is-current", i === chapter),
  );
  progressBar.style.transform = `scaleX(${p})`;
  document.querySelector(".stage-time").textContent = `0${chapter + 1} : 03`;
  document.querySelector(".scroll-hint").style.opacity =
    1 - smooth(0.025, 0.15, p);
  draw(p);
}

let currentProgress = 0;
resize();
update(0);
window.addEventListener("resize", resize);

const trigger = ScrollTrigger.create({
  trigger: ".story",
  start: "top top",
  end: () => `+=${window.innerHeight * (reducedMotion.matches ? 2.5 : 4)}`,
  pin: ".stage",
  anticipatePin: 1,
  invalidateOnRefresh: true,
  onUpdate: (self) => update(self.progress),
  onRefresh: (self) => update(self.progress),
});

navButtons.forEach((button) =>
  button.addEventListener("click", () => {
    const positions = [0, 0.52, 0.94];
    const position = positions[Number(button.dataset.go)];
    const y = trigger.start + (trigger.end - trigger.start) * position;
    window.scrollTo({
      top: y,
      behavior: reducedMotion.matches ? "instant" : "smooth",
    });
  }),
);

reducedMotion.addEventListener("change", () => ScrollTrigger.refresh());

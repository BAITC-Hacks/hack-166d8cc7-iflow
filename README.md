# IFlow — financial intelligence in motion

An interactive frontend concept for a finance hackathon track, aimed at bank teams and analysts. The product messaging is provisional while the team defines its idea.

## Run locally

```bash
npm install
npm run dev
```

Open the local address printed by Vite. Build with `npm run build`.

## How the animation works

- Three.js renders an original, procedural 3D sculpture. No video or external image assets are required.
- GSAP ScrollTrigger pins the main scene and maps scroll progress to object position, rotation, scale, background color, chapter text, and the progress bar.
- Scene changes are derived from scroll progress, so moving backward restores the corresponding state. Chapter buttons jump to their scenes.
- A CSS visual remains if WebGL is unavailable. The layout supports mobile screens and reduced motion preferences.

## Project status

This is a frontend prototype, not a working banking analytics product. It has no backend, data connection, Gemini API calls, or API keys. Define the financial problem and approved data sources before adding those integrations. Keep any future API key on a server, outside browser code.

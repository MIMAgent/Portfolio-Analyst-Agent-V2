# Production dashboard

This is the repository's only frontend application and the source deployed by
Netlify. The root `netlify.toml` sets this directory as the build base.

## Commands

```powershell
npm ci
npm run build
npm run dev
```

## Fund data

The fund registry is `src/data/funds/index.js`. Each fund directory contains its
review, evidence, packet, manifest, and factor-risk files. Shared signal history
is `src/data/signalHistory.json`.

Add or update funds through that registry. Do not create a second frontend.

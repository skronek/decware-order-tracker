# Decware Order Tracker frontend

React SPA (Create React App, MUI, React Router) for the Decware Order Tracker. Django serves the
production build; see the repo root `CLAUDE.md` for how it's deployed.

Coding standards and project layout are in [`CLAUDE.md`](CLAUDE.md).

```bash
npm start                                          # dev server on :3000, proxies /api to Django on :8000
CI=true npx react-scripts test --watchAll=false    # run the tests once
npm run build                                      # production build in build/
```

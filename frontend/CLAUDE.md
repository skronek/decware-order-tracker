# Frontend

React 18 SPA (Create React App, JavaScript, MUI 7, React Router 6). Served by Django in production. In dev, `npm start` proxies API calls to `localhost:8000`.

## Standard: Bulletproof React

Follow the architecture and conventions of **Bulletproof React**: https://github.com/alan2207/bulletproof-react (see its `docs/`). The existing code was written before this standard was adopted. New code follows it. When you touch existing code, move it toward the standard incrementally, and don't do repo-wide rewrites unless asked.

### Project structure

Target layout under `src/` (create folders only when needed):

```
src/
  app/          # app shell: App.js, providers (theme, router, ErrorBoundary), routes/
  assets/
  components/   # shared, feature-agnostic UI (layout, LoadingSpinner, ErrorBoundary)
  config/       # env/config values
  features/     # one folder per domain feature, e.g. orders/, search/
    <feature>/
      api/        # request functions + hooks for this feature
      components/
      hooks/
      utils/
  hooks/        # shared hooks
  lib/          # preconfigured libraries (the single API client lives here)
  testing/      # test utils, MSW handlers/server
  utils/        # shared pure helpers
```

### Rules

- **Unidirectional imports:** shared (`components`, `hooks`, `lib`, `utils`) → `features` → `app`. Shared code never imports from features or app.
- **No cross-feature imports.** Compose features at the `app/routes` level instead.
- **Feature-scoped code stays in its feature.** Only promote something to a shared folder when a second feature needs it.
- **One API client.** All HTTP goes through one configured instance in `lib/`. Each endpoint gets a request function and a hook in its feature's `api/` folder. Components never call `axios`/`fetch` directly.
- **State by kind:** component state → `useState`/`useReducer`; server data → the feature's API hooks; URL state → React Router search params. Don't add a global store unless genuinely needed.
- **Components:** small and colocated. Avoid nested render functions. Keep prop lists short. Wrap MUI patterns you repeat in shared components.
- **Error handling:** handle API errors centrally in the client (interceptor). Put error boundaries around route-level sections, not only around the whole app.
- **Performance:** lazy-load routes (`React.lazy`) as pages grow.
- **Naming:** kebab-case for new files and folders (e.g. `order-details.js`). Existing PascalCase files get renamed when they move into the new structure.
- **Testing:** prefer integration tests with Testing Library and MSW over mocking hooks. Test behaviour users see.

### Current state vs. standard (known debt)

- All HTTP goes through `lib/api-client.js` (`baseURL: '/api'`). Request functions live in `features/orders/api/`. The hooks that use them (`hooks/useApi.js`, `hooks/useOrderDetails.js`) haven't moved into the feature yet.
- `src/mocks/` (MSW) uses the v1 `rest` API with MSW v2 installed, mocks a nonexistent `/orders/search/` endpoint, and isn't loaded by `setupTests.js`. It's dead until it's rewritten.
- Code is organized by type (`components/`, `hooks/`, `pages/`), not by feature.
- Bulletproof React uses TypeScript, ESLint import-boundary rules, and `@/` path aliases. None of these are set up here. Don't introduce them unless asked.

## Testing

```bash
CI=true npx react-scripts test --watchAll=false   # all tests, no watch mode
```

- `setupTests.js` mocks axios globally, `matchMedia` and `MutationObserver`. `src/__mocks__/` mocks `react-router-dom` and `@mui/x-data-grid`.
- Because axios is mocked globally, `axios.get` in a test is the API client's `get`. In component and page tests, mock the feature request function (e.g. `jest.mock('../../features/orders/api/get-order')`) rather than axios.

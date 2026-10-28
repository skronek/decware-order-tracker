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

- All HTTP goes through `lib/api-client.js` (`baseURL: '/api'`). Its response interceptor rewrites `error.message` to something fit to show (404 → "Order not found.", otherwise DRF's `detail`), so callers just display `error.message`. Request functions and `use-order-details.js` live in `features/orders/api/`. The generic `hooks/useApi.js` stays shared.
- Code is still mostly organized by type (`components/`, `pages/`). `OrderDetails` has moved to `features/orders/components/order-details.js`; the other order components (`SearchResults`, `order-summary`, …) belong there too when they next move.
- Shared building blocks: `components/common/LoadingSpinner` for loading states, `utils/orderFormat.js` (`formatDate` and the status/estimate labels), `utils/storage.js` for saved order IDs (always strings). The grey button is the theme's `secondary` color (`color="secondary"`).
- Bulletproof React uses TypeScript, ESLint import-boundary rules, and `@/` path aliases. None of these are set up here. Don't introduce them unless asked.
- MSW isn't installed. The old unused `src/mocks/` handlers were deleted; add MSW back (v2 API, in `src/testing/`) when tests are moved over to it.

## Testing

```bash
CI=true npx react-scripts test --watchAll=false   # all tests, no watch mode
```

- `setupTests.js` mocks axios globally (including `interceptors`), `matchMedia` and `MutationObserver`. `src/__mocks__/react-router-dom.js` replaces the router in every test; tests that need real routing (`MemoryRouter`, `useParams`) call `jest.unmock('react-router-dom')`.
- Because axios is mocked globally, `axios.get` in a test is the API client's `get`. In component, hook and page tests, mock the feature request function (e.g. `jest.mock('../../features/orders/api/get-order')`) rather than axios or the hooks. To simulate a failed request, reject with an `Error` carrying the message the interceptor would set (and `response.status` if the code checks it).
- Use the real `localStorage` (cleared in `beforeEach`) instead of mocking `utils/storage`.

# Task: Migrate three screens of a real GWT application to Angular

The attached `gwt/` sources are from a real open-source GWT 2.7 application:
the GWTP "carstore" sample (ArcBees/GWTP-Samples), built with GWTP
(Model-View-Presenter), UiBinder (`*.ui.xml`) and CellTable. Migrate these
three screens to an **Angular 18** single-page app, keeping their behavior:

1. **Manufacturers** (`client/application/manufacturer/`): the manufacturer
   table with Edit and Delete per row, and the create/edit popup
   (`manufacturer/ui/EditManufacturer*`) with Save and Close.
2. **Ratings** (`client/application/rating/`): the rating table with Delete
   per row, and the create form (`rating/ui/EditRating*`): pick a car, enter a
   rating, Save.
3. **Reports** (`client/application/report/`): the average rating per
   manufacturer.

plus the parts of the shell they need: the header menubar used to move between
screens (`widget/header/`) and the success/error messages
(`widget/message/`).

Out of scope: login/logout (the REST API is not protected), the cars and stats
screens, the mobile and tablet views, the detail pages.

## The backend stays as it is

The Angular app is served at `/ng/` by the same server as the GWT app and calls
its existing JSON REST API at `/api` (same origin, no CORS). The contract is in
`gwt/.../shared/api/*.java` (JAX-RS resources: paths in `ApiPaths`, parameters
in `ApiParameters`) and `gwt/.../shared/dto/*.java` (the JSON bodies, Jackson
field names = Java bean properties). Do not invent endpoints.

## Acceptance criteria (this is how your work is checked)

1. `ng build` succeeds in the fixed workspace (`workspace/`: Angular 18.2,
   standalone components, TypeScript strict mode). No other npm packages are
   available and there is no network access during the build.
2. The app's existing end-to-end scenarios pass against your Angular app with
   the selectors unchanged. They are in `e2e/`: the Cucumber features
   (`Manufacturers.feature`, `Ratings.feature`, `Reports.feature`), their step
   definitions and the Selenium page objects that show exactly how elements are
   found. In short, keep:
   - the GWT debug ids as element ids: GWT renders `debugId="X"` as
     `id="gwt-debug-X"` (see `client/debug/DebugIds.java`), e.g.
     `id="gwt-debug-manufacturers"` on the manufacturer table and
     `id="gwt-debug-successMessage"` on a success message;
   - tables as `<table>` with `<thead>` header cells named like the GWT
     columns, rows in the first `<tbody>`, and the Edit / Delete buttons as the
     last two columns where the GWT table has them;
   - the menubar (`id="gwt-debug-menubar"`) with links whose `href` contains
     the GWT history tokens (`manufacturer`, `rating`, `report`, see
     `NameTokens.java`); use hash-based routing;
   - a `window.confirm()` before a delete, as the GWT app does.

## Workspace and output format

Write the app under `src/app/`. The fixed `src/main.ts` bootstraps
`AppComponent` from `src/app/app.component.ts` and `appConfig` from
`src/app/app.config.ts`, so both must exist. `package.json`, `angular.json`,
`tsconfig*.json`, `src/main.ts` and `src/index.html` are fixed (changes are
discarded); you may add global CSS to `src/styles.css`.

Paths are relative to the workspace root (`src/app/...`). Emit each new file
whole:

````
### FILE: src/app/app.component.ts
```ts
...full file content...
```
````

To change an existing file (only `src/styles.css` exists in `src/` besides the
fixed files), you may also use `### EDIT: <path>` with SEARCH/REPLACE blocks:

````
### EDIT: src/styles.css
```css
<<<<<<< SEARCH
exact existing lines
=======
replacement lines
>>>>>>> REPLACE
```
````

Do not add commentary outside these blocks.

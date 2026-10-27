# Repository: mohitsaxena27/ai_sdlc

## Folder: backend

### backend/proxy.js

`backend/proxy.js` is the main Express application server setup. It initializes and configures an HTTPS server that acts as a proxy between the frontend and various backend services, handling security, CORS, request parsing, logging, routing, and error handling.

Important components:
- **Security middleware**: Helmet configuration, disabled `X-Powered-By`/etag, and custom security headers such as `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, and cache-control headers.
- **CORS setup**: Allows the configured frontend origin with credentials and common HTTP methods/headers.
- **Parsing middleware**: Compression, JSON/urlencoded body parsing up to 100MB, and cookie parsing.
- **Debug logging middleware**: Logs request method, path, status, duration, user/session info, IP, origin, and error details.
- **Global error handler**: Handles payload-too-large errors and CORS errors.
- **Proxy route**: `/sakverse/unite-login` proxies to `http://unite.report.com:8080` with path rewrite to `/ui/`.
- **Route registrations**: Mounts auth, business, project, admin, upload, automation, TDM, data, and suite routes under `/sakverse/*`.
- **HTTPS server**: Reads SSL key/certificate files and starts the server on configured host/port.
- **WebSocket integration**: Attaches a stream server to the HTTPS server.

In relation to the overall project, this file appears to be the central backend entry point that exposes the application’s API routes and proxy endpoints to the frontend while applying shared security, session-aware logging, and transport configuration.


## Folder: backend/config

### backend/config/apiConfig.js

This file loads environment variables with `dotenv` and exports a `config` object containing backend/server settings and integration settings.

Important components:
- `HOST`, `PORT` (defaults to `3000`), `BASE_IP`, and `JAVA_IP`
- `JIRA_CONFIG` with `USERNAME`, `PASSWORD`, and `URL` from Jira-related environment variables
- `FRONTEND.URL`, built as `https://${HOST}:${FRONTEND_PORT}`
- `CORS` settings, including origin, credentials, allowed methods, and allowed headers

It likely serves as a central configuration module for the backend, providing environment-driven values for server startup, frontend communication, CORS, and Jira integration.


## Folder: backend/controllers

### backend/controllers/UploadController.js

This file is a backend controller for file-system operations. It uses Node’s `fs` and `path`, `multer` for multipart uploads, and `dotenv` to read `process.env.PATH` as `BASE_PATH`.

Important components:
- `BASE_PATH`: root directory for all operations, from the `PATH` environment variable.
- `formatDate`: formats file modification timestamps.
- `getDirectoryStructure`: recursively builds a folder/file tree, but only includes folders whose names end with `Documents`; files are included with name, size, and last modified time.
- `getFolderStructure`: reads entries directly under `BASE_PATH` and returns the filtered recursive structure.
- `createFileOrFolder`: creates a file or folder under `BASE_PATH/:folderName` using `relativePath`, `isFolder`, and optional `content`.
- `deleteFileOrFolder`: deletes a file or folder under `BASE_PATH/:folderName` using `relativePath`.
- `upload` / `uploadFiles`: configures `multer` to store uploaded files under `BASE_PATH/:folderName` using original filenames, then returns upload metadata.

Relation to the overall project: it likely serves as the file-management API layer for a larger application, exposing operations for browsing, creating, deleting, and uploading files within a configured base directory. The provided content does not show route registration, authentication, or how these functions are connected to the rest of the app.

### backend/controllers/adminController.js

This file is a backend controller module for admin-related operations.

**What it does**
- `projectOnboarding`: accepts multipart form uploads via Multer, validates that either JSON `data` or files are present, builds a `FormData` payload, forwards it to the Java backend at `${JAVA_IP}/api/admin/projectOnboarding` with the session bearer token, cleans up temporary uploaded files, and returns the Java response’s `request_id`.
- `GetProjectList`: makes a GET request to a hardcoded mock Postman endpoint (`/project`) and returns its data.
- `GetUserList`: makes a GET request to a hardcoded mock Postman endpoint (`/user`) and returns its data.

**Important components**
- `multer` upload middleware configured for multiple files under field name `files` into `uploads/`.
- `FormData` construction for forwarding JSON and file streams.
- `axios` HTTP calls to external services.
- `req.session` used for authentication token in onboarding.
- File cleanup with `fs.unlinkSync` after success or failure.

**Relation to overall project**
- It appears to be part of the backend API/controller layer, handling admin project onboarding and providing project/user list endpoints. The onboarding flow proxies to a Java backend, while the list endpoints currently use mock URLs.

### backend/controllers/authController.js

This file is a Node.js/Express authentication controller that mediates login, logout, and session validation between the frontend and a Java backend.

Important components:
- `loginUser`: validates required credentials, decodes the base64-encoded password, authenticates against `${JAVA_IP}/api/auth/login`, fetches allowed projects, creates an in-memory session via `setSession`, sets an `httpOnly`, `secure`, `sameSite: 'None'` `sessionId` cookie, and returns `displayName` and `allowedProjects`.
- `logoutUser`: reads the `sessionId` cookie, removes the session with `deleteSession`, clears the cookie, and returns a success message.
- `checkAuth`: verifies the session exists and is not expired, decodes the stored JWT to extract `roles`, fetches assigned projects from the Java backend, and returns authentication status, role, display name, and allowed projects.
- Helper `generateSessionId`: creates a 64-character hex session ID using `crypto.randomBytes`.

Relation to overall project: it appears to be the backend authentication/session layer, relying on a Java authentication service for credentials and project assignments while maintaining server-side sessions and cookies for the client.

### backend/controllers/automationController.js

This file is a backend controller module for automation-related API operations. It exports Express-style async request handlers that validate inputs, call external automation services via `axios`, and return JSON/HTML responses.

Important components:

- **Environment/config**: reads `NGROK_URL` and `BASE_IP` from environment variables.
- **Session auth**: uses `req.session.token` as a Bearer token for proxied requests.
- **Test scenario retrieval**: `GetTestScenario` fetches test cases from `${baseIP}/get_update/` and returns the matching test case by ID.
- **Execution lifecycle proxies**: `ExecuteTest`, `CloneTest`, `AddstepsToTest`, `GetTestResult`, `DeletePlannedStep`, `MovePlannedStep`, `UpdatePlannedIntent`, and `UpdateExecutionStep` forward requests to `${NGROK_URL}` endpoints for creating, cloning, modifying, reordering, deleting, and retrieving test execution steps/results.
- **Suite execution/reporting**: `ExecuteSuiteParallel` and `OpenSuiteReport` call hardcoded `http://10.154.2.83:8000` endpoints.
- **Report generation**: `GenerateReport` validates that `req.body.results` exists, calls `generateExecutionHTML(payload)`, and returns an inline HTML report.

Relation to overall project: it appears to be the backend automation controller layer that bridges the application frontend/API to external test automation services and report generation, handling test scenario lookup, execution control, step management, and report output.

### backend/controllers/businessController.js

This file is a backend controller for business-analysis-related operations. It exports several request handlers that proxy or process business data:

- `GetIdea`: fetches an idea by ID from an external service using the session token.
- `PublishUserStory`: publishes a user story by sending `userstory_ref_id` and `project_id` to an external service.
- `UploadBAResource`: accepts text and/or uploaded files, forwards them as multipart form data to a BA resource endpoint, then cleans up temporary files.
- `getProcessedIdea`: fetches a processed idea by `pr_id`.
- `downloadFeature`: generates an Excel file from request body data using `generateExcel`.
- `downloadFeatureDoc`: generates a Word document from request body data using `generateWord`.

It uses `axios`, `multer`, `form-data`, `fs`, and helper functions from `../helper/BA/baHelper.js`. It likely sits in the backend API layer, connecting frontend requests to business-analysis services and file-generation utilities.


## Folder: backend/controllers

### backend/controllers/dataController.js

This file defines a backend controller that proxies a CSV generation request to an external data service.

- **What it does:** It exports `generateCsv`, an async Express-style handler that sends the incoming request body to `${DATAIP}/generate-csv` using Axios, forwarding the user’s session token as a Bearer token. It then returns the upstream response status and data, or an error response if the request fails.
- **Important components:** `axios` for HTTP requests, `dotenv` for environment loading, `dataIP` from `process.env.DATAIP`, and `generateCsv`, which uses `req.session.token` for authorization.
- **Project relation:** It appears to be part of a backend API layer that delegates CSV generation to a separate data service, acting as an authenticated intermediary between the client and that service.

### backend/controllers/projectController.js

This file is a backend controller module that exposes many async request handlers for project, user-story, test-case, JIRA, and ADO-related operations.

Important components:
- Environment-based API configuration: `baseIP`, `javaIP`, and JIRA credentials/URL.
- Session/auth handling: some handlers use `req.session`, while others read `sessionId` from cookies and call `getSession(sessionId)` to obtain a bearer token.
- External API proxying via `axios` to endpoints such as `/api/assigned-projects`, `/ticket_list/:pr_id`, `/get_list_user_story_details`, `/get_update/`, `/getDashBoard/`, `/download-excel`, `/process`, `/update_qna`, `/update_review_status`, `/update_userstory`, `/update_requirement`, `/update_testcase`, `/publish_testcase`, `/append_user_story`, `/fetch_configuration/:id`, `/fetch_testsuite/...`, `/fetch_testplans/...`, and `/process/v2`.
- File upload support in `us_submit_v2` using `multer` and `FormData`, including cleanup of uploaded files.
- Input validation and error responses for missing parameters/body fields.
- JIRA access in `jira` using Basic auth from environment variables.

Overall project relation: it appears to be the Node/Express controller layer that connects the frontend to downstream services (main API, Java service, JIRA, and ADO-related endpoints), centralizing project/user-story/test-case workflows and authenticated request forwarding.

### backend/controllers/sessionStore.js

This file implements an in-memory session store for the backend.

**What it does**
- Stores active sessions in a `Map` keyed by `sessionId`.
- Tracks which session belongs to which user in another `Map` keyed by `username`.
- Provides CRUD-style helpers: `getSession`, `setSession`, `deleteSession`, and `hasSession`.
- `setSession` enforces one active session per user by deleting a previous session for the same username when a new session ID is used.
- `cleanupExpiredSessions` removes sessions whose `expires` timestamp is in the past.
- Runs cleanup automatically every 15 minutes via `setInterval`.

**Important components**
- `sessions`: in-memory map of session ID to session data.
- `userToSession`: in-memory map of username to session ID.
- Exported functions for reading, creating/updating, deleting, and checking sessions.
- Periodic expired-session cleanup.

**Relation to overall project**
- It appears to be a backend controller/utility for managing user sessions in memory, likely used by other backend code that needs to create, look up, or remove sessions. The provided content does not show its callers or persistence layer.

### backend/controllers/suiteController.js

This file is a backend controller module for test-suite operations. It uses `axios` to proxy requests to an external suite API whose base URL comes from `NGROK_URL`, and it authenticates those requests with `req.session.token`.

Important components:
- `CreateSuite`: validates `project_id`, `suite_name`, and non-empty `items`, then POSTs the request body to `/test-suites`.
- `GetSuiteList`: validates `project_id`, then GETs `/test-suites`.
- `ExecuteSuite`: validates `suite_id` and optional `max_parallel` (1–6), then POSTs to `/execute-suite/{suite_id}`.
- `GetSuiteReportJson`: validates `suite_id`, optionally appends `screenshot_mode`, then GETs `/test-suites/{suite_id}/report/json`.
- A default export object containing all four functions.

In the overall project, this likely serves as the backend controller layer that connects the application’s routes/handlers to the external test-suite service. The provided file does not show routing, middleware, or how these exports are wired into the app.


## Folder: backend/controllers

### backend/controllers/tdmController.js

This file is a backend controller that acts as a proxy between the application’s Express routes and an external TDM service. It reads the TDM base URL from `TDMIP` and forwards authenticated requests using the user’s session token.

Important components:
- Repository operations: `getRepositories`, `createRepository`, `deleteRepository`
- Table operations: `getTableData`, `createTable`, `deleteTable`, `addTableColumn`
- Data record operations: `updateDataRecord`, `createDataRecord`, `deleteDataRecord`
- File/download operation: `downloadTable`, which streams an XLSX response
- Shared pattern: each handler uses `req.session.token` for `Authorization: Bearer ...`, calls the corresponding TDM endpoint, and returns the upstream response or a normalized error
- Multer upload middleware is configured as `upload` for `files`, though it is not used by the exported handlers shown

Overall project relation: it likely sits in the backend API layer, exposing repository/table/data management endpoints to the frontend while delegating persistence and business logic to the TDM service.


## Folder: backend/helper/Automation

### backend/helper/Automation/automationHelper.js

This file is a backend helper that exports `generateExecutionHTML(data)`, which builds a complete HTML test execution report from an execution result object.

Important components:
- Input handling: reads `data.results` (defaulting to an empty array).
- Grouping: groups result rows by `execution_id`, with unknown IDs grouped under `'unknown'`.
- Statistics: counts total, passed, failed, pending, skipped, and in-progress steps overall.
- Per-execution sections: sorts steps by `execution_order`, counts statuses, determines an overall execution status (`SUCCESS`, `FAILED`, `IN PROGRESS`, or `NOT FOUND`), and renders an accordion item.
- Step table rows: renders order, intent/step, step type, target, actual action, status badge, error/log box, and optional base64 screenshot toggle.
- Report layout: includes summary cards, styled accordion/table UI, responsive/print CSS, and small JavaScript for screenshot toggling and auto-opening accordions containing errors.
- Output: returns a full HTML document string.

Relation to the overall project: based on its path and footer text, it appears to support the automation/reporting side of the backend, likely converting automation execution results into a viewable HTML report. The provided file alone does not show where it is imported or how reports are stored/served.


## Folder: backend/helper/BA

### backend/helper/BA/baHelper.js

This file is a backend helper that generates two formatted business-analysis deliverables from a structured `data` object: an Excel workbook and a Word document.

**What it does**
- `generateExcel(data)` builds an ExcelJS workbook with:
  - an **Overview** sheet (project ID, executive summary, parsed business objectives)
  - a **Features Summary** sheet (feature IDs, core features, story counts)
  - one sheet per feature (`F{id}`) containing implementation approach, user stories, prerequisites/actions/test data, and acceptance criteria
- `generateWord(data)` builds a `docx` document with equivalent sections: overview, features summary, and per-feature details, including page breaks between features.

**Important components**
- `COLORS` and `excelStyles` / `wordStyles`: shared styling helpers for fonts, fills, borders, rows, banners, and tables.
- Excel sheet builders: `createExcelOverviewSheet`, `createExcelSummarySheet`, `createExcelFeatureSheet`.
- Word section builders: `buildWordOverviewSection`, `buildWordSummarySection`, `buildWordFeatureSection`.
- Exported entry points: `generateExcel` and `generateWord`.

**Likely relation to the overall project**
- It appears to be a document-generation utility in the backend, probably called by a BA-related route/service to produce downloadable Excel/Word project documentation from analyzed feature/story data. The expected input shape includes fields such as `id`, `executive_summary`, `business_objectives`, and `feature_breackdown`.


## Folder: backend/middleware

### backend/middleware/authMiddleware.js

This file defines an Express authentication middleware named `verifySession`.

- **What it does:** It checks whether a request has a valid, non-expired session. It reads `sessionId` from `req.cookies`, verifies the session exists via `hasSession`, retrieves it with `getSession`, checks `session.expires` against the current time, deletes expired sessions with `deleteSession`, and attaches the session to `req.session` before calling `next()`. If no session exists or it is expired, it returns a `401` response.
- **Important components:** `verifySession`, imports from `../controllers/sessionStore.js` (`getSession`, `hasSession`, `deleteSession`), cookie-based `sessionId`, expiration check, and `req.session` attachment.
- **Project relation:** It is intended for protecting routes by validating active user sessions before allowing access to downstream middleware or handlers.

### backend/middleware/checkProjectAccess.js

This file defines Express middleware for session and project-level authorization.

Important components:
- `checkProjectAccess`: reads `sessionId` from cookies, validates it with `hasSession`, retrieves session data, extracts `projectId` from `req.params.projectId`, `req.query.pr_id`, or `req.body.pr_id`, verifies `session.allowedProjects` is an array, compares project IDs as strings, attaches the session to `req.session`, and calls `next()` if allowed; otherwise returns 401/400/403.
- `checkSession`: reads and validates `sessionId`, retrieves the session, attaches it to `req.session`, and calls `next()`; otherwise returns 401.
- Imports `setSession`, `deleteSession`, `getSession`, and `hasSession` from `../controllers/sessionStore.js`, though only `getSession` and `hasSession` are used here.

Relation to overall project: it likely protects backend routes by ensuring requests have a valid session and, for project-specific routes, that the user is assigned to the requested project.


## Folder: backend/routes

### backend/routes/UploadRoute.js

This file defines an Express router for upload/file-management endpoints.

Important components:
- `router`: an Express router instance.
- Imported controller functions: `getFolderStructure`, `createFileOrFolder`, `deleteFileOrFolder`, `uploadFiles`, and `upload`.
- Four routes:
  - `GET /folder-structure` → `getFolderStructure`
  - `POST /CreateFile/:folderName` → `createFileOrFolder`
  - `DELETE /DeleteFile/:folderName` → `deleteFileOrFolder`
  - `POST /UploadFiles/:folderName` → runs `upload` middleware, then `uploadFiles`

Relation to overall project: It appears to be a backend route module handling folder structure retrieval, file/folder creation and deletion, and file uploads under a specified folder. The provided content does not show where this router is mounted or how the controller functions are implemented.

### backend/routes/adminRoutes.js

This file defines an Express router for admin-related backend endpoints.

Important components:
- `router`: an Express `Router` instance.
- `verifySession`: middleware applied to `POST /project_onboarding`.
- Controller handlers imported from `../controllers/adminController.js`:
  - `projectOnboarding` for `POST /project_onboarding`
  - `GetProjectList` for `GET /projects`
  - `GetUserList` for `GET /user`
- Default export of the router for use elsewhere in the Express app.

Relation to the overall project: it groups admin route definitions and connects HTTP requests to authentication middleware and admin controller functions. The comment suggests `/project_onboarding` is intended as a streaming form-data proxy without multer or extra headers.

### backend/routes/authRoutes.js

This file defines an Express router for authentication-related HTTP routes.

Important components:
- `router`: an Express `Router` instance.
- Imported handlers: `loginUser`, `logoutUser`, `checkAuth` from `authController.js`; `getAssignedProjects` from `projectController.js`.
- Imported middleware: `verifySession` from `authMiddleware.js`.
- Route mappings:
  - `POST /login` → `loginUser`
  - `POST /logout` → `verifySession`, then `logoutUser`
  - `GET /check` → `checkAuth`, then `verifySession`
  - `GET /project` → `verifySession`, then `getAssignedProjects`
  - `GET /us_list` → `verifySession`, then `getAssignedProjects`

Relation to the overall project: it acts as part of the backend routing layer, connecting incoming HTTP requests to authentication and project-related controller functions and applying session verification middleware where specified. The provided content does not show where this router is mounted or the implementations of the imported functions.

### backend/routes/automationRoutes.js

This file defines an Express router for automation-related API endpoints. It imports `verifySession` from auth middleware and several controller functions from `automationController.js`, then maps HTTP methods and paths to those handlers. Most routes require session verification; `/generate-report` does not show `verifySession` in the provided content. It likely serves as the backend routing layer for test execution, scenario retrieval, step management, suite execution/reporting, cloning, and report generation within the larger application.

### backend/routes/businessRoutes.js

This file defines an Express router for business-related API endpoints.

Important components:
- `express.Router()` creates the router.
- `verifySession` middleware is applied to every route, indicating these endpoints require an authenticated session.
- Imported controller functions: `GetIdea`, `PublishUserStory`, `UploadBAResource`, `getProcessedIdea`, `downloadFeature`, and `downloadFeatureDoc`.
- Routes:
  - `GET /getUS/:id` → `GetIdea`
  - `POST /publishUS` → `PublishUserStory`
  - `POST /uploadBA` → `UploadBAResource` (comment notes multer is handled inside controller)
  - `GET /get_processed_idea/:pr_id` → `getProcessedIdea`
  - `POST /downloadFeature` → `downloadFeature`
  - `POST /downloadFeatureDoc` → `downloadFeatureDoc`
- The router is exported as the default export.

Relation to overall project: It appears to be a backend route module that exposes business functionality through HTTP endpoints, delegating request handling to `businessController.js` and protecting routes with session verification. The exact business logic is not shown in this file.


## Folder: backend/routes

### backend/routes/dataRoutes.js

This file defines an Express router for data-related routes. It imports `verifySession` middleware and the `generateCsv` controller function, then registers a protected `POST /generate_synthetic_data` endpoint that requires a valid session and invokes `generateCsv`. It likely connects the backend API to synthetic data generation functionality within the broader project.

### backend/routes/projectRoutes.js

This file defines an Express router for project-related API endpoints.

**What it does**
- Creates an `express.Router()`.
- Imports session/project-access middleware and controller functions.
- Registers HTTP routes (`GET`/`POST`) that map URL paths to controller handlers.
- Applies middleware such as `checkSession`, `verifySession`, and `checkProjectAccess` on many routes, though the exact middleware chain varies by route.
- Exports the router as the default export.

**Important components**
- `router`: the Express router instance.
- Middleware imports: `verifySession`, `checkProjectAccess`, `checkSession`.
- Controller imports: `US_List`, `Get_update`, `Download_Excel`, `us_submit`, `jira`, `updateQnA`, `acceptTestCase`, `updateUserStory`, `updateRequirement`, `updateTestCase`, `publishTestCase`, `requirement_List`, `getJiraDetails`, `publishUserStory`, `nextStep`, `Get_testcase`, `getTestConfiguration`, `Ado_fetch_testplans`, `Ado_fetch_testsuite`, `Ado_fetch_testdata`, `us_submit_v2`.
- Route definitions, including paths such as `/us_list`, `/Get_update`, `/Get_testcase`, `/requirement_list`, `/DownloadUserstory`, `/us_submit`, `/externalstories/:pr_id`, `/nextStep/:user_story_ref`, `/jira`, `/Accept_Testcase`, `/updateQueries`, `/update_us`, `/update_r`, `/update_tc`, `/publish`, `/appendUS`, `/TestConfigurations/:userstory_ref_id`, `/Ado_fetch_testplans/:userstory_ref_id`, `/Ado_fetch_testsuite/:userstory_ref_id/:plan_id`, `/Ado_fetch_testdata/:userstory_ref_id`, and `/us_submit_v2`.

**Relation to overall project**
- It serves as the backend routing layer for project-related operations, connecting incoming HTTP requests to the corresponding controller functions and middleware. Based only on the provided file, it appears to support user-story, requirement, test-case, Jira/ADO-related, and publishing workflows.

### backend/routes/suiteRoutes.js

This file defines an Express router for test-suite-related API endpoints.

Important components:
- `express.Router()` creates the router.
- `verifySession` middleware is applied to all routes, indicating they require an authenticated session.
- Imported controller functions: `CreateSuite`, `GetSuiteList`, `ExecuteSuite`, and `GetSuiteReportJson`.
- Four routes:
  - `POST /test-suites` → `CreateSuite`
  - `GET /test-suites` → `GetSuiteList`
  - `POST /execute-suite/:suite_id` → `ExecuteSuite`
  - `GET /test-suites/:suite_id/report/json` → `GetSuiteReportJson`

Relation to overall project: It appears to be part of the backend routing layer, exposing authenticated endpoints for creating, listing, executing test suites, and retrieving a suite report in JSON format. The actual business logic is delegated to `suiteController.js`, which is not shown here.

### backend/routes/tdmRoutes.js

This file defines an Express router for TDM-related backend API endpoints.

**What it does**
- Creates an Express `router`.
- Imports controller functions from `../controllers/tdmController.js`.
- Applies `verifySession` middleware to every route, so all endpoints require a valid session.
- Maps HTTP methods and paths to controller functions for repository, table, data record, and download operations.

**Important components**
- `router`: the Express router exported as default.
- `verifySession`: authentication/session middleware applied to all routes.
- Imported controller functions: `getRepositories`, `createRepository`, `deleteRepository`, `getTableData`, `createTable`, `deleteTable`, `updateDataRecord`, `createDataRecord`, `deleteDataRecord`, `addTableColumn`, and `downloadTable`.
- Route groups:
  - Repositories: `GET /repositories`, `POST /createrepository`, `DELETE /deleteRepository/:repoId`
  - Tables: `GET /tabledata/:tableId`, `POST /createtable`, `DELETE /deleteTable/:tableId`
  - Data records: `PATCH /repository/:repoName/table/:tableName/row/:rowNumber/column/:columnName`, `POST /createdatarecord`, `DELETE /deleteDataRecord/:dataId`, `PATCH /table/:tableId/columns`
  - Downloads: `GET /download/:tableId`

**Relation to overall project**
- It is part of the backend routing layer.
- It exposes protected TDM API endpoints and delegates request handling to `tdmController.js`.
- It likely connects frontend or other clients to backend logic for managing repositories, tables, records, columns, and table downloads.


## Folder: work-main

### work-main/axios.js

This file creates and exports a configured Axios instance (`api`) for making HTTP requests.

Important components:
- `axios.create(...)` instance with:
  - `baseURL` set twice (`${config.JavaIP}/api` then `${config.BaseIP}/api`; the later value overrides the earlier one)
  - `withCredentials: true` to send cookies with requests
  - default `Content-Type: application/json`
- A response interceptor that:
  - returns successful responses unchanged
  - on errors, clears `localStorage` if the response status is `401`
  - rejects the error so callers can handle it
- `useNavigate` is imported from `react-router-dom` but not used in the shown code.

Relation to the overall project: It likely serves as the shared HTTP client for the frontend, centralizing API base URL, cookie-based credentials, JSON content type, and basic 401 handling. The unused `useNavigate` import suggests possible intended navigation on unauthorized responses, but the current code only clears local storage.

### work-main/postcss.config.js

This file is a PostCSS configuration file. It exports a default configuration object that enables two PostCSS plugins: `tailwindcss` and `autoprefixer`.

Important components:
- `export default { ... }`: the default configuration object consumed by PostCSS.
- `plugins`: the section listing PostCSS plugins to run.
- `tailwindcss: {}`: enables the Tailwind CSS plugin with default/empty options.
- `autoprefixer: {}`: enables the Autoprefixer plugin with default/empty options.

Relation to the overall project: based only on this file, it indicates the project’s CSS processing pipeline uses PostCSS with Tailwind CSS and Autoprefixer. The exact project structure, build tool, or usage beyond that is not shown in the provided content.

### work-main/tailwind.config.js

This file configures Tailwind CSS for the project.

- **What it does:** Enables class-based dark mode, tells Tailwind which files to scan for class usage (`index.html` and `src/**/*.{js,ts,jsx,tsx}`), and extends the default theme with custom color tokens.
- **Important components:** The `brand` colors (primary/accent variants) and the `ui` color system, which includes paired light/dark values for background, surface, navbar, border, text, and muted colors.
- **Project relation:** It likely supports a React/Vite-style frontend using Tailwind utility classes, with consistent branding and light/dark UI theming controlled by a `dark` class.

### work-main/vite.config.js

This file configures the Vite development server for a React application.

Important components:
- Loads environment variables with `loadEnv`, including `VITE_API_URL`, `VITE_BACKEND_PORT`, `VITE_FRONTEND_PORT` (default `5175`), and `VITE_HOST` (default `localhost`).
- Enables the React plugin via `@vitejs/plugin-react`.
- Configures HTTPS using local certificate files from `./certs/private.key` and `./certs/certificate.crt`.
- Binds the dev server to `0.0.0.0` on the configured frontend port.
- Configures HMR over `wss` using the public host and frontend port.
- Proxies `/sakverse` and `/view` requests to the backend at `${API_URL}:${BACKEND_PORT}`, with `changeOrigin: true`, `secure: false`, and WebSocket support enabled for `/view`.

Relation to the overall project: it sets up the frontend development server and routes selected API/WebSocket paths to a backend service, indicating a frontend-backend split architecture during development.


## Folder: work-main/src

### work-main/src/App.jsx

This file is the main React application component (`App`). It:

- Reads authentication state from `useAuthContext`, including `isAuthenticated`, `authInfo`, and `authLoading`.
- Shows a loading message while auth state is loading.
- Wraps the app in an `ErrorBoundary` with a fallback UI for errors.
- Renders different top-level views based on authentication and role:
  - `Login` if not authenticated
  - `AdminDashboard` if `authInfo.role === 1`
  - `Automation` if `authInfo.role === 3`
  - `BusinessDashboard` if `authInfo.role === 5`
  - Otherwise `PageContent`, passing `Role={authInfo?.role}`
- Imports `Navbar`, `Sidebar`, and `useLocation`, though the shown code does not visibly use `Navbar`, `Sidebar`, or `location` in the returned JSX.

It likely serves as the central entry point that routes users to role-specific dashboards or general page content after authentication.

### work-main/src/PrivateRoute.jsx

This file defines a React component named `PrivateRoute` that protects routes.

- **What it does:** It checks authentication state from `useAuth()`. While `loading` is true, it renders a loading message. If `isAuthenticated` is true, it renders its `children`; otherwise, it redirects to `/login` using `Navigate`, replacing the current history entry and passing the current location in route state.
- **Important components/imports:** `React`, `Navigate` and `useLocation` from `react-router-dom`, and `useAuth` from `../Hooks/authUse`.
- **Project relation:** It likely acts as a wrapper around protected pages/routes, using the app’s authentication hook and React Router navigation to restrict access to authenticated users.

### work-main/src/main.jsx

This file is the React entry point. It creates a root on the DOM element with id `"root"` and renders the application wrapped in routing, error handling, and authentication context.

Important components/elements:
- `BrowserRouter` from `react-router-dom`: provides client-side routing.
- `ErrorBoundary` from `react-error-boundary`: catches rendering errors and shows `ErrorPage` as fallback.
- `AuthProvider` from `./Hooks/Auth/AuthContext.jsx`: wraps the app with authentication context.
- `App` from `./App.jsx`: the main application component.
- `ErrorPage` from `./Components/Error/index.jsx`: fallback UI for errors.
- `./index.css`: global styles.

Relation to overall project: It bootstraps the React app and establishes top-level providers (routing, auth, error boundary) around `App`, so the rest of the application runs within those contexts.


## Folder: work-main/src/Admin

### work-main/src/Admin/api.js

This file is an Admin API helper module, but in its current state it mostly contains commented-out code and unused constants.

**What it does**
- Imports `axios`.
- Reads two Vite environment variables: `VITE_API_URL` and `VITE_BACKEND_PORT`.
- Defines `API_BASE` as an empty string.
- Defines `BASE_URL` as `/sakverse/admin`.
- Contains commented-out `fetchProjects` and `fetchUsers` implementations, so no active API functions are currently exported or executed.

**Important components**
- `axios` import.
- `APIURL` and `PORT` environment-based constants.
- `API_BASE` constant.
- `BASE_URL` constant set to `/sakverse/admin`.
- Commented-out fetch helpers for projects and users.

**Relation to overall project**
- It appears intended to support Admin-related API calls, likely under a `/sakverse/admin` path, but the provided content does not show active usage or exports, so its current functional role in the project cannot be confirmed from this file alone.

### work-main/src/Admin/index.jsx

This file defines the `Admin` React component, which serves as an admin section layout and router.

- It uses `useState` to track whether the sidebar is open.
- It renders a `Navbar` and a `Sidebar`, plus a routed content area using `Routes`/`Route` from `react-router-dom`.
- It imports and maps several admin pages: `Projects`, `ProjectOnboarding`, `ProjectDetails`, `Users`, `Audit`, and `Directory`.
- Unknown routes redirect to `/Admin/Projects`.
- It also imports `useLogout`, though the provided snippet does not show it being called in the returned JSX.

In the overall project, this appears to be the admin dashboard shell that organizes navigation and page routing for administrative features such as projects, users, audit logs, and directory.


## Folder: work-main/src/Admin/Components

### work-main/src/Admin/Components/Adminlayout.jsx

This file defines an `AdminLayout` React component that renders the admin page shell.

- It uses `useState` to track whether the sidebar is open.
- It renders `Sidebar`, passing `isOpen` and a `closeSidebar` callback.
- It renders `Navbar`, passing a `toggleSidebar` callback.
- It renders a `main` area containing React Router’s `Outlet`, where nested admin route content appears.
- The layout uses Tailwind-style classes for a dark background and responsive left margin.

It likely serves as the shared layout for admin routes, with `Sidebar` and `Navbar` as persistent navigation UI and `Outlet` displaying the active admin page.

### work-main/src/Admin/Components/Content.jsx

Based on the provided file, all code is commented out, so the file currently does not execute any component.

What it appears intended to do:
- Define a `Content` component that renders a `<main>` container.
- Inside it, use React Router `Routes`/`Route` to map admin paths to page components:
  - `/Admin` → `Dashboard`
  - `/Admin/Users` → `Users`
  - `/Admin/Onboarding` → `Onboarding`
  - `/Admin/Projects` → `Projects`
  - `/Admin/Audit` → `Audit`
  - `/Admin/Directory` → `Directory`
- Redirect unknown `/Admin/*` paths to `/Admin` using `Navigate`.

Important components/symbols referenced:
- `Content` (default export, commented)
- `Routes`, `Route`, `Navigate` from `react-router-dom`
- Page components: `Dashboard`, `Users`, `Projects`, `Audit`, `Onboarding`, `Directory`

Relation to overall project:
- It appears intended to be the admin content/routing area, rendering different admin pages based on URL.
- Because everything is commented out, it is not currently active in the application.

### work-main/src/Admin/Components/Navbar.jsx

This file defines an admin `Navbar` React component.

- **What it does:** It renders a sticky top navigation bar with a mobile sidebar toggle button and a profile icon. Clicking the profile icon toggles a logout dropdown, which auto-closes after 5 seconds unless hovered. The dropdown contains a “Logout” button that calls the `logout` function from `useLogout`.
- **Important parts:** `Navbar` component, `toggleSidebar` prop, `showLogout` state, `logoutTimeoutRef`, `handleProfileClick`, `handleMouseEnter`, `handleMouseLeave`, and the logout dropdown.
- **Project relation:** It appears to be part of an admin dashboard UI, providing top-level navigation controls (mobile sidebar toggle and logout) for the admin area.

### work-main/src/Admin/Components/Sidebar.jsx

This file defines a React `Sidebar` component for an admin interface.

- **What it does:** It renders a fixed left sidebar with a “Sakverse Admin” title and navigation links. It accepts `isOpen` and `closeSidebar` props to control mobile visibility, including a mobile-only close button. On medium screens and above, it remains visible.
- **Important components/elements:** The default-exported `Sidebar` component; `NavLink` entries for `/Admin/Projects` and `/Admin/Users`; FontAwesome icons for those links; commented-out `NavLink` entries for other possible admin pages.
- **Relation to overall project:** It appears to be the navigation sidebar for the admin area, providing access to at least the Projects and Users admin pages. The commented links suggest additional admin sections may have been planned or are currently disabled.


## Folder: work-main/src/Admin/Components/UI

### work-main/src/Admin/Components/UI/Chart.tsx

This file defines a React functional component named `Chart` that renders a simple bar chart using mock data.

Important parts:
- `data` and `labels` arrays provide seven values and weekday labels.
- `maxValue` normalizes bar heights.
- The component maps over `data` to render vertical bars with gradient styling and hover opacity.
- It includes weekday labels under each bar and a legend labeled “Daily Visits.”

Relation to the overall project: Based on its path (`work-main/src/Admin/Components/UI/Chart.tsx`), it appears to be a reusable UI component for an admin area, likely used to display a simple daily visits chart. The provided content does not show where it is imported or used.

### work-main/src/Admin/Components/UI/HealthStatus.tsx

This file defines a React component named `HealthStatus` that renders a “System Health” card. It accepts a `services` prop, where each service has a `name`, `status` (`healthy`, `warning`, or `error`), and `uptime`. For each service, it displays a status icon and colored status label plus uptime.

Important parts:
- `HealthStatus` component (default export)
- `Service` and `HealthStatusProps` interfaces
- `getStatusIcon` and `getStatusColor` helper functions for mapping status values to icons/colors

Based on its path (`work-main/src/Admin/Components/UI/HealthStatus.tsx`), it appears to be an admin UI component likely used to show the health status of system services in an admin dashboard.

### work-main/src/Admin/Components/UI/StatCard.tsx

This file defines a reusable React component named `StatCard` for displaying a statistic card in an admin UI.

Important parts:
- `StatCardProps` interface defines required props: `title`, `value`, `change`, `trend` (`'up'` or `'down'`), `icon`, and `color`.
- `colorClasses` maps supported color names to Tailwind background/text classes, including dark mode variants.
- The component renders a card with the title and value, an icon in a colored container, and a trend indicator using `TrendingUp` or `TrendingDown` plus the change text and “vs last month” label.

Relation to the overall project: Based on its path (`work-main/src/Admin/Components/UI/StatCard.tsx`), it is a UI component likely used within the admin section of the project to present summary metrics/statistics. The provided content does not show where it is imported or used.


## Folder: work-main/src/Admin/common

### work-main/src/Admin/common/user.jsx

This file defines a React functional component named `UserForm` (default export) for rendering a user administration form.

Important parts:
- It accepts props: `formData`, `handleChange`, `handleSubmit`, `handleClear`, and `handleDiscard`.
- It renders a `<form>` with `onSubmit={handleSubmit}`.
- Input fields for `username`, `userDisplayName`, and `apiKey`, all required and controlled by `formData`/`handleChange`.
- A disabled `role` input.
- An `enabled` radio group where “True” is selectable and “False” is disabled.
- `handleClear` and `handleDiscard` are accepted as props but are not used in the shown markup.

Relation to the overall project: Based on its path (`work-main/src/Admin/common/user.jsx`) and fields, it appears to be a reusable/common form component for managing user records in an admin area. The provided content does not show how it is imported or used elsewhere.


## Folder: work-main/src/Admin/pages

### work-main/src/Admin/pages/Dashboard.jsx

This file defines a React `Dashboard` component for an admin dashboard page. It renders a page titled “Dashboard Overview” with a last-updated timestamp, a grid of four statistic cards, a “Site Traffic” chart section with a time-range selector, and a health status panel listing services.

Important components used:
- `StatCard` — displays each stat item (title, value, change, trend, icon, color).
- `Chart` — renders the site traffic chart.
- `HealthStatus` — displays service health/uptime information.

Relation to the overall project: Based on its path (`work-main/src/Admin/pages/Dashboard.jsx`) and content, it appears to be the main overview page for an admin area, aggregating high-level metrics and service health status. The provided content does not show data fetching, routing, or broader app structure.


## Folder: work-main/src/Admin/pages/AuditLogs

### work-main/src/Admin/pages/AuditLogs/AuditLogs.jsx

This file defines a React page component, `AuditLogs`, for viewing system audit activity.

**What it does**
- Renders a static list of five sample audit log entries.
- Provides UI controls for searching by action/user/target, filtering by log type, and selecting a date range.
- Filters the displayed logs by search term and selected type.
- Renders the results in a table with timestamp, user, action, target, type badge, and details.
- Includes an “Export Logs” button, though no click handler is shown.

**Important parts**
- `AuditLogs` default-exported component.
- State: `logs`, `searchTerm`, `filterType`, `dateRange`.
- Helpers: `getTypeIcon(type)` and `getTypeColor(type)` for type-specific badges.
- Derived data: `filteredLogs`, which applies search and type filtering.
- Note: `dateRange` is stored in state but is not used in the shown filtering logic.

**Relation to overall project**
- Located at `work-main/src/Admin/pages/AuditLogs/AuditLogs.jsx`, so it appears to be an admin-facing page for tracking system activities and changes. Based only on this file, it is a frontend presentation component with hardcoded sample data rather than a live data integration.


## Folder: work-main/src/Admin/pages/Directory

### work-main/src/Admin/pages/Directory/FileViewer.jsx

This file defines a React modal component, `FileViewer`, used to display a selected file in an iframe.

- **What it does:** It renders a full-screen overlay with a centered panel. If `file` is provided, it shows the file name and an iframe loading `/api/view-file/{folderName}/{file}`. It also closes when the user presses `Escape` or clicks the close button.
- **Important parts:** the `FileViewer` component; the `useEffect` Escape-key handler; the conditional `if (!file) return null`; the close button; and the iframe that requests the file from the backend API.
- **Project relation:** Based on its path (`src/Admin/pages/Directory/`), it appears to be part of an Admin directory feature for viewing files within a folder.

### work-main/src/Admin/pages/Directory/api.js

This file is a frontend API helper module for the Admin “Directory” page. It uses `axios` to call backend endpoints under `/sakverse/upload` for folder/file operations.

Important components:
- `APIURL` and `PORT`: read from Vite environment variables, though they are not used in the shown requests.
- `API_BASE`: an empty string, making `BASE_URL` resolve to `/sakverse/upload`.
- `fetchFolderStructure()`: GETs `/sakverse/upload/folder-structure`.
- `uploadFilesToFolder(folderName, files)`: POSTs files as `multipart/form-data` to `/sakverse/upload/UploadFiles/{folderName}`.
- `createFileOrFolder(folderName, data)`: POSTs JSON data to `/sakverse/upload/CreateFile/{folderName}`.
- `deleteFileOrFolder(folderName, relativePath)`: DELETEs `/sakverse/upload/DeleteFile/{folderName}` with `relativePath` in the request body.

Relation to the overall project: it provides the Directory page’s client-side functions for interacting with backend file/folder management endpoints, including listing structure, uploading, creating, and deleting files or folders.

### work-main/src/Admin/pages/Directory/index.jsx

This file is a React page component for an admin “Directory”/repository view. It loads a folder structure, lets the user browse folders, open a folder, search folders/files, select files for upload, save pending uploads, delete files, and view file metadata/icons.

Important parts:
- `App` (default export): main component managing state (`folders`, `current`, `pendingUploads`, `searchTerm`, `loading`, `error`) and UI.
- `getFileIcon`: maps file extensions to FontAwesome icons.
- `formatFileSize`: formats byte sizes.
- API helpers imported from `./api`: `fetchFolderStructure`, `uploadFilesToFolder`, `deleteFileOrFolder`.
- Key behaviors: URL `?folder=` auto-open, URL updates on folder open/home, pending upload preview, refresh after upload/delete.

Relation to overall project: It appears to be the Admin Directory page for “Sak AI Repository,” used to manage project documents/folders within the admin interface. The provided file alone does not show routing, backend implementation, or how it is mounted.


## Folder: work-main/src/Admin/pages/ONBOARDING

### work-main/src/Admin/pages/ONBOARDING/Onboarding.jsx

This file defines the `Onboarding` React component for an admin onboarding page.

- It reads and updates the `tab` query parameter via `useSearchParams`, defaulting to `'home'`.
- It renders breadcrumb navigation, showing “DASHBOARD” and, when not on home, the active onboarding type.
- It conditionally renders:
  - `ProjOnboard` when `tab=project`
  - `UserOnboard` when `tab=user`
  - Otherwise a welcome screen with buttons to switch to project or user onboarding.
- It relates to the overall project as an admin-facing onboarding entry point that routes between project onboarding and user onboarding views.

### work-main/src/Admin/pages/ONBOARDING/UserOnboard.jsx

This file defines a React component named `UserOnboard` for an admin user-onboarding form.

What it does:
- Maintains form state for `username`, `userDisplayName`, `apiKey`, `role`, and `enabled`.
- Handles input changes, including converting the `enabled` radio values to booleans.
- On submit, calls `addUser(formData)` from `./apiService`, shows a success or error alert, and resets the form on success.
- Provides `Clear` and `Discard` actions; `Discard` also navigates to `/Admin/Onboarding`.

Important components/elements:
- `UserOnboard` default-exported React component.
- Form fields for username, name, API key, role, and enabled status.
- Submit, Clear, and Discard buttons.

Relation to overall project:
- It appears to be an admin onboarding page that creates users through `addUser`, without including a password in the frontend form data. It also integrates with React Router navigation back to `/Admin/Onboarding`.

### work-main/src/Admin/pages/ONBOARDING/apiService.js

This file is a frontend API service module for the admin onboarding area. It defines a base URL of `/sakverse/admin` and exports three async functions that make authenticated (`credentials: "include"`) POST requests to backend endpoints:

- `addUser(userData)` — sends user data as JSON to `/add_user`.
- `addProject(projectData)` — sends project data as JSON to `/add_project`.
- `AssignRole({ userId, projectId })` — calls `/assign_role` with `userId` and `projectId` as URL query parameters.

Each function checks `response.ok`, throws an error with the response text if the request fails, and returns parsed JSON on success.

It likely supports the Admin onboarding UI by handling user creation, project creation, and role assignment requests. The file also defines `APIURL`, `PORT`, and `API_BASE`, but those constants are not used in the shown functions.

### work-main/src/Admin/pages/ONBOARDING/projOnboard.jsx

This file defines a React page component, `ProjOnboard`, for onboarding a project and at least one user.

**What it does**
- Renders a form for project details: name, description, and manual repository.
- Optionally shows a user details form via a toggle button.
- Collects user fields such as username, display name, API key, role, and enabled status.
- On submit, validates that username and display name are present, then calls `addProject`, `addUser`, and `AssignRole` from `./apiService`.
- Shows success/error feedback using `alert` and `showToast`.
- Clears form state after successful submission.

**Important parts**
- `ProjOnboard`: main exported component.
- State hooks: `projectFormData`, `userFormData`, `showUserForm`, `loading`, plus `userId`, `projectId`, and `files`.
- Handlers: `handleProjectChange`, `handleUserChange`, `handleClear`, `handleFinalSubmit`.
- `role()`: maps numeric role values to display labels such as Admin, Manual Tester, Automation Tester, SDET, and Data Analyst.
- UI sections: project form, user form toggle, user details form, and action buttons.

**Relation to overall project**
- Located under `Admin/pages/ONBOARDING`, so it appears to be an admin onboarding page.
- It coordinates project creation, user creation, and role assignment through the local `apiService`.
- It is part of a React Router-based app, as indicated by the `useNavigate` import, though navigation is not visibly used in this file.


## Folder: work-main/src/Admin/pages/PROJECTS

### work-main/src/Admin/pages/PROJECTS/ProjectList.jsx

This file defines the `ProjectList` React component, an admin page for viewing and managing projects.

What it does:
- Fetches project data through the `useUserData` hook (`projects`, `loading`).
- Lets the user search projects by name, toggle between grid and table views, and paginate results (9 per page).
- Sorts projects by numeric `project_id` and resets pagination when search changes.
- Renders project cards/rows with project name, ID, type, role, and linked/unlinked status.
- Navigates to `/Admin/ProjectsOnboarding` to create a project and to `/Admin/Projects/{project_id}` to view details.

Important parts:
- `ProjectList` default-exported component.
- State: `search`, `view`, `currentPage`.
- Derived data: `filteredProjects`, `totalPages`, `paginatedProjects`.
- Helper: `getProjectTypeColor`, mapping project types (`PM`, `TM`, `KM`, `LLM`) to Tailwind color classes.
- UI sections: header/view toggle/create button, search, loading spinner, grid view, table view, pagination, empty state.

Relation to overall project:
- It appears to be an admin-facing project management screen, using shared user/project data from `useUserData` and React Router for navigation to project onboarding and detail pages.

### work-main/src/Admin/pages/PROJECTS/api.js

This file defines a React hook, `useUserStoryFlow`, for submitting project onboarding data to a backend endpoint.

Important parts:
- `projectOnboarding(text, files)`: builds a `FormData` payload, appending `data` and/or `files`, then sends a `POST` request to `/sakverse/admin/project_onboarding` with a Bearer token from `sessionStorage` and credentials included.
- State management: `loading`, `error`, and `response` track request status and result.
- `API_BASE` is set to `/sakverse`; `APIURL` and `PORT` are defined but not used in the shown code.

Relation to the overall project: based on its path under `Admin/pages/PROJECTS`, it likely supports an Admin project onboarding workflow by connecting frontend UI to the backend project onboarding API. The provided file does not show where the hook is consumed.


## Folder: work-main/src/Admin/pages/PROJECTS/ProjectDetails

### work-main/src/Admin/pages/PROJECTS/ProjectDetails/ProjectDetails.jsx

This file implements the **ProjectDetails** page for an admin project-management UI.

**What it does**
- Reads `projectId` from the route and finds the matching project from `useUserData().projects`.
- Renders a tabbed view with **Details**, **Integrations**, and **Users**.
- In **Details**, shows project fields such as name, type, role, linked status, and integration count; some fields can be edited when editing is enabled.
- In **Integrations**, displays a table of project integrations and allows editing tool, username, password, and enabled state while in edit mode.
- In **Users**, displays a static list of dummy users with role, joined date, status, and delete/add-user actions that currently only log to the console.
- Provides Edit/Save/Cancel controls for Details and Integrations; Save currently only exits edit mode, and Cancel restores the original project.

**Important components/helpers**
- `ProjectDetails` — main page component.
- `Field` — labeled wrapper for detail fields.
- `ReadonlyField` — read-only display box.
- Constants: `tabs`, `INTEGRATION_LABELS`, `DUMMY_USERS`.

**Relation to overall project**
- Located under `Admin/pages/PROJECTS/ProjectDetails`, so it is part of the admin project details experience.
- Depends on `useUserData` for project data and React Router for navigation/params.
- Uses local component state for editing and integration form values; the provided code does not show persistence/API calls for saving changes.


## Folder: work-main/src/Admin/pages/PROJECTS/onboarding

### work-main/src/Admin/pages/PROJECTS/onboarding/CreateProjectModal.jsx

This file defines a React modal component, `CreateProjectModal`, used to create a new project through a 4-step onboarding flow.

**What it does**
- Renders a modal only when `isOpen` is true.
- Tracks the current step (`1`–`4`), step validity, local submit loading, and toast messages.
- Maintains `formData` containing project details and uploaded documents.
- Provides navigation with `handleNext` and `handleBack`.
- Updates project fields, integrations, and user onboarding data through dedicated updater functions.
- On final submission, serializes project data, sends it with documents via `projectOnboarding` from `useUserStoryFlow`, shows a success/error toast, and closes the modal after success.

**Important components/elements**
- `CreateProjectModal` itself, receiving `isOpen`, `onClose`, and `users`.
- Imported step components: `Step1ProjectDetails`, `Step2DocumentUpload`, `Step3ToolIntegration`, `Step4UserOnboarding`.
- `useUserStoryFlow` hook, used for `projectOnboarding`, `apiLoading`, and `apiError`.
- Modal UI sections: header, scrollable step content, footer with navigation/progress, loading overlay, and toast.

**Relation to overall project**
- Located under `Admin/pages/PROJECTS/onboarding`, so it is part of the admin project onboarding workflow.
- It orchestrates the multi-step project creation process and connects the step UIs to the onboarding API.

### work-main/src/Admin/pages/PROJECTS/onboarding/Step1ProjectDetails.jsx

This file defines a React component, `Step1ProjectDetails`, used as a step in a project onboarding flow.

What it does:
- Receives `formData`, `updateProjectData`, `setStepValid`, and `setStepError` as props.
- Uses a `useEffect` to validate required fields: `project_name`, `project_type`, `llm_model`, and `linked`.
- Calls `setStepValid` and `setStepError` based on whether validation passes.
- Renders a form UI for entering project details, including project name, project type, description, LLM model name, and a yes/no choice for linking the Unite Automation Tool.
- Includes a hidden section containing a read-only automation repo URL.

Important components/elements:
- `Step1ProjectDetails` component.
- Validation logic in `useEffect`.
- Controlled inputs/select/textarea/radio buttons bound to `formData` and `updateProjectData`.
- Hidden repo section with a fixed GitHub URL.

Relation to overall project:
- Located under `Admin/pages/PROJECTS/onboarding/`, so it appears to be the first step of an admin project onboarding wizard.

### work-main/src/Admin/pages/PROJECTS/onboarding/Step2DocumentUpload.jsx

This file defines a React component, `Step2DocumentUpload`, used as an onboarding step for uploading project documents.

What it does:
- Lets the user enter a required manual repository name.
- Accepts file uploads via drag-and-drop or file picker.
- Filters uploads to PDF, DOCX, and XLSX MIME types.
- Stores uploaded files in `formData.documents`.
- Allows removing uploaded files by index.
- Validates that both a manual repository name and at least one document exist, then reports validity/error to the parent through `setStepValid` and `setStepError`.

Important components/elements:
- `handleFileUpload`: filters and appends selected files.
- `removeFile`: removes a file from `formData.documents`.
- `useEffect`: performs step validation based on `formData.project.manual_repo` and `formData.documents`.
- UI sections: manual repository input, drag-and-drop upload area, uploaded files list.

Relation to overall project:
- It appears to be Step 2 of a project onboarding flow, collecting required repository and document information before proceeding.

### work-main/src/Admin/pages/PROJECTS/onboarding/Step3ToolIntegration.jsx

This file implements a React component for **Step 3 of an onboarding flow: Tool Integrations**. It lets users configure one integration per category:

- **PM** — Project Management
- **TM** — Test Management
- **KM** — Knowledge Management
- **LLM** — LLM Integration (marked required)

### What it does
- Builds initial state from saved `integrations`, with blank defaults for missing categories.
- Validates each integration:
  - LLM requires both tool/model name and API URL.
  - Other categories require tool and URL together if either is set.
  - PM and TM require a Custom ID when both tool and URL are set.
- Tracks per-card errors and auto-opens cards with errors.
- Supports accordion expand/collapse for each category card.
- Supports additional key/value config rows, including comma-separated values converted to arrays on output.
- Notifies the parent via `updateIntegration`, `setStepValid`, and `setStepError`.
- Outputs only non-empty integrations, with `additional_config` set to `null` when empty.

### Important components/functions
- `ToolIntegration` — main component.
- `validate` — validation logic.
- `toOutput` — transforms internal state into parent-facing output.
- `buildInitialItems` — merges saved integrations with defaults.
- `ConfigRow` — editable key/value config row.
- Helper functions: `setField`, `addConfigRow`, `setConfigValue`, `renameConfigKey`, `removeConfigRow`, `toggleCard`.

### Relation to overall project
Based on its path (`.../onboarding/Step3ToolIntegration.jsx`) and props such as `setStepValid`/`setStepError`, it appears to be one step in a multi-step onboarding wizard, specifically the step where users connect external tools/services and provide optional additional configuration.

### work-main/src/Admin/pages/PROJECTS/onboarding/Step4UserOnboarding.jsx

This file implements **Step 4 of a project onboarding flow**: configuring user credentials for an admin and optional team members, including per-integration credentials.

**What it does**
- Initializes/syncs admin credentials when `integrations` changes.
- Renders an admin card with fixed admin identity and editable integration credentials.
- Allows adding/removing team users and editing their basic fields plus integration credentials.
- Validates required username/password fields for admin and new users.
- Reports validation state to the parent via `setStepValid` and `setStepError`.
- Shows a global error banner when validation fails.

**Important components**
- `Field`: reusable labeled input with required marker and disabled styling.
- `CredRow`: memoized row for one integration credential (integration type, username, password).
- `Step4UserOnboarding`: main component managing state updates through `updateUsers`.

**Relation to overall project**
- It is located under `Admin/pages/PROJECTS/onboarding`, so it is part of the admin project onboarding wizard.
- It depends on parent-provided `usersData`, `integrations`, and step validation callbacks, indicating it is one step in a larger multi-step onboarding process.


## Folder: work-main/src/Admin/pages/PROJECTS/onboarding

### work-main/src/Admin/pages/PROJECTS/onboarding/index.jsx

This file implements a multi-step **project onboarding wizard** for the Admin area. It manages wizard state (current step, validity, loading, errors, toast, and form data), renders the appropriate step component, handles navigation between steps, and submits the collected project data and documents through `useUserStoryFlow().projectOnboarding`.

Important parts:
- `CreateProjectPage`: main container component.
- Step components: `Step1ProjectDetails`, `Step2DocumentUpload`, `Step3ToolIntegration`, `Step4UserOnboarding`.
- State and handlers: `handleNext`, `handleBack`, `updateProjectData`, `updateIntegration`, `updateUsers`, `handleSubmit`.
- UI elements: toast notifications, step indicators, header/footer navigation, loading overlay.

It likely relates to the broader application as the Admin project creation/onboarding flow, connecting form input to the project onboarding API and routing users back to `/Admin/Projects` after success.


## Folder: work-main/src/Admin/pages/USERS

### work-main/src/Admin/pages/USERS/index.jsx

This file defines a React page component, `UserManagement`, for managing a list of users in an admin interface.

**What it does**
- Stores a local array of users with fields like name, email, role, project, status, and last login.
- Lets the user search by name/email and filter by role/project.
- Displays users in a table with status badges and action buttons.
- Supports adding a new user and editing an existing user through a modal form.
- Supports toggling a user’s active/inactive status and deleting a user.
- All changes are kept in React component state; no API or persistence logic is shown.

**Important components/functions**
- `UserManagement`: main page component.
- State: `users`, `showAddModal`, `isEditMode`, `selectedUser`, `searchTerm`, `filterRole`, `filterProject`, `newUser`.
- `filteredUsers`: derived list based on search and filters.
- `handleSubmitUser`: adds or updates a user.
- `toggleUserStatus`: switches active/inactive.
- `deleteUser`: removes a user.
- UI sections: header with “Add User”, filter bar, user table, add/edit modal.

**Relation to overall project**
- Located under `work-main/src/Admin/pages/USERS/`, so it appears to be an admin user-management page.
- The roles and projects suggest it may be part of a testing/project management application, but the provided file only shows frontend UI behavior and does not show routing, backend integration, or how it connects to the rest of the app.


## Folder: work-main/src/Admin/pages/USERS/Modal

### work-main/src/Admin/pages/USERS/Modal/Modals.jsx

This file defines a React component named `UserModal` that renders a modal dialog for adding or editing a user.

Important parts:
- It imports `Dialog` from `@headlessui/react`.
- It accepts props: `isOpen`, `onClose`, `newUser`, `setNewUser`, `onAddUser`, `onUpdateUser`, and `isEditing`.
- It displays a title that changes based on `isEditing` ("Edit User" or "Add New User").
- It contains controlled inputs for `name`, `email`, `role`, `project_access`, and `token`, updating `newUser` through `setNewUser`.
- It has Cancel, and either Update or Add buttons depending on `isEditing`.

Relation to the overall project: Based on its path (`work-main/src/Admin/pages/USERS/Modal/Modals.jsx`), it is part of the admin area's Users page and provides the modal UI for creating or updating user records. The actual data handling is delegated to the parent component through the provided callback props.


## Folder: work-main/src/Business

### work-main/src/Business/api.js

This file defines a React custom hook, `useUserStoryFlow`, that centralizes frontend API calls for a “Business” user-story workflow.

What it does:
- Manages shared request state: `loading`, `error`, and `response`.
- Provides async functions to call backend endpoints under `/sakverse/business/...`:
  - `uploadBA`: uploads BA text/files and optional `pr_id` as `FormData`.
  - `fetchUserStoryById`: fetches a user story by request ID.
  - `getProcessedIdea`: fetches processed ideas for a project ID.
  - `publishUserStory`: publishes a user story using `userstory_ref_id` and `project_id`.
  - `downloadFeature`: downloads an Excel file from a POST request.
  - `downloadFeatureDoc`: downloads a Word document from a POST request.
- Handles errors, loading state, JSON parsing, and browser file downloads via blob URLs.

Important components:
- `useUserStoryFlow` hook
- State variables: `loading`, `error`, `response`
- Callback functions: `uploadBA`, `fetchUserStoryById`, `getProcessedIdea`, `publishUserStory`, `downloadFeature`, `downloadFeatureDoc`
- Constants: `API_BASE = /sakverse`; `APIURL` and `PORT` are defined but not used in the shown code.

Relation to overall project:
- It appears to be the frontend API/service layer for the Business module’s user-story flow, used by React components to interact with backend business endpoints and manage request lifecycle state.

### work-main/src/Business/index.jsx

This file defines and exports a React component named `Admin`, which appears to be a page/layout for a “Business” area.

What it does:
- Manages local state for `isSidebarOpen` and `selectedProjectId`.
- Gets the current user from `useAuthContext` and derives `username` from `user.displayName`.
- Renders a `Navbar`, passing `setSelectedProjectId` as `onProjectSelect` and `username`.
- Renders `UserStoryFlow`, passing the selected project ID.
- Wraps the layout in a full-height flex container with a scrollable main content area.

Important components/imports shown:
- `Navbar`
- `UserStoryFlow` (imported from `./IdeationAgent/US_Creator`)
- `useAuthContext`
- `Sidebar` and `useLogout` are imported, but the shown JSX does not render `Sidebar` or visibly use `logout`.

Relation to overall project:
- It appears to be an entry point for the Business module, connecting project selection in the navbar to the user-story creation flow, while using authentication context for the displayed username.


## Folder: work-main/src/Business/Components

### work-main/src/Business/Components/Content.jsx

This file defines a React component named `Content`.

- **What it does:** It renders a `<main>` element with the class `ml-0 transition-all overflow-y-auto` and places the `IdeationAgent` component inside it.
- **Important components:** `Content` (the default-exported component) and `IdeationAgent`, imported from `../IdeationAgent/US_Creator`.
- **Relation to overall project:** It appears to serve as a content-area wrapper that displays the `IdeationAgent` component. It also imports `Routes` and `Route` from `react-router-dom`, though those imports are not used in the shown code.

### work-main/src/Business/Components/Navbar.jsx

This file defines a React `Navbar` component used as a top navigation bar.

What it does:
- Renders the app logo/title (“Intelligent BA Agent”).
- Loads the current user’s projects via `useUserData`.
- Automatically selects a project when there is exactly one project, otherwise clears selection.
- Lets the user manually select a project from a dropdown and notifies the parent through `onProjectSelect`.
- Shows loading and “No projects available” states.
- Provides a user menu with the signed-in username and a logout action.

Important parts:
- `Navbar` component and its props: `toggleSidebar`, `onProjectSelect`, `username`.
- State: `showLogout`, `projectDropdownOpen`, `selectedProject`.
- Hooks: `useLogout`, `useAuthContext`, `useUserData`.
- Handlers: `handleProjectSelect`, `getProjectDisplayName`.
- `useEffect` that synchronizes `selectedProject` with the loaded `projects`.

Relation to the overall project:
- It appears to be a shared navigation/layout component that depends on authentication and user project data.
- It communicates project selection upward to a parent component through `onProjectSelect`, likely affecting which project’s data is displayed elsewhere in the app.

### work-main/src/Business/Components/Sidebar.jsx

This file defines a React `Sidebar` component for a business section of the app.

- **What it does:** Renders a fixed left sidebar with a close button (mobile only) and a navigation list. It uses `isOpen` to toggle mobile visibility via Tailwind transform classes, and `closeSidebar` handles the close button click.
- **Important components/elements:** The `Sidebar` component; a `NavLink` to `/Business` labeled “Ideation” with a hover tooltip; commented-out `NavLink`s for `/Business/Team` and `/Business/Settings`.
- **Relation to overall project:** It appears to be part of a business-area layout/navigation, providing access to the Ideation route and potentially future Team/Settings routes.


## Folder: work-main/src/Business/IdeationAgent

### work-main/src/Business/IdeationAgent/US_Creator.jsx

This file is a React component for the **AI User Story Agent / US Creator** workflow. It provides a project-scoped UI for creating, tracking, viewing, publishing, and downloading AI-generated user stories.

### What it does
- Accepts a `selectedProjectId` and loads processed ideas for that project.
- Lets users submit new business requirements through `InputForm` via `uploadBA`.
- Tracks idea processing status and polls `fetchUserStoryById` until an executive summary is available.
- Displays completed idea details: executive summary, requirement analysis document, and feature/user story breakdown.
- Supports publishing stories and downloading outputs (Excel, Word, HTML; Markdown helper exists).
- Shows loading, empty, error, and processing states.

### Important components / pieces
- **`UserStoryFlow`** (default export): main container and state manager.
- **`Card`**, **`StatusBadge`**, **`EmptyState`**: local UI primitives.
- Imported components: `InputForm`, `Loader`, `Modal`, `UserStoryAccordion`, `IdeaHistoryPanel`.
- Hook: `useUserStoryFlow` for API operations such as upload, fetch, publish, download, and processed idea retrieval.
- Key handlers: `handleSubmit`, `handleSelectIdea`, `handlePublish`, `handleNewIdea`, `handleDownloadFeature`, `handleDownloadFeatureDoc`, `handleDownloadHTML`.

### Relation to overall project
It appears to be the frontend page/component for the **Business/IdeationAgent** module, connecting the UI to the user-story generation API and presenting project-specific ideation history and generated artifacts.

### work-main/src/Business/IdeationAgent/apiService.js

This file is currently inactive: all of its code is commented out.

What it does:
- It appears intended to provide API service functions for an admin-related backend.
- The commented functions are `addUser`, `addProject`, and `AssignRole`.
- They would send authenticated `POST` requests using a bearer token from `sessionStorage`.
- `addUser` and `addProject` would send JSON request bodies.
- `AssignRole` would send a request with query parameters for `userId` and `projectId`.

Important components:
- Commented import of `config` from `../../../../../config.mjs`.
- Commented `API_BASE_URL` built from `config.JavaIP`.
- Commented `addUser(userData)`.
- Commented `addProject(projectData)`.
- Commented `AssignRole({ userId, projectId })`.

Relation to overall project:
- Based on its path, `work-main/src/Business/IdeationAgent/apiService.js`, it is associated with the `IdeationAgent` business module.
- It likely was meant to support user, project, and role-assignment operations through an admin API, but in its current state it exports nothing active and performs no runtime behavior.


## Folder: work-main/src/Business/IdeationAgent/components

### work-main/src/Business/IdeationAgent/components/IdeaHistoryPanel.jsx

This file defines a React component, `IdeaHistoryPanel`, that renders a sidebar for browsing and selecting ideas within a project.

**What it does**
- Displays an “Idea History” panel with a header, optional project-specific idea count, refresh button, and “New Idea” button.
- Shows different body states depending on props: no project selected, loading, error, or a list of ideas.
- Sorts ideas by descending `id` and renders each as a selectable card.
- Shows each idea’s status via `StatusBadge`, creation date, ID, and a short text preview.
- Supports a polling state: if an idea ID is in `pollingIds`, its badge shows `inprogress`, and if it is also selected, it shows an “AI agent working...” indicator.
- Allows opening a modal to view the full `input` for an idea via an eye icon button.
- Calls parent-provided callbacks: `onSelect`, `onRefresh`, and `onNewIdea`.

**Important components / dependencies**
- `StatusBadge`, imported from `../US_Creator`.
- `FontAwesomeIcon` with `faEye` for the “view full input” action.
- Local `fmt` helper for formatting `created_at` dates.
- Local `viewIdea` state for controlling the input modal.

**Relation to the overall project**
- It is located under `work-main/src/Business/IdeationAgent/components/`, so it is part of the IdeationAgent feature area.
- It appears to be a presentation component used by a parent IdeationAgent view to manage idea history for a selected project, including selection, refresh, creation, and polling status display.

### work-main/src/Business/IdeationAgent/components/InputForm.jsx

This file defines a React component named `InputForm` for collecting a business requirement and optional file attachments.

**What it does**
- Maintains local state for `text`, selected `files`, and drag-over status.
- Supports drag-and-drop and click-to-browse file selection.
- Allows removing selected files.
- Validates that either text or at least one file exists before calling `onSubmit(text, files)`.
- Clears inputs after submission.
- Shows a loading state on the submit button and allows canceling via `setVisible(false)`.

**Important parts**
- `handleFileDrop`, `handleFileChange`, `removeFile`: file selection/removal logic.
- `handleSubmit`: submission guard and callback invocation.
- Textarea for the business requirement.
- Drag-and-drop file zone with visual drag-over feedback.
- File list rendering with remove buttons.
- Submit/Cancel action buttons.

**Relation to overall project**
Based on its path and UI, it appears to be an input form within the `IdeationAgent` business feature, used to gather a business requirement and attachments before generating user stories. The provided content does not show how it is imported or used elsewhere.

### work-main/src/Business/IdeationAgent/components/Loader.jsx

This file defines a React loading component named `Loader` for the `IdeationAgent` area of the project.

- **What it does:** It renders a full-area loading screen with an animated “AI core” visual, a main message, a rotating set of thinking messages, an optional submessage, and pulsing progress dots.
- **Important parts:** The default-exported `Loader` component; its `message` and `submessage` props; the internal `messages` array; the `step` state and interval that rotate messages every 2 seconds; and the CSS keyframe animation `loadingPulse`.
- **Project relation:** Based on its path, it is a UI component used within the `IdeationAgent` business feature, likely shown while that feature processes or generates results. The provided file alone does not show where it is imported or used.

### work-main/src/Business/IdeationAgent/components/Modal.jsx

This file defines a React functional component named `Modal`.

- **What it does:** It renders a full-screen overlay with a centered modal card. The card displays a heading, the `content` prop inside a `<pre>` block, and a “Close” button that calls `onClose`.
- **Important components/elements:** The overlay container, the modal card, the title “🧾 Original User Input”, the scrollable `<pre>` content area, and the close button.
- **Project relation:** Based on its path under `IdeationAgent/components`, it is likely a reusable UI component for the IdeationAgent feature, specifically for showing the original user input in a modal dialog. The provided content does not show where it is imported or used.

### work-main/src/Business/IdeationAgent/components/UserStoryAccordion.jsx

This file defines a React component, `UserStoryAccordion`, used to display a feature in an accordion UI. It shows the feature name, counts of stories and approaches, and expands to reveal tabs for “Stories” and “Approach.” The “Stories” tab renders `StoryCard` items with details such as prerequisites, user actions, and acceptance criteria, plus a publish action. The “Approach” tab renders numbered approach steps. It also shows published status badges.

Important components:
- `UserStoryAccordion`: main accordion container for a feature.
- `StoryCard`: expandable card for an individual user story, including publish handling.
- `TabButton`, `Section`, `ChevronRight`: small helper UI components.

Relation to the overall project: It is located under `work-main/src/Business/IdeationAgent/components/`, so it appears to be part of the IdeationAgent business feature’s frontend UI, specifically for presenting and publishing generated user stories/approaches for a feature.


## Folder: work-main/src/Components/AppHeader

### work-main/src/Components/AppHeader/Documentation.jsx

This file defines a React presentational component, `SakVerseDocumentation`, that renders a full documentation page for the SakVerse platform.

Important parts:
- A top-level layout with a scrollable main content area.
- Documentation sections: “What is SakVerse,” “How SakVerse Works,” “Key Advantages,” comparison table, “Summary,” and FAQ.
- Interactive `<details>`/`<summary>` accordions for workflow steps and FAQ items.
- FontAwesome icons used for section and item visuals.
- A comparison table contrasting traditional manual QA with SakVerse’s automated approach.

Relation to the overall project:
- It appears to be a documentation view within the app, located under `Components/AppHeader`, likely shown to users to explain SakVerse’s purpose, workflow, advantages, and FAQs. It is static content and does not manage application state or data.

### work-main/src/Components/AppHeader/index.jsx

This file defines a React `Navbar` component used as the application header.

**What it does**
- Renders a fixed top navigation bar with the app logo, title/subtitle, sidebar toggle, Documentation button, username, and profile/logout menu.
- Dynamically changes the displayed title/subtitle and browser tab title based on whether the current route includes `/ManualProject/2`.
- Toggles a logout dropdown when the profile icon is clicked, with auto-hide behavior using a timeout and mouse enter/leave handling.
- Navigates to `/Documentation` and reloads the page when the logo is clicked.
- Calls a shared `useLogout` hook for logout functionality.

**Important parts**
- `Navbar` component and its props: `onToggleSidebar`.
- State: `showLogout`.
- Refs: `logoutTimeoutRef`.
- Route-aware logic: `isTCG`, `mainTitle`, `subTitle`.
- Event handlers: `goToHome`, `handleProfileClick`, `handleMouseEnter`, `handleMouseLeave`.
- UI sections: left brand/title area and right actions/profile area.

**Relation to overall project**
- It appears to be the shared app header for a React Router-based application, likely wrapping or sitting above routed pages.
- It integrates with sidebar toggling, documentation navigation, session-based username display, and logout behavior.


## Folder: work-main/src/Components/Common

### work-main/src/Components/Common/logout.js

This file defines a custom React hook, `useLogout`, that returns an async `handleLogout` function.

- **What it does:** `handleLogout` calls `logout()` from `AuthContext`, clears `localStorage`, then navigates to `/login`. If logout fails, it logs the error.
- **Important components:** `useLogout` (default export), `handleLogout`, and its dependencies on `useNavigate` and `useAuthContext`.
- **Project relation:** It appears to support the app’s authentication/logout flow by coordinating session cleanup and redirecting users to the login page.


## Folder: work-main/src/Components/Error

### work-main/src/Components/Error/index.jsx

This file defines a React component named `ErrorPage` that renders a full-screen error UI.

Important parts:
- It accepts `error` and `id` props.
- It uses `useNavigate` from `react-router-dom` for navigation.
- `handleCheck` navigates to `/` if `id === 1` or `error.status === 401`; otherwise it navigates back with `navigate(-1)`.
- It displays an error image, a “SOMETHING WENT WRONG.” heading, an error message (or “An error occurred.” if no error), and a “CLICK HERE” button that triggers `handleCheck`.

Relation to the overall project: Based only on this file, it appears to be a reusable error display component, likely used to show errors and guide users to login or return to the previous page.


## Folder: work-main/src/Components/PageContent

### work-main/src/Components/PageContent/index.jsx

This file defines a React component named `PageContent` that renders the imported `AppRoutes` component and exports it as the default export. Its important components are `PageContent` and `AppRoutes`. It likely serves as a content-area wrapper that displays the application’s routed pages.


## Folder: work-main/src/Components/SideMenu

### work-main/src/Components/SideMenu/index.jsx

This file defines a React sidebar navigation component (`Sidebar`) for the app.

**What it does**
- Renders a fixed left sidebar with navigation items.
- Tracks the current route via `useLocation` and updates `selectedKey`.
- Navigates using `useNavigate` when items are clicked.
- Expands/collapses based on `isSidebarOpen` or mouse hover.
- Loads and displays user projects from `useUserDataContext`.
- Shows a dropdown for “Manual Projects” and renders project buttons that navigate to project routes.
- Includes Dashboard and Settings navigation buttons.
- Has commented-out sections for “Data Projects” and “Automation Projects.”

**Important parts**
- `Sidebar` (default export): main component.
- `renderProjects(type)`: filters projects by `project_type`, handles loading/error/empty states, and renders project buttons.
- `handleClick(path)`: navigates to a path and calls `onClose` if provided.
- `handleProjectClick(projectId, type)`: navigates to `/{type}Project/{projectId}`.
- `handleAutomationProjectClick(projectId)`: navigates to `/automation?projectId=...`.
- State: `selectedKey`, `openDropdown`, `hovered`.

**Relation to overall project**
- It appears to be the app’s side navigation menu, connecting routing, user project data, and page navigation (Dashboard, Manual Projects, Settings). It uses shared user data context to list projects and supports a collapsible/hover-expanded sidebar layout.


## Folder: work-main/src/Hooks/Auth

### work-main/src/Hooks/Auth/AuthContext.jsx

This file defines a React authentication context.

- `AuthContext`: a React context initialized to `null`.
- `AuthProvider`: wraps children and provides a single instance of auth state/logic from `useAuth()`.
- `useAuthContext`: a custom hook that reads the context and throws if used outside `AuthProvider`.

It likely serves as the central place for sharing authentication-related state and functions across the React component tree, with `AuthProvider` expected to be placed high in the app.

### work-main/src/Hooks/Auth/ProtectedProjectRoute.jsx

This file defines a React route-guard component, `ProtectedProjectRoute`, that conditionally renders its `children` based on whether the current user can access a project identified in the URL.

Important parts:
- `useAuthContext()` provides `authInfo` and `loading`.
- React Router hooks (`useParams`, `useSearchParams`) extract `projectId` either from route params or a query parameter, depending on `paramType`.
- While auth state is loading, it shows “Checking access...”.
- If no `projectId` is found, it logs a warning and renders children anyway.
- Otherwise, it parses the project ID and checks whether it is included in `authInfo.allowedProjects`.
- If access is denied, it renders `ErrorPage` with a 403-style authorization error.
- If access is allowed, it renders `children`.

In relation to the overall project, this component likely acts as an authorization wrapper for project-specific routes/pages, using shared auth state and a common error display component.

### work-main/src/Hooks/Auth/authFetch.js

This file defines an async helper, `authFetch`, that wraps the browser `fetch` API.

- **What it does:** It calls `fetch` with the provided `input` and `init`, forcing `credentials: "include"` so cookies are sent. If the response status is `401`, it clears `localStorage`, redirects the browser to `/login`, shows an alert saying the session expired, and returns without a response. Otherwise, it returns the fetch response.
- **Important components:** the `authFetch(input, init = {})` function; the merged fetch options with `credentials: "include"`; the `401` status check; `localStorage.clear()`; `window.location.href = "/login"`; and the alert.
- **Project relation:** Based only on the file, it appears intended as a shared authenticated request utility for the project, centralizing cookie-based requests and session-expiry handling. The provided content does not show where it is imported or used.

### work-main/src/Hooks/Auth/authUse.js

This file defines a React custom hook, `authUse`, for frontend authentication/session management.

**What it does**
- Maintains auth state: `authInfo`, `isAuthenticated`, `user`, `loading`, and `error`.
- On mount, calls `checkAuth()` to verify the current session via `GET /sakverse/auth/check`.
- `login(username, password)` base64-encodes the password with `btoa`, posts it to `/sakverse/auth/login`, then re-checks auth.
- `logout()` posts to `/sakverse/auth/logout` and clears local auth/user state.
- `canAccessProject(projectId)` checks whether `user.allowedProjects` includes the project ID as a string.
- Also defines `encryptPassword(password)` using `node-forge` and an RSA public key, though it is not used within the shown hook.

**Important components**
- State: `authInfo`, `loading`, `error`, `isAuthenticated`, `user`
- Functions: `checkAuth`, `login`, `logout`, `canAccessProject`, `encryptPassword`
- API endpoints used: `/sakverse/auth/check`, `/sakverse/auth/login`, `/sakverse/auth/logout`

**Relation to overall project**
- It appears to be a shared frontend authentication hook used to manage login/logout, session restoration, and project-level access control for a React app communicating with a backend under `/sakverse`.


## Folder: work-main/src/Hooks/Automation

### work-main/src/Hooks/Automation/Automation.js

This file defines a React custom hook, `useAutomationFlow`, that centralizes frontend calls to automation-related backend endpoints.

**What it does**
- Maintains shared `loading` and `error` state.
- Exposes async functions for automation operations, including:
  - `getTestScenario`
  - `executeTest`
  - `cloneTest`
  - `getTestResult`
  - `AddStep`
  - `deletePlannedStep`
  - `movePlannedStep`
  - `updatePlannedIntent`
  - `updateExecutionStep`
  - `executeSuiteParallel`
  - `openSuiteReport`
  - `generateHTMLReport`
- Each function performs a `fetch` to `${API_BASE}/automation/...` with `credentials: 'include'`, parses JSON/text responses, sets errors on failure, and toggles loading state.

**Important components**
- `useAutomationFlow` hook
- Its returned callback functions and shared `loading`/`error` state
- `API_BASE`, set to `/sakverse`

**Relation to overall project**
- It appears to be a frontend data-access hook for automation features, likely consumed by React components/pages that need to trigger or inspect automated test execution and reporting. The provided file does not show those consumers.


## Folder: work-main/src/Hooks/DataSynthesize

### work-main/src/Hooks/DataSynthesize/Data.js

This file defines a reusable React hook, `useData`, for making an authenticated POST request to generate synthetic data.

**What it does**
- Manages `loading` and `error` state.
- Exposes `generateSyntheticData(payload)`, which sends `payload` as JSON to `/sakverse/data/generate_synthetic_data` with credentials included.
- Parses the JSON response, throws an error if the response is not OK, and returns the response data on success.

**Important components**
- `useData`: the custom hook.
- `generateSyntheticData`: the async API call function.
- `loading` and `error`: state values returned for UI feedback.
- `API_BASE`: the base path used for the request.

**Relation to the overall project**
- It appears to be a frontend data-access hook that components can use to trigger backend synthetic-data generation and handle request status/errors. The file alone does not show where it is imported or used.


## Folder: work-main/src/Hooks/Manual

### work-main/src/Hooks/Manual/UserData.js

This file is a React hooks module (`work-main/src/Hooks/Manual/UserData.js`) that centralizes frontend data fetching and mutation logic for a project-management/testing workflow. It uses React state/effects and calls backend endpoints under `/sakverse`, mostly with `authFetch` or `fetch` and `credentials: "include"`.

Important components/hooks include:

- `useUserData` (default export): fetches the current user’s assigned projects from `/sakverse/auth/project`.
- `useJiraData(projectId)`: fetches external/Jira stories for a project.
- `useNextStep(selectedStoryId)`: triggers a POST to get the next step for a selected story.
- `useProjectLinkedStatus(projectId)`: checks whether a project is linked.
- Submission/update hooks: `useUserStorySubmit`, `useUpdateQueries`, `useReviewStatusUpdate`, `useUpdateUserStory`, `useUpdateRequirement`, `useUpdateTestCase`, `usePublishTestCases`, `usePublishUserStory`, and `useUserStorySubmit_v2`.
- Data/utility hooks: `useRequirementGraph`, `useDownloadExcel`, `useTestConfiguration`, `useAdoTestPlan`, `useAdoTestSuite`, and `useAdoTestData`.

Overall, it likely supports a React frontend for managing projects, user stories, requirements, test cases, Jira/ADO integrations, and publishing/exporting test artifacts. The file contains both active and commented-out hook implementations.

### work-main/src/Hooks/Manual/UserDataContext.jsx

This file creates a React context for sharing user data.

- **What it does:** It defines `UserDataContext`, a `UserDataProvider` component that calls `useUserData()` and supplies its result as context value, and a `useUserDataContext` hook for consuming that context.
- **Important components:** `UserDataContext`, `UserDataProvider`, and `useUserDataContext`.
- **Project relation:** It likely acts as a shared access point for user-related data across components in the React application, wrapping parts of the component tree with `UserDataProvider`. The actual behavior of `useUserData` is defined in `./UserData`, which is not shown here.


## Folder: work-main/src/Hooks/Suite

### work-main/src/Hooks/Suite/Suite.js

This file defines a custom React hook, `useSuite`, that centralizes frontend API calls for test-suite operations.

**What it does**
- Manages shared `loading` and `error` state for suite-related requests.
- Exposes four async operations:
  - `createSuite(projectId, payload)` — POSTs a new suite for a project.
  - `getSuiteList(projectId)` — GETs suites for a project.
  - `executeSuite(suiteId, maxParallel = 1)` — POSTs a request to execute a suite, with an optional parallelism parameter.
  - `getSuiteReportJson(suiteId, screenshotMode = 'all')` — GETs a suite report as JSON, with an optional screenshot mode.
- All requests use `credentials: 'include'` and target paths under `/sakverse`.

**Important components**
- `useSuite` hook itself.
- `loading` and `error` state.
- The four `useCallback`-wrapped request functions.
- `API_BASE` constant (`/sakverse`), used to build endpoint URLs.
- `APIURL` and `PORT` are defined but not used in the shown code.

**Relation to overall project**
- It likely serves as a frontend data-access layer for suite management features, such as creating, listing, executing, and reporting on test suites.
- Components or pages in the project can call this hook to interact with the backend suite endpoints while sharing loading/error state.


## Folder: work-main/src/Hooks/TDM

### work-main/src/Hooks/TDM/tdm.js

This file defines a React custom hook, `useTDM`, that acts as a frontend API client for TDM-related backend operations.

**What it does**
- Maintains shared `loading` and `error` state.
- Exposes async functions that call backend endpoints under `/sakverse/tdm`.
- Each function performs a `fetch` with `credentials: 'include'`, parses JSON where applicable, throws on non-OK responses, updates `error`, and resets `loading` in `finally`.
- `downloadTable` differs by returning a `Blob` instead of JSON.

**Important components/functions**
- State: `loading`, `error`
- Repository operations: `getRepositories`, `createRepository`, `deleteRepository`
- Table operations: `getTableData`, `createTable`, `deleteTable`, `addTableColumn`
- Data record operations: `updateDataRecord`, `createDataRecord`, `deleteDataRecord`
- File operation: `downloadTable`
- Constants: `APIURL`, `PORT`, and `API_BASE`; note `APIURL` and `PORT` are defined but not used in the shown code.

**Relation to overall project**
- It likely serves as the client-side data-access layer for a TDM feature, allowing UI components to manage repositories, tables, columns, records, and table downloads through a consistent hook interface. The provided content does not show which components consume it or backend implementation details.


## Folder: work-main/src/Pages/Auth

### work-main/src/Pages/Auth/Login.jsx

This file implements the **Login page** for the application.

**What it does**
- Renders a full-screen login UI with an animated background, Saksoft branding, a typewriter headline, and a username/password form.
- Manages local form state for `username` and password (via `passwordRef`), plus password visibility toggle.
- Calls `login(username, password)` from `useAuthContext()` on submit.
- Shows loading state and auth error messages.
- Redirects already-authenticated users away from `/login`: admins go to `/Admin/Projects`, others go to `/`.
- Sets the document title to “SAKSOFT AI SDLC PLATFORM”.

**Important components/functions**
- `Login` — main page component.
- `AnimatedBackground` — styled component providing the animated radial-gradient background.
- `handleSubmit` — form submission handler.
- `handleKeyPress` — Enter-key handling for username/password fields.
- `togglePasswordVisibility` — toggles password input type.
- Two `useEffect` hooks — one sets the page title; one handles authenticated redirect.

**Relation to overall project**
- Located under `Pages/Auth`, so it is the authentication entry point.
- Depends on `useAuthContext` for login state and actions.
- Uses React Router (`useNavigate`, `useLocation`) for post-login navigation and redirect behavior.
- Likely connects to protected routes elsewhere by gating access through authentication state.


## Folder: work-main/src/Pages/Automation

### work-main/src/Pages/Automation/AutomationPage.jsx

This file defines the main `AutomationPage` React component for an automation testing workflow.

**What it does**
- Renders the automation page layout with a left panel (test scenario + execution logs/steps) and a right panel (live view, success/failure states, or ready-to-execute state).
- Manages execution lifecycle state: `executionId`, `sessionId`, polling status, executing flag, local steps, edit mode, loading actions, clone modal state, and row number.
- Polls execution results every 10 seconds while an execution is active, updating `executionData` and stopping on `SUCCESS`, `FAILED`, or non-running statuses.
- Supports executing a test, cloning an executed test, reordering/deleting/updating steps, adding steps, and downloading an HTML report.
- Uses optimistic UI updates for step reorder/delete/update operations, with rollback on failure.
- Resets execution-related state when `testCaseId` changes.

**Important components / pieces**
- `AutomationPage` (default export)
- `EditModeContext` (context for edit mode)
- Child components: `TestScenario`, `StepList`, `LiveView`, `GIFoption`, `StatusIndicator` (Navbar), `Failed`, `AddStepModal`
- Hook: `useAutomationFlow`
- Key handlers: `handleExecute`, `handleCloneTest`, `handleDrop`, `handleDeleteStep`, `handleAddStep`, `handleUpdatePlannedStep`, `handleUpdateExecutionStep`, `handleDownloadReport`

**Relation to overall project**
- It appears to be a page-level component in the `work-main` frontend for running and inspecting automated test cases.
- It coordinates test scenario display, step-level execution logs, live execution view, and post-execution reporting within a project/test-case context (`projectId`, `testCaseId`, `selectedStoryId`).

### work-main/src/Pages/Automation/index.jsx

This file is the index/entry component for the Automation page. It reads query parameters (`projectId`, `selectedStoryId`, `testCaseId`, `source`), and when `source` is `"tcg"` and all required IDs are present, it calls `getTestScenario` from `useAutomationFlow` to load a test scenario into state. It then renders `AutomationPage`, passing the loaded or fallback scenario plus the IDs. The whole page is wrapped in `ProtectedProjectRoute` with `paramType="query"`, and a `ToastContainer` is rendered for notifications.

Important parts:
- `Index` component
- `useEffect` that conditionally fetches the test scenario for TCG source
- `executionData` / `testScenario` state and fallback objects
- `AutomationPage` as the main rendered view
- `ProtectedProjectRoute` for route protection
- `ToastContainer` for toast notifications
- `useAutomationFlow` hook providing `getTestScenario`

In relation to the overall project, this appears to be the Automation feature’s page-level controller: it connects route/query context, protected project access, scenario loading, and the Automation UI component.


## Folder: work-main/src/Pages/Automation/components

### work-main/src/Pages/Automation/components/AddStepModal.jsx

This file defines a React modal component, `AddStepModal`, used to create a new automation step.

What it does:
- Renders a modal when `isOpen` is true.
- Collects `step_type`, `intent`, `target`, and `value` from the user.
- Provides a dropdown of predefined step types (`STEP_TYPES`), including a `CUSTOM` type.
- Validates that `intent`, `target`, and `step_type` are present before submission.
- Calls `onAdd` with the normalized step data, where `step_type` is lowercased.
- Shows success/error toasts and resets the form after successful submission.
- For `CUSTOM`, renders a code-like textarea with line numbers and Tab-key indentation support; otherwise renders a simple value input.

Important parts:
- `STEP_TYPES`: list of available step types and metadata.
- `AddStepModal`: main component with props `isOpen`, `onClose`, `onAdd`.
- Form state and validation logic (`form`, `errors`, `validateForm`, `isFormValid`).
- `handleSubmit`: validates, submits, closes, and resets.
- Dropdown handling and outside-click behavior.

Relation to overall project:
- Based on its path (`work-main/src/Pages/Automation/components/AddStepModal.jsx`) and props, it is likely used within the Automation page/feature to add steps to an automation workflow. The provided content does not show its parent usage or backend integration.

### work-main/src/Pages/Automation/components/Navbar.jsx

This file defines a React component, `AutomationNavbar`, used as the top navigation/control bar for an automation test execution page.

**What it does**
- Renders the app logo/title and a set of execution controls.
- Shows execution status as a badge (`Failed`, `Passed`, `Not Started`, `Running`, or `Retry`) based on `failedSteps`, `totalSteps`, `completedSteps`, and `status`.
- Provides an Execute/Re-run/Retry button that calls `onExecute`, with spinner/disabled states while running.
- Shows a progress bar when `totalSteps > 0`.
- Lets the user select a “Row” number (0–10, where 0 displays as `null`) and notifies the parent via `onNumberChange`.
- Supports cloning a test through a modal that collects a source execution ID and calls `onClone`.
- Provides profile dropdown actions: clone test, open Test Data Manager, and logout.
- Conditionally shows a BUG button when `failedSteps > 0`; clicking it sends a hardcoded bug payload to a webhook and displays the returned `jiraKey`.
- Shows a Download Report button that calls `onDownloadReport`, enabled only when `status === 'SUCCESS'`.
- Ensures a `projectId` query parameter exists by defaulting to the first project from `useUserData()`.

**Important parts**
- Props: `status`, `totalSteps`, `completedSteps`, `onExecute`, `failedSteps`, `onNumberChange`, `isEditMode`, `setIsEditMode`, `onClone`, `isCloning`, `onDownloadReport`.
- Local state: submission/loading flags, logout visibility, selected row number, clone modal state, source execution ID, bug submission state, and Jira key.
- Helper functions: `getTestResultBadge`, `getButtonConfig`, `handleExecute`, `handleCloneClick`, `handleCloneSubmit`, `handleBugClick`, `handleNumberChange`, profile/logout handlers.
- Clone modal and profile dropdown UI.

**Relation to overall project**
- It appears to be the control surface for an automation test execution workflow, coordinating with a parent page through callbacks.
- It integrates project selection via URL search params and user data, test execution status/progress, cloning, bug triage/reporting, and test data management navigation.

### work-main/src/Pages/Automation/components/StepDetail.jsx

This file defines a React component named `StepDetail` used to display and interact with a single automation step.

**What it does**
- Renders a collapsible step card with a status badge and status-based styling (`passed`, `failed`, `running`, `pending`).
- Shows planned step fields (`intent`, `target`, `value`) and, when available, executed result fields (`target`, `value`, `data`, `error`).
- Supports editing planned step fields and selected execution result fields, with Save/Cancel controls.
- Supports copying individual fields or a combined “full step text” to the clipboard.
- Supports enabling/disabling a step, deleting a step with confirmation, and viewing a screenshot in a modal.
- Hides certain edit/delete/enable controls when `executionStatus === "IN_PROGRESS"`.

**Important parts**
- `STATUS_STYLES`: maps step status to Tailwind classes and icons.
- `StepDetail` props: `step`, `status`, `result`, `isEditMode`, `onUpdatePlannedStep`, `onUpdateExecutionStep`, `onDelete`, `executionStatus`.
- Local state: expansion, screenshot visibility, delete confirmation, copied state, editing flags, editable step/result.
- Effects: sync `editableStep` from `step` while preserving local `enabled`; sync `editableResult` only when `result` has content.
- Handlers: `handleSaveStep`, `handleSaveResult`, `handleAbilityToggle`, `handleDelete`, `handleCopy`, `buildFullStepText`.
- UI sections: header, planned section, executed section, screenshot section, delete confirmation modal, screenshot modal.

**Relation to overall project**
- Located under `work-main/src/Pages/Automation/components/`, so it is likely a UI component within the Automation page area.
- It appears to represent one step in an automation workflow, combining planned instructions and execution results, and allowing user edits and status-aware interactions.

### work-main/src/Pages/Automation/components/StepList.jsx

This file defines a React component, `StepList`, that renders an ordered list of automation steps and their execution status.

**What it does**
- Receives `steps`, `executionData`, drag state, loading state, and callbacks for adding, deleting, updating, and reordering steps.
- Builds a lookup map (`resultsByStepId`) from `executionData.results`, keyed by result `id` (treated as `step_id`), choosing the result with the highest `execution_order` when duplicates exist.
- Derives each step’s display status from its matching result, falling back to the step’s own `execution_status` when no result exists.
- Renders an empty-state message when there are no steps.
- In edit mode, renders “Add Step” dividers above/between steps and supports drag-and-drop reordering with visual drop indicators and loading overlays.
- Renders each step through `StepDetail`, passing the step, matched result, derived status, edit mode, execution status, and update/delete callbacks.

**Important components**
- `StepList`: main list renderer and status/result lookup logic.
- `AddStepDivider`: small reusable divider with an “Add Step” button and loading spinner.

**Relation to overall project**
- It is part of the Automation page UI (`work-main/src/Pages/Automation/components/StepList.jsx`), specifically the step-management/execution view.
- It connects plan steps to execution results and supports edit-mode interactions such as adding, deleting, updating, and reordering steps.

### work-main/src/Pages/Automation/components/StepResult.jsx

## Analysis of `work-main/src/Pages/Automation/components/StepResult.jsx`

### What this file does
This file defines a React functional component named `StepResult`. It takes no props and renders a single `<div>` containing the text "StepResult". It is exported as the default export.

### Important components
- **`StepResult`** — the only component defined; a stateless functional component with no props, state, or logic.

### Relation to the overall project
Based solely on the file path (`work-main/src/Pages/Automation/components/StepResult.jsx`), this component appears to belong to an "Automation" page/feature area and is located in a `components` subfolder, suggesting it is intended as a reusable UI piece within that feature. However, the provided content does not show how it is imported or used elsewhere, so its exact role in the project cannot be determined from this file alone. The current implementation is a placeholder/stub.


## Folder: work-main/src/Pages/Automation/components

### work-main/src/Pages/Automation/components/TestScenario.jsx

This file defines a React component, `TestScenario`, for displaying and editing a test case scenario.

**What it does**
- Receives `data`, `testCaseId`, `Scenario`, `status`, and `failedSteps`.
- Keeps local editable form state (`formData`) synced with incoming `data`.
- Notifies a parent via the `Scenario` callback whenever key fields change.
- Supports editing summary-related fields through accordions: Test Data, Manual Steps, and Expected Result.
- Saves edits through `useUpdateTestCase`, sending a constructed `postData` object.
- Disables editing when `status` is `"SUCCESS"` or `"IN_PROGRESS"` and `failedSteps === 0`.

**Important components**
- `TestScenario`: main component handling state, editing, saving, and read-only logic.
- `AccordionSection`: reusable collapsible section wrapper with optional count.
- `ListItems`: reusable editable/non-editable list renderer used for Test Data and Manual Steps.

**Relation to overall project**
- Located under `Pages/Automation/components`, so it is part of the Automation area.
- It appears to be a UI piece for viewing/editing test case details and reporting scenario changes to a parent component, while integrating with test-case update functionality.


## Folder: work-main/src/Pages/Automation/components/RightPanel

### work-main/src/Pages/Automation/components/RightPanel/Failed.jsx

This file defines a React component named `Failed` that renders a full-screen failure state UI. It accepts an `onExecute` prop and displays an “Execution Failed” message with a warning icon and a “Re-try” button that calls `onExecute` when clicked.

Important parts:
- `Failed` component
- `onExecute` prop used by the retry button
- Tailwind-styled layout and red-themed failure UI

Based on its path (`work-main/src/Pages/Automation/components/RightPanel/Failed.jsx`), it likely represents a failed execution state within an Automation page’s right panel, though the provided content only confirms its UI and retry behavior.

### work-main/src/Pages/Automation/components/RightPanel/GIFoption.jsx

This file defines a React component named `GIFoption` that displays a screenshot-based, slideshow-style preview of test execution results.

What it does:
- Accepts `results`, `testCaseId`, `totalSteps`, `completedSteps`, and `failedSteps` as props.
- Filters `results` to items with a `screenshot`, mapping them into screenshot objects with `image`, `step`, `status`, and `index`.
- Maintains playback state: current index, playing/paused, speed, finished state, and fullscreen state.
- Auto-advances screenshots on an interval while playing, stopping at the last screenshot.
- Supports play/pause, replay after finishing, speed selection, fullscreen toggle, and keyboard shortcuts for space and Escape.
- Renders a fallback message when no screenshots are available.
- Displays the current screenshot, step information, execution stats, speed control, and playback controls.

Important components/elements:
- `GIFoption` default-exported React component.
- `containerRef` for fullscreen container handling.
- Screenshot extraction logic from `results`.
- Auto-play `useEffect` interval.
- Fullscreen change listener.
- Keyboard shortcut listener.
- Main image display with overlay controls.
- Header with test case ID and step statistics.

Relation to overall project:
- Based on its file path (`work-main/src/Pages/Automation/components/RightPanel/GIFoption.jsx`) and props, it appears to be part of the Automation feature’s right panel, used to preview test execution screenshots and progress for a test case. The provided file alone does not show where it is imported or how it is wired into the larger application.

### work-main/src/Pages/Automation/components/RightPanel/LiveView.jsx

This file defines a React component, `LiveView`, used to display a live browser/automation session stream.

**What it does**
- Connects to a WebSocket at `/view/{sessionId}` and receives binary frame data.
- Converts each received `ArrayBuffer` into a base64 data URL and draws it onto a `<canvas>`.
- Tracks and displays connection status, FPS, frame count, elapsed duration, step progress, and fullscreen state.
- Reconnects automatically after WebSocket close with a 2-second delay.
- Supports fullscreen toggling for the stream container.
- Shows a placeholder canvas with the WebSocket URL before/while connecting.

**Important components/functions**
- `LiveView`: main component; accepts `totalSteps`, `completedSteps`, `status`, and `sessionId`.
- `Stat`: small presentational component for labeled metric cards.
- Utilities: `formatDuration`, `getWebSocketUrl`, `arrayBufferToDataUrl`.

**Relation to overall project**
- Located under `Pages/Automation/components/RightPanel`, so it appears to be the right-panel live preview for an automation run/session.
- It depends on a backend WebSocket stream identified by `sessionId` and renders automation progress metrics passed as props.


## Folder: work-main/src/Pages/Automation/components/StepDetail

### work-main/src/Pages/Automation/components/StepDetail/DeleteConfirmModal.jsx

This file defines a small React confirmation modal component named `DeleteConfirmModal`.

- **What it does:** It renders a fixed overlay with a dialog asking “Are you sure you want to delete this step?” and provides two buttons: “Cancel” and “Delete”. Clicking them calls the `onCancel` and `onConfirm` props respectively.
- **Important components:** The default-exported `DeleteConfirmModal` component, which accepts `onConfirm` and `onCancel` callback props.
- **Project relation:** Based on its file path under `Pages/Automation/components/StepDetail`, it is likely used within the Automation StepDetail UI to confirm deletion of a step. The provided content does not show where it is imported or used.

### work-main/src/Pages/Automation/components/StepDetail/ExecutedSection.jsx

This file defines a React component, `ExecutedSection`, used in the Automation area under `StepDetail`. It displays an executed step result and supports editing/copying certain fields.

What it does:
- Receives `result`, `isEditable`, `onUpdateResult`, `onSaveResult`, `onCopy`, and `copied` as props.
- Maintains local editing state (`isEditing`) and a local copy of the result (`localResult`).
- Renders fields for `target`, `value`, `data`, and conditionally `error`.
- Hides empty non-editing fields.
- In edit mode, shows textareas for non-error fields and Save/Cancel buttons.
- In view mode, shows values as code blocks and allows copying non-error values.
- Calls `onSaveResult` and `onUpdateResult` when saving.

Important parts:
- `ExecutedSection`: main component.
- `handleSave`: saves local result, updates parent result, exits edit mode.
- `handleCancel`: discards local edits and exits edit mode.
- `renderField`: renders an individual result field, including styling, copy button, and edit/view behavior.

Likely relation to the project:
- It appears to be a detail view component for an automation step’s executed output, allowing users to inspect and optionally edit result values such as target, value, data, and error.

### work-main/src/Pages/Automation/components/StepDetail/PlannedSection.jsx

This file defines a React component, `PlannedSection`, used to display and optionally edit a step’s planned fields: `intent`, `target`, and `value`.

Important parts:
- Props: `step`, `isEditMode`, `isEditable`, `onUpdateStep`, `onSaveStep`
- Local state: `isEditing` and `localStep`
- `handleSave`: saves `localStep` via `onSaveStep`, updates via `onUpdateStep`, then exits editing
- `handleCancel`: resets `localStep` to `step` and exits editing
- `getFieldLabel`: labels `value` as `script` when `step.step_type === "custom"`
- `hasContent`: shows a field while editing or when the step already has that field
- Renders a “Planned” section with Edit/Save/Cancel controls when `isEditable`, and textareas or code blocks for each field

Relation to the project: Based on its path and props, it appears to be a detail/editing subcomponent within the Automation area, specifically for showing and editing planned step data in a step detail view.

### work-main/src/Pages/Automation/components/StepDetail/ScreenshotModal.jsx

This file defines a React component named `ScreenshotModal` that displays a screenshot in a full-screen modal overlay.

Important parts:
- Props: `screenshot`, `stepNumber`, `stepIntent`, and `onClose`.
- A fixed overlay container with a dark background.
- A close button using `AiOutlineClose` that calls `onClose`.
- An `<img>` rendering the screenshot as a base64 WebP data URL.
- A footer showing `Step {stepNumber}: {stepIntent}`.

Based on its path under `Pages/Automation/components/StepDetail/`, it likely supports a step detail view in the Automation section by showing a screenshot for a specific step.

### work-main/src/Pages/Automation/components/StepDetail/StepContent.jsx

This file defines a React component, `StepContent`, used in the Automation area to display and edit details for a single automation step.

What it does:
- Receives a `step`, `result`, edit mode, execution status, and update callbacks.
- Keeps local editable copies of `step` and `result`, syncing them when props change.
- Provides a “copy” button that copies a formatted text representation of the planned and executed step details.
- Renders `PlannedSection` for planned step data and, when execution result fields exist, `ExecutedSection` for executed result data.
- Shows a “View Screenshot” button when a screenshot is present in the result.
- Disables editing while `executionStatus === "IN_PROGRESS"`.

Important components/elements:
- `StepContent` itself.
- `PlannedSection` and `ExecutedSection` child components.
- Local state: `copied`, `editableStep`, `editableResult`.
- Handlers: `handleCopy`, `buildFullStepText`, save callbacks passed to child sections.

Relation to overall project:
- It appears to be part of the Automation feature’s step detail UI, coordinating planned step editing and executed result display/editing for an individual step.


## Folder: work-main/src/Pages/Automation/components/StepDetail

### work-main/src/Pages/Automation/components/StepDetail/StepHeader.jsx

This file defines a React component, `StepHeader`, used as the header row for an automation step in the Automation page’s step-detail UI.

What it does:
- Renders step metadata such as step number, step type, intent, and optional timestamp.
- Shows a tooltip for the step type using the local `STEP_TYPES` lookup table.
- Provides interaction controls: drag handle and delete button when editable, enable/disable toggle, status badge, and an accordion open/close toggle.
- Calls parent-provided callbacks (`onToggleOpen`, `onDeleteRequest`, `onToggleAbility`) instead of managing that state itself.

Important components/elements:
- `STEP_TYPES`: local array of supported step types with labels, icons, and descriptions.
- `StepHeader`: main presentational component receiving props like `step`, `statusStyle`, `isEditMode`, `executionStatus`, `isOpen`, and event handlers.

Relation to overall project:
- Located under `Pages/Automation/components/StepDetail`, so it is part of the Automation feature’s step detail presentation layer.
- It appears designed to be composed by a parent component that supplies step data, status styling, edit/execution state, and action handlers.

### work-main/src/Pages/Automation/components/StepDetail/constants.js

This file defines and exports a `STATUS_STYLES` object that maps step statuses (`passed`, `failed`, `running`, `pending`) to Tailwind CSS classes and an icon character for background, border, text color, and status icon.

Important component:
- `STATUS_STYLES`: a lookup table for visual styling based on status.

Relation to overall project: Based on its path under `Pages/Automation/components/StepDetail/`, it likely supports the StepDetail UI by providing consistent status-based styling/icons, though the provided content only shows the constants themselves.

### work-main/src/Pages/Automation/components/StepDetail/index.jsx

This file defines a React component, `StepDetail`, used in the Automation area. It renders a single automation step as an expandable card whose visual style depends on the step’s status.

What it does:
- Holds local UI state for whether the step is expanded (`isOpen`), whether the screenshot modal is shown, and whether the delete confirmation modal is shown.
- Derives a status style from `STATUS_STYLES` based on the `status` prop.
- Renders `StepHeader` with step metadata, status, edit mode, execution status, toggle, delete request, and enabled toggle.
- Conditionally renders `StepContent` when expanded, passing the step, result, edit mode, execution status, update callbacks, and screenshot trigger.
- Conditionally renders `DeleteConfirmModal` and `ScreenshotModal` (only when a screenshot exists in `result`).
- Calls `onDelete` when deletion is confirmed.

Important components used:
- `StepHeader`
- `StepContent`
- `DeleteConfirmModal`
- `ScreenshotModal`
- `STATUS_STYLES` from `./constants`

Project relation:
- Based on its path under `Pages/Automation/components/StepDetail`, it appears to be a detail view for an individual step within an automation workflow, supporting both planned-step editing and execution-result display, including screenshots and deletion.


## Folder: work-main/src/Pages/Dashboard

### work-main/src/Pages/Dashboard/index.jsx

This file defines the Dashboard page component (`WelcomePage`) for displaying a user’s manual projects.

**What it does**
- Fetches project data, loading, and error state from `useUserDataContext`.
- Filters projects to those with `project_type === 'Manual'`.
- Lets users expand/collapse each project to view details.
- Navigates to `/ManualProject/{id}` when “Open” is clicked, or `/error/unauthorized` if the project is not found.
- Shows loading and error states.

**Important components**
- `WelcomePage`: main page component; manages expanded project IDs and renders the project list.
- `ProjectItem`: expandable row for a project, showing name, role, and chevron.
- `ProjectDetails`: expanded panel showing project type, integrations, and an “Open” button.

**Relation to overall project**
- It appears to be the dashboard entry point for manual projects, using shared user/project context and React Router navigation to open a selected manual project.


## Folder: work-main/src/Pages/ManualProject

### work-main/src/Pages/ManualProject/footer.jsx

This file defines a small React functional component named `footer` that renders a fixed bottom banner with the disclaimer text “Sakverse can make mistakes. Please review important details.” It uses Tailwind-style classes for styling and positioning, and exports the component as the default export.

Important parts:
- The `footer` function component.
- A single `div` with fixed bottom positioning, centered text, small white text, dark background, top border, and `z-10`.
- The disclaimer message.

Based only on the provided content, it appears to be a footer/disclaimer UI element likely used within the `ManualProject` page area, but the exact usage or integration is not shown.

### work-main/src/Pages/ManualProject/index.jsx

This file is the main page component for the Manual Project view. It orchestrates the page layout and state for a selected project, including sidebar story navigation, story selection, content display, optional test suite view, and footer.

Important parts:
- Uses `useParams`, `useNavigate`, and `useLocation` to read `projectId` and manage navigation between the main manual project route and the testsuite route.
- Reads project/user data from `useUserDataContext` and auth data from `useAuthContext`.
- Fetches user stories with `useUserStoriesData` and content with `useFetchData`.
- Maintains state for `sidebarOpen`, `selectedStory`, `showSuiteState`, and `reloadContent`.
- Derives integration details from the current project, such as LLM/TM/PM enabled status, tool names, and custom IDs.
- Renders `Stories`, `TextArea`, `Home`, `Suite`, `Charts`, `RequirementTable`, `Content`, `Footer`, and `ToastContainer`.
- Provides handlers for selecting/clearing stories, reloading data, and opening/closing the suite view.

In relation to the overall project, this component appears to be the central container for the manual project workflow, coordinating navigation, data fetching, story selection, and conditional rendering of project content, charts, requirements, and test suite functionality.

### work-main/src/Pages/ManualProject/useFetchData.js

This file defines two React custom hooks used in the `ManualProject` page area.

- `useFetchData(selectedStoryId, projectId)` fetches an individual story’s data from `/sakverse/project/Get_update`, decodes the response as JSON, stores `jsonData.message`, and exposes loading/error state plus `refetch` and `GetUpdate` for forced refresh.
- `useUserStoriesData(projectId)` fetches a project’s user stories list from `/sakverse/project/us_list`, sorts the returned list by `_id` in descending order, and exposes loading/error state plus `refetch`.

Overall, it likely supports the ManualProject UI by loading a selected story’s details and the project’s user stories list, with credentials included in requests.


## Folder: work-main/src/Pages/ManualProject/Home

### work-main/src/Pages/ManualProject/Home/Home.jsx

This file defines a React dashboard component for a manual project. It renders project summary information, integration cards, progress metrics, the latest user story, a suite execution status message, and a table of recent user stories. It also contains handlers for running a test suite and downloading a suite report, though the buttons that trigger them are commented out in the JSX.

Important components/functions:
- `StatusBadge`: displays a colored status label.
- `MetricCard`: displays a labeled numeric metric.
- `IntegrationCard`: displays an integration tool, type, and active/inactive state.
- `StoryRow`: renders one user story row, with expand/collapse and selection actions.
- `Home`: main component; manages expanded rows, report loading, and suite messages; computes metrics from `userStories`; handles story selection and suite/report actions.

Relation to overall project: It is located under `work-main/src/Pages/ManualProject/Home/`, so it likely serves as the home/dashboard page for a manual project workflow. It uses `useAutomationFlow` for suite execution/reporting and receives project/story data through props, suggesting it is part of a larger React application with project and automation features.

### work-main/src/Pages/ManualProject/Home/reports.jsx

This file defines a React component named `HtmlPreviewer` (default export). It:

- Initializes `htmlCode` state with a built-in default HTML document.
- Renders a navbar with an “HTML Previewer” title and a “Download HTML” button.
- Previews the current HTML in an `<iframe>` using `srcDoc={htmlCode}`.
- Downloads the current HTML as `page.html` via a Blob and temporary anchor element.

Important parts:
- `HtmlPreviewer` component
- `htmlCode` state and `setHtmlCode`
- `handleDownload` function
- `defaultHtml` constant
- `styles` object used for inline styling

Based only on the provided content, the file appears to be a standalone HTML preview/download utility component. Its path (`work-main/src/Pages/ManualProject/Home/reports.jsx`) suggests it may be located in a reports-related area of the project, but the content itself does not show how it is imported, routed, or used elsewhere.


## Folder: work-main/src/Pages/ManualProject/Suite

### work-main/src/Pages/ManualProject/Suite/CreateSuiteModal.jsx

This file defines a React modal component, `CreateSuiteModal`, used to create a test suite for a project.

What it does:
- Renders a modal when `isOpen` is true.
- Collects suite metadata: suite name, description, and a disabled “Created By” field derived from the `User` prop.
- Lets users add, remove, reorder, and edit test items, each with `execution_id`, `data_row_id`, `execution_order`, and `enabled`.
- Validates required fields before submission.
- Builds a payload and calls `onCreateSuite(payload)`, then closes the modal on success.
- Shows loading and error states.

Important parts:
- State management with `useState` for form fields, items, loading, and errors.
- `useEffect` hooks to set `createdBy` from `User` and reset the form when the modal opens.
- Helper functions: `addItem`, `removeItem`, `updateItem`, `moveItem`, `validateForm`, `handleSubmit`, and `resetForm`.
- UI sections for basic information and test items, plus footer actions.

Relation to overall project:
- Located under `work-main/src/Pages/ManualProject/Suite/`, so it likely supports a Manual Project suite creation workflow.
- It is a reusable modal component invoked with project/user context and a suite creation callback.
- The `availableExecutions` prop is accepted but not used in the shown implementation.

### work-main/src/Pages/ManualProject/Suite/Suite.jsx

This file implements the **Test Suites page** for a manual project. It fetches and displays suites for a given `projectId`, shows loading/error/empty states, supports refresh, creation, execution, report download, and a detail modal.

Important parts:
- **`Suite` component**: main page container and state manager.
- **`useSuite` hook**: provides suite API calls (`getSuiteList`, `executeSuite`, `getSuiteReportJson`, `createSuite`).
- **Polling logic**: refreshes reports for suites whose status is `RUNNING`.
- **`SuiteCard`**: renders each suite tile with status/report data.
- **`CreateSuiteModal`**: creates a new suite.
- **`ExecutionModal`**: confirms/starts suite execution.
- **`SuiteDetailModal`**: shows richer suite detail/report data, fetched separately with abort/stale-response handling.
- **Report download**: fetches full report (`mode='all'`), transforms it, and downloads an HTML file.

Relation to overall project: it is a project-scoped UI for managing and monitoring test suites, integrating suite CRUD/execution/report APIs and reusable modal/card components.

### work-main/src/Pages/ManualProject/Suite/constants.js

This file defines shared constants for the ManualProject/Suite area.

- `POLL_INTERVAL_MS`: a polling interval value of 300000 ms.
- `STATUS_STYLES`, `EXEC_STATUS_STYLES`, `CASE_STATUS_STYLES`, and `ACTION_STYLES`: lookup maps from status/action names to Tailwind CSS class strings for badges, dots, or action styling.
- `DEFAULT_STYLE`: fallback styling object.
- `getStyle(map, key)`: helper that returns the matching style from a map or `DEFAULT_STYLE` when the key is missing.

It likely supports UI rendering in the ManualProject/Suite feature by centralizing status/action visual styling and polling timing, so components can consistently display suite, execution, case, and action states.

### work-main/src/Pages/ManualProject/Suite/index.jsx

This file is a small re-export (barrel) module: it takes the default export from `./Suite` and re-exports it as this file’s default export.

Important components: the only identifiable component is the default export coming from `./Suite`; this file itself does not define any component.

Relation to the overall project: it likely serves as a convenient entry point for importing the `Suite` page/component under `work-main/src/Pages/ManualProject/Suite/`, but the provided content does not show how it is consumed elsewhere.

### work-main/src/Pages/ManualProject/Suite/indexmodals.jsx

This file implements the **Test Suites page** for a manual project. It fetches and displays suites, shows execution/report status, supports creating suites, executing suites, viewing detailed execution reports, and downloading an HTML report.

Important components:
- **`Suite`** (main component): loads suites via `useSuite`, manages state, polling for running suites, create/execute/download actions, and renders suite cards.
- **`SuiteDetailModal`**: detailed view with suite info, execution metadata, donut chart summary, searchable/filterable test case executions, and screenshot lightbox.
- **`ExecutionModal`**: prompts for max parallel executions before running a suite.
- **`TestCaseAccordion` / `StepRow`**: render test case and step-level execution details, statuses, errors, targets, values, and screenshots.
- Supporting UI helpers: `DonutChart`, `Lightbox`, `ScreenshotThumb`, `CopyButton`.

Relation to overall project: it appears to be a frontend page under `ManualProject/Suite`, consuming suite APIs through `useSuite` and report/HTML helpers, providing the UI for managing and inspecting manual test suite executions.


## Folder: work-main/src/Pages/ManualProject/Suite

### work-main/src/Pages/ManualProject/Suite/indexog.jsx

This file implements a React page for managing and executing **test suites** within a manual project.

**What it does**
- Fetches a list of suites for a given `projectId` using `useSuite().getSuiteList`.
- Normalizes the API response into a list and total count via `extractSuiteList`.
- Loads execution reports for suites via `getSuiteReportJson` and stores them in `suiteReports`.
- Polls reports every 10 minutes (`POLL_INTERVAL_MS`) while any suite has status `RUNNING`.
- Allows creating a suite through `CreateSuiteModal`.
- Allows executing a suite through `ExecutionModal`, including choosing max parallel executions (1–6).
- Allows downloading a suite report as an HTML file using `generateExecutionHTML` and `transformReportData`.
- Displays suite cards with execution status, test case counts, passed/failed counts, and action buttons.

**Important components/functions**
- `Suite` (default export): main page component; manages state, fetching, polling, execution, download, and rendering.
- `ExecutionModal`: modal for selecting parallel execution count and triggering suite execution.
- `extractSuiteList`: normalizes suite list API responses.
- `refreshReports`: fetches reports for multiple suite IDs and merges them into state.
- `handleExecuteSuite`, `handleDownloadReport`, `handleCreateSuite`: core user actions.
- `STATUS_STYLES` / `EXEC_STATUS_STYLES`: status badge styling maps.

**Relation to overall project**
- It is a UI page under `Pages/ManualProject/Suite`, likely part of a manual testing workflow.
- It depends on `useSuite` for backend suite operations and on helper functions for report HTML generation.
- It integrates suite creation, execution, status tracking, and report download into one dashboard-like view.

### work-main/src/Pages/ManualProject/Suite/utils.js

This file is a utility module for the ManualProject Suite page. It exports small helper functions used to normalize and format suite-related data.

Important components:
- `getSuiteId`: returns `suite.suite_id` if present, otherwise `suite.id`.
- `formatDate`: formats a date string into an `en-IN` locale string in the `Asia/Kolkata` time zone, treating naive strings as UTC.
- `formatDuration`: calculates elapsed time between `start` and `end`, returning minutes/seconds or `N/A`.
- `truncateMiddle`: shortens long strings by keeping characters at both ends.
- `looksLikeBase64Image` and `toImageSrc`: detect and convert base64 image strings into usable image sources.
- `extractSuiteList`: normalizes an API response into `{ list, total }`, supporting arrays or nested `suites`/`total_suites` fields.

Relation to overall project: based on its path, it supports the ManualProject Suite UI by handling common data formatting, image handling, and response normalization for suite records.


## Folder: work-main/src/Pages/ManualProject/Suite/components

### work-main/src/Pages/ManualProject/Suite/components/Lightbox.jsx

This file defines reusable React UI components for a ManualProject Suite feature.

Important components:
- `CopyButton`: copies provided text to the clipboard, shows a check icon briefly after copying, and renders nothing if no text is provided.
- `DonutChart`: renders an SVG donut chart from `passed`, `failed`, and `skipped` counts, with color-coded segments and a centered pass-rate percentage.
- `Lightbox`: renders a full-screen image overlay that closes when clicking the backdrop or close button; clicking the image itself does not close it.
- `ScreenshotThumb`: renders a small screenshot thumbnail button that opens the image via `onOpen`, or a placeholder when no image source is available.

It likely supports the ManualProject Suite UI by providing screenshot viewing, text copying, and test-result visualization. The file imports `toImageSrc` from `../utils`, indicating screenshot data may need conversion before display.

### work-main/src/Pages/ManualProject/Suite/components/SuiteCard.jsx

This file defines a React component, `SuiteCard`, used to display a single suite in the ManualProject Suite area.

What it does:
- Renders a card showing the suite name/description, execution status badge, and summary counts (test cases, passed, failed).
- Provides Execute and Report/Download buttons, with loading/disabled states.
- Calls `onCardClick`, `onExecute`, and `onDownload` callbacks, stopping propagation on button clicks.
- Uses helper functions/constants such as `getStyle`, `EXEC_STATUS_STYLES`, `STATUS_STYLES`, and `getSuiteId`.

Important components/elements:
- The main `SuiteCard` component.
- Status badge derived from `report?.suite_execution?.status`.
- Execution summary grid.
- Execute button with spinner state.
- Download button with spinner state.

Relation to overall project:
- It appears to be a presentational card component within `work-main/src/Pages/ManualProject/Suite/components/`, likely used by a parent Suite page to list suites and trigger execution/report download actions.

### work-main/src/Pages/ManualProject/Suite/components/TestCaseAccordion.jsx

This file defines a React accordion component for displaying a manual test case execution and its individual steps.

**What it does**
- `TestCaseAccordion` renders a collapsible card for one `testcase`.
- Its header shows execution ID, row number, execution intent, passed/failed step counts, and overall status.
- When expanded, it maps over `testcase.steps` and renders each as a `StepRow`.
- `StepRow` renders step details: planned intent, action, status, target/value, optional long-target code view, error message, timestamp, and a screenshot thumbnail.

**Important components**
- `StepRow`: displays one step, including status indicator, action/status badges, navigation links, long target code toggle, error block, and screenshot.
- `TestCaseAccordion`: manages open/closed state and renders the step list.

**Relation to overall project**
- It is located under `work-main/src/Pages/ManualProject/Suite/components/`, so it is a UI component for the ManualProject Suite feature, likely used to present test case execution results and step-level diagnostics.


## Folder: work-main/src/Pages/ManualProject/Suite/modals

### work-main/src/Pages/ManualProject/Suite/modals/ExecutionModal.jsx

This file defines a React modal component, `ExecutionModal`, used to confirm and configure execution of a test suite.

**What it does**
- Renders only when `isOpen` is true.
- Lets the user choose `maxParallel` (1–6) via a range slider.
- Displays the suite name and suite ID.
- On submit, calls `onExecute(suiteId, maxParallel)` and then `onClose()`.
- Shows a loading state on the execute button (`loading`), including a spinner and “Executing...” text.

**Important components/elements**
- `ExecutionModal` default export.
- Local state: `maxParallel`.
- Props: `isOpen`, `onClose`, `onExecute`, `suiteName`, `suiteId`, `loading`.
- `handleSubmit` triggers execution and closes the modal.

**Relation to overall project**
- Its path (`work-main/src/Pages/ManualProject/Suite/modals/ExecutionModal.jsx`) indicates it is part of the ManualProject Suite UI, likely invoked from a Suite page to start running a selected suite with a chosen parallelism level.

### work-main/src/Pages/ManualProject/Suite/modals/SuiteDetailModal.jsx

This file defines a React modal component, `SuiteDetailModal`, used to display detailed information about a suite and its execution report.

**What it does**
- Renders a full-screen modal when `isOpen` and `suite` are provided.
- Resets search, status filter, and lightbox state when the modal opens or the suite changes.
- Computes status counts from `report.testcases`.
- Filters test cases by status (`ALL`, `PASSED`, `FAILED`, `SKIPPED`) and by search text matching execution intent, session ID, or execution ID.
- Shows suite metadata, execution metadata, result summary counts, and a searchable/filterable list of test case executions.
- Supports downloading the report via `onDownload(suite)` and shows a downloading state.
- Supports opening images in a `Lightbox`.

**Important components / dependencies used**
- `SuiteDetailModal` itself, with props: `isOpen`, `onClose`, `suite`, `report`, `onDownload`, `downloading`.
- `TestCaseAccordion` for rendering each filtered test case.
- `Lightbox` for image viewing.
- `DonutChart` is imported but its usage is commented out in the results section.
- Utility/style helpers: `getStyle`, `STATUS_STYLES`, `EXEC_STATUS_STYLES`, `getSuiteId`, `formatDate`, `formatDuration`.
- Icons from `@fortawesome/free-solid-svg-icons`.

**Relation to overall project**
- It appears to belong to the Manual Project Suite feature area, under `work-main/src/Pages/ManualProject/Suite/modals/`.
- It acts as a detail/report viewer for a selected suite execution, combining suite information, execution status, summary metrics, and individual test case results.


## Folder: work-main/src/Pages/ManualProject/content

### work-main/src/Pages/ManualProject/content/content.jsx

This file defines the `Content` React component for a manual project page. It renders a four-stage workflow UI (`QUERY MASTER`, `STORY BUILDER`, `REQUIREMENT ANALYZER`, `TEST DESIGNER`) and conditionally displays the corresponding accordion components based on stage/status.

Key behaviors:
- Tracks local stage/status and resets UI state when the selected story, stage, or status changes.
- Refetches content when `reload` is true.
- Polls `onReloadAll` every 120 seconds while `localStatus` is `in-progress`.
- Computes each stage’s icon (`Completed`, `inprogress`, `play`, `Error`, `notStarted`) from `localStatus` and `localStage`.
- Handles play clicks by optimistically updating status/stage, calling `POST /sakverse/project/nextStep/{selectedStoryId}`, showing toast feedback, then reloading after a delay.
- Only renders an accordion when its stage icon is `inprogress` or `Completed`.

Important internal pieces:
- `getAccordionName`, `stageMap`
- `getIconForStage`
- `handlePlayClick`
- `StatusIcon`
- `renderAccordion`

In the overall project, this component appears to be the main content area for a selected manual project user story, coordinating stage progression, status display, accordion rendering, and backend refresh/polling.


## Folder: work-main/src/Pages/ManualProject/content/Accordion

### work-main/src/Pages/ManualProject/content/Accordion/QueriesAccordion.jsx

This file defines a React component, `QueriesAccordion`, used in the Manual Project page to display and edit project “Queries.”

What it does:
- Receives `data`, `isOpen`, and `toggle` props.
- Stores query items locally from `data?.qna`.
- Supports filtering queries by `knowledge_exist` (`all`, `0` for missing, `1` for exists).
- Allows editing a query’s `assumptions`/clarification in a textarea.
- Saves edits through `useUpdateQueries`, sending `{ id, answer }`.
- Shows toast messages for processing state, successful update, or failed update.
- Prevents opening the accordion when no query data exists yet.

Important components/elements:
- `Accordion` wrapper with title “Queries”.
- Filter dropdown, shown only if missing or existing knowledge queries are present.
- Query list items colored by knowledge status: red for missing, green for exists, white otherwise.
- Edit and Update icon buttons.
- Textarea for clarification editing.

Relation to overall project:
- It is part of the Manual Project content UI, specifically the Queries accordion section.
- It interacts with project query data and the `useUpdateQueries` hook to update clarifications.

### work-main/src/Pages/ManualProject/content/Accordion/RequirementDetailsAccordion.jsx

This file defines a React component, `RequirementDetailsAccordion`, used in the manual project area. It displays requirement details inside an `Accordion` titled “Features Details.”

What it does:
- Receives `data`, `selectedStoryId`, `isOpen`, and `toggle`.
- Initializes local state from `data.requirement_details`.
- Supports filtering displayed details by type: all, functional, or non-functional.
- Allows editing a detail’s `detail` field and updating it through `useUpdateRequirement`.
- Renders `data` and `test_steps` recursively via `renderValue`.
- Renders technique-specific tables via `renderDynamicTable`, with selectable categories such as Boundary Values, Equivalence Partitioning, State Transition, Decision Table, and Use Cases.
- Shows loading/error states from `useFetchData(selectedStoryId)`.

Important parts:
- `RequirementDetailsAccordion`: main component.
- `Accordion`: wrapper UI component.
- `renderValue`: recursive renderer for strings, arrays, and objects.
- `renderDynamicTable`: renders available technique detail panels.
- Hooks: `useFetchData`, `useUpdateRequirement`.

Relation to overall project:
- It appears to be part of the manual project feature-details UI, presenting and editing requirement details associated with a selected story.

### work-main/src/Pages/ManualProject/content/Accordion/TestCasesAccordion.jsx

This file defines a React component, `TestCasesAccordion`, that displays and manages test cases for a selected user story inside an accordion.

What it does:
- Receives story/test-case data and UI state through props such as `data`, `selectedStoryId`, `isOpen`, `toggle`, `projectId`, `linkedStatus`, `isTMConnected`, `TMTool`, `tmCustomId`, and `selectedStatus`.
- Maintains local state for filtering by technique, requirement, and priority; accepted test cases; expanded test-data rows; and edit-modal state.
- Syncs local `testCases` from `data.test_cases` and derives unique technique/requirement filter options.
- Supports inline editing of summary, test steps, and expected result, plus a separate `TestCaseEditModal` for editing a selected test case.
- Handles review actions: accepting/unaccepting test cases, toggling regression status, and opening an automation page for accepted cases when `linkedStatus` is true.
- Supports publishing accepted, unpublished test cases through `PublishModal` when TM is connected, with the publish button enabled only when `selectedStatus === "Completed"`.
- Renders a table of test cases with scenario, test data, test steps, expected result, automation flag, actions, and an optional Play column.

Important components/hooks used:
- `Accordion` for the collapsible container.
- `PublishModal` for publishing selected test cases.
- `TestCaseEditModal` for editing a test case.
- Hooks: `useFetchData`, `useUpdateTestCase`, `useReviewStatusUpdate`, `usePublishTestCases`, and imported `useTestConfiguration`.
- React Router’s `useNavigate` for opening automation in a new tab.

Relation to the overall project:
- It appears to be part of the Manual Project area, specifically test-case review and management for a user story.
- It connects test-case data to review, regression, automation, and optional test-management publishing workflows.
- It is a presentation/stateful component that coordinates multiple child modals and API hooks rather than defining the underlying data services.

### work-main/src/Pages/ManualProject/content/Accordion/index.jsx

This file defines a reusable React `Accordion` component.

- **What it does:** It renders a collapsible card with a clickable header showing an icon, title, and `+`/`-` indicator. When `isOpen` is true, it displays `children`. Its `handleToggle` prevents toggling and shows an alert if `children` is missing, otherwise calls `toggle`.
- **Important parts:** The default-exported `Accordion` component; the `handleToggle` function; props such as `title`, `isOpen`, `toggle`, `icon`, `children`, and `statusIcon` (the latter is accepted but not used in the shown code). It also imports `inprogress` and `completed` icons, though they are not used in the shown code.
- **Project relation:** Based on its path (`Pages/ManualProject/content/Accordion`), it appears to be part of the Manual Project page UI, likely used to display collapsible content sections. The provided file alone does not show where it is imported or used.


## Folder: work-main/src/Pages/ManualProject/content/Accordion

### work-main/src/Pages/ManualProject/content/Accordion/userStories.jsx

This file defines a React component, `UserStoryAccordion`, used in the manual project pages to display and edit a user story inside an `Accordion`.

What it does:
- Receives user story data plus project/story identifiers and UI state through props.
- Keeps a local copy of `data.user_story` and syncs it when `data` changes.
- Renders each user story field, excluding `id` and conditionally filtering `test_data`.
- Supports inline editing of fields with a textarea, then updates the field through `useUpdateUserStory`.
- Supports publishing the selected user story through `usePublishUserStory`, with a confirmation modal.
- Shows toast notifications for update/publish success or failure.
- Renders nested values recursively for strings, arrays, and objects.

Important parts:
- `UserStoryAccordion` (default export)
- `Accordion` wrapper component
- Hooks: `useUpdateUserStory`, `usePublishUserStory`
- Helper functions: `handleChange`, `handleUpdate`, `handleEdit`, `handleToggle`, `handlePublish`, `confirmPublish`, `handleConfirmPublish`, `renderValue`

Relation to overall project:
- It is part of `work-main/src/Pages/ManualProject/content/Accordion`, so it appears to be a content section for manual projects.
- It connects UI editing/publishing actions to user-story data hooks and uses shared toast feedback.


## Folder: work-main/src/Pages/ManualProject/content/Accordion/components

### work-main/src/Pages/ManualProject/content/Accordion/components/TestCaseEditModal.jsx

This file defines a React modal component, `TestCaseEditModal`, used to edit a test case’s details.

**What it does**
- Accepts props: `isOpen`, `onClose`, `testCase`, and `onSave`.
- Maintains local form state for `summary`, `test_data`, `test_steps`, and `expected_result`.
- Syncs local state from the incoming `testCase` when it changes.
- Renders a modal only when `isOpen` is true.
- Lets the user edit scenario, test data, test steps, and expected result.
- Calls `onSave` with the original `testCase` merged with edited form data when “Save” is clicked.

**Important parts**
- `formData` state and `handleChange` for controlled inputs.
- `useEffect` that initializes form values from `testCase`.
- Textarea handling that converts between newline-separated text and arrays for `test_data` and `test_steps`.
- Modal layout: header, scrollable content, footer with Cancel/Save buttons.

**Relation to overall project**
- Based on its path, it is part of the Manual Project feature, specifically within the Accordion content area, and likely supports editing test cases displayed in that UI.


## Folder: work-main/src/Pages/ManualProject/content/Accordion/components/actions

### work-main/src/Pages/ManualProject/content/Accordion/components/actions/actions.jsx

This file defines a React modal component, `ActionModal`, for viewing and editing a single test case.

**What it does**
- Renders a fixed overlay modal when `isOpen` is true and `testCase` exists.
- Displays test case details: ID, technique, scenario/summary, test data, test steps, expected result, priority, and “to be automated” status.
- Supports local editing state: clicking Edit populates `editedData` and enables textareas for summary, test data, test steps, and expected result; clicking Update calls `handleUpdateClick` and exits editing.
- Provides action controls: Accepted checkbox, Regression toggle, and an Automate button shown only when the test case is accepted.
- Disables Edit/Update and Accepted controls when the test case is published, and shows a “Published” badge.
- Calls parent-provided handlers for edit, update, checkbox, regression, and automate actions.

**Important components**
- `ActionModal` (default export): the main modal component.
- Internal state: `editedData` and `isLocalEditing`.
- Local handler wrappers: `handleLocalEditClick`, `handleLocalUpdateClick`, `handleLocalCheckboxChange`, `handleLocalRegressionClick`, `handleLocalAutomateClick`, and `handleChange`.

**Relation to overall project**
- Based on its path, it is part of the Manual Project feature, specifically within an Accordion’s actions area, likely used to inspect or modify test cases associated with a project/story context. The component accepts `projectId` and `selectedStoryId`, suggesting it may be used in that broader manual project workflow, though the provided file does not show where it is imported or rendered.


## Folder: work-main/src/Pages/ManualProject/content/Accordion/components/publish

### work-main/src/Pages/ManualProject/content/Accordion/components/publish/AdoPublishModal.jsx

This file defines a React modal component, `AdoPublishModal`, used to publish selected manual test cases to Azure DevOps.

**What it does**
- Renders only when `isOpen` is true.
- Fetches ADO test plans/suites using `useAdoTestData(userStoryId)`.
- Lets the user choose a test plan and test suite.
- Shows the provided `selectedTestCases` in a table with checkboxes.
- Initializes the checkbox selection to unpublished test cases when the modal opens.
- Validates that a plan, suite, and at least one test case are selected.
- Builds a payload containing `userstory_ref_id`, `plan_id`, `suite_id`, and selected test case IDs.
- Calls `publishTestCasesApi(payload)` and shows success/error toast messages.
- Closes the modal on successful publish.

**Important parts**
- State: `selectedPlanId`, `selectedSuiteId`, `publishSelection`, `isPublishing`.
- Derived data: `selectedPlan` and its `suites`.
- `confirmPublish`: async publish handler with validation and loading state.
- UI sections: header, plan/suite selectors, test case table, footer with Cancel/Publish buttons.

**Relation to overall project**
- Located under `ManualProject/content/Accordion/components/publish/`, so it is part of the manual project test case publishing flow.
- It connects the UI to ADO data via `useAdoTestData` and to backend publishing via the `publishTestCasesApi` prop.
- It accepts `projectId`, though the shown code does not use it.

### work-main/src/Pages/ManualProject/content/Accordion/components/publish/KiwiPublishModal.jsx

This file defines a React modal component, `KiwiPublishModal`, used to publish selected test cases.

**What it does**
- Renders a modal when `isOpen` is true.
- Loads test configuration via `useTestConfiguration(userStoryId)`.
- Builds version and test-plan dropdown options from the loaded configuration.
- Lets the user choose an existing version/test plan or create a new version/test plan.
- Shows unpublished selected test cases in a table with checkboxes.
- On “Publish Test Cases”, validates inputs, builds a payload, calls `publishTestCasesApi(payload)`, refreshes data via `GetUpdate`, marks published cases, and updates the selection.
- Shows loading/error states and a publishing loader.

**Important parts**
- State: `selectedProduct`, `selectedVersion`, `selectedTestPlan`, `isNewVersion`, `newVersionName`, `isNewTestPlan`, `newTestPlanName`, `newTestPlanParent`, `dropdownConfig`, `publishSelection`, `isPublishing`.
- Effects: initialize dropdown config from configuration data; initialize checkbox selection for unpublished test cases.
- Helpers: `findTestPlanById`, `renderIndentedPlan`, `handleAddTestPlan`, `handleCheckboxChange`.
- Main action: `confirmPublish`.
- UI sections: header, version/test-plan selectors, test-case table, footer with Cancel/Publish buttons.

**Relation to overall project**
- Located under `ManualProject/content/Accordion/components/publish`, so it is part of the manual project test-case publishing workflow.
- It connects parent-provided data/actions (`selectedTestCases`, `userStoryId`, `publishTestCasesApi`, `projectId`) with hooks (`useTestConfiguration`, `useFetchData`) to configure and publish test cases.

### work-main/src/Pages/ManualProject/content/Accordion/components/publish/publishModal.jsx

This file defines a React modal component, `PublishModal`, used to publish selected test cases. It manages local state for product/test plan/category and loading, builds a payload with the user story ID and selected test case IDs, calls `publishTestCasesApi`, and shows success/error toasts.

Important parts:
- `PublishModal`: default modal UI with a table of selected test cases (scenario and expected result) and Cancel/Publish actions.
- `KiwiPublishModal` and `AdoPublishModal`: tool-specific modal variants rendered when `tmCustomId` is `2` or `3`.
- `handlePublish`: performs the publish request and handles loading/toast feedback.

In the overall project, it appears to be part of the Manual Project accordion publish flow, allowing test cases to be published to a test management tool, with different modal implementations depending on the configured tool (`tmCustomId`).


## Folder: work-main/src/Pages/ManualProject/download

### work-main/src/Pages/ManualProject/download/DownloadExcel.jsx

This file defines a React component named `DownloadExcel` that renders a download button. When clicked, it checks whether `isStoryCompleted` is true; if not, it shows an error toast saying “Userstory not yet Completed.” If completed, it calls `downloadExcelFile(projectId, selectedStoryId)` from the `useDownloadExcel` hook, and alerts any error message if the call fails.

Important parts:
- Props: `projectId`, `selectedStoryId`, `selectedstatus`, `selectedstage`, `isStoryCompleted` (note: `selectedstatus` and `selectedstage` are accepted but not used in the shown code).
- `useDownloadExcel` hook, which provides `downloadExcelFile`.
- `showToast` for incomplete-story feedback.
- A button with a FontAwesome download icon.

Relation to the overall project: It appears to be part of the Manual Project pages, specifically a download feature for Excel files tied to a project and selected story, with a guard preventing download until the story is completed.


## Folder: work-main/src/Pages/ManualProject/testcase

### work-main/src/Pages/ManualProject/testcase/testcase.jsx

This file defines a React page component, `TestCasePage`, that displays details for a single test case.

**What it does**
- Reads `pr_id`, `selectedStoryId`, and `testcaseid` from URL search parameters.
- Fetches test case data from `/sakverse/project/Get_testcase` using those parameters, with credentials included.
- Shows loading and error states.
- Renders test case information such as ID, priority, acceptance status, requirement summary, technique, summary, test steps, expected result, test data, and additional project/story IDs.

**Important components/functions**
- `TestCasePage`: main page component.
- `getPriorityStyle`: helper that returns Tailwind classes based on priority (`high`, `medium`, `low`, default).
- The fetch logic inside `useEffect`, which depends on the three query parameters.

**Relation to overall project**
- It appears to be part of the manual project area, located under `Pages/ManualProject/testcase`.
- It is a detail view for a test case associated with a project and story, likely reached via query parameters from another page in the manual project workflow.


## Folder: work-main/src/Pages/ManualProject/textArea

### work-main/src/Pages/ManualProject/textArea/DetailModal.jsx

This file defines a React modal component, `DetailModal`, used to display detailed user-story information.

**What it does**
- Renders nothing when `isOpen` is false.
- When open, shows a modal with a header, scrollable content area, and footer.
- If `selectedStoryDetails` exists, it parses the text into:
  - **User Story**: text before the marker sections.
  - **Additional Context Provided**: text between that marker and the next marker, shown in an accordion.
  - **Detailed Fetched From Uploaded Documents**: text after that marker, shown in an accordion.
- If no special sections are present, it shows a message saying no additional context or document details are available.
- If no details are provided, it shows “No story details available.”

**Important components/functions**
- `DetailModal`: main exported component.
- `renderStorySections(text)`: helper that splits and renders the story text into sections.
- Modal UI elements: overlay, header with close button, content area, footer close button.

**Relation to overall project**
- Based on its path (`work-main/src/Pages/ManualProject/textArea/DetailModal.jsx`), it likely supports the Manual Project text-area feature by presenting complete user-story details in a modal. The provided content does not show where it is imported or used.

### work-main/src/Pages/ManualProject/textArea/StoryModal.jsx

This file defines a React modal component, `StoryModal`, used to create or select a user story for a project.

**What it does**
- Renders a modal when `isOpen` is true.
- If `isPMConnected` is true, it shows a searchable dropdown of `jiraData.tickets`, lets the user select one, and previews the selected ticket’s key, summary, status, and description.
- If not connected, it shows a textarea for manually entering a user story description.
- On submit, it validates required fields, calls `submitUserStory` from `useUserStorySubmit`, stores the returned `request_id` in `localStorage`, shows a success message, calls `onStorySubmit`, and closes the modal.
- Includes an Auto-Pilot toggle and a countdown timer while submission is in progress.

**Important parts**
- `StoryModal` component and its props: `isOpen`, `onClose`, `onStorySubmit`, `projectId`, `jiraData`, `isPMConnected`, `PMTool`.
- State for input, selected ticket, submission status, dropdown/search, and Auto-Pilot mode.
- `handleSubmit`: builds payload with `pr_id`, `user_input`, `key`, and `autopilot`, then submits.
- Ticket filtering by key or summary.
- Outside-click handling to close the dropdown.

**Relation to overall project**
- It appears to be part of the manual project workflow under `Pages/ManualProject/textArea`.
- It connects manual project creation to an external project-management tool ticket source when `isPMConnected` is true.
- It triggers user-story generation through the `useUserStorySubmit` hook and communicates completion via `onStorySubmit`.

### work-main/src/Pages/ManualProject/textArea/textArea.jsx

This file defines a React toolbar/header component named `TextArea` for a manual project page. It displays project/story metadata and provides action buttons for common workflows.

Important parts:
- **State and props**: Tracks modal visibility (`isModalOpen`, `isDetailsModalOpen`, `isChatOpen`, `isDocOpen`, `isImportOpen`), Jira/external story data, and an auth token. Receives many props such as `projectId`, `selectedStoryId`, `selectedStoryDetails`, connection flags, and callbacks.
- **External story loading**: `handleAddStoryClick` opens the story modal and, if PM is connected, fetches external stories from `/sakverse/project/externalstories/${projectId}`.
- **Story modal selection**: Uses `twoStep` when `pmCustomId === 2`, otherwise `StoryModal`.
- **Sub-components**:
  - `StoryIdButton`: shows external/internal story ID and opens `DetailModal`.
  - `DateBadges`: shows started/updated timestamps.
  - `ActionButtons`: shows Suite, document generation, chat, add story, reload, impact analysis, Excel download, and home buttons; when `isSuiteOpen`, only shows Home.
- **Sakpilot integrations**: Opens `ChatSession`, `GenerateDoc`, and `ImportAnalysis`, obtaining an auth token via `loginAndGetToken` when needed.
- **Suite navigation**: `handleSuiteClick` calls parent-provided `onSuiteClick`.

Relation to overall project: It appears to be the top action bar for the Manual Project area, coordinating story selection, metadata display, modal workflows, external PM story import, document/chat/impact-analysis tools, Excel export, and navigation to the Suite page.

### work-main/src/Pages/ManualProject/textArea/twoStep.jsx

This file defines a React modal component, `twoStepStoryModal`, used to create/generate a user story in two stages.

**What it does**
- Opens as a full-screen modal when `isOpen` is true.
- Stage 0 collects the main input:
  - If `isPMConnected` is true, it shows a searchable dropdown of `jiraData.tickets` and requires selecting a ticket.
  - Otherwise, it shows a textarea for a user story description.
- Stage 1 collects additional information:
  - Shows selected ticket context.
  - Allows optional file uploads.
  - Allows chat-style additional detail messages.
- On submit, it calls `twoStepSubmit` from `useUserStorySubmit_v2`, passing project ID, ticket description or user input, auto-pilot state, ticket key, additional context, and files.
- Stores `request_id` in `localStorage`, then calls `onStorySubmit` and closes the modal.
- Includes an Auto-Pilot toggle and validation/alerts for required fields.

**Important components/functions**
- `twoStepStoryModal` main component.
- `renderStageContent`, `renderUserInput`, `renderJiraDropdown`, `renderFileUploadStage`.
- `handleNextStage`, `handlePreviousStage`, `handleSubmit`, `handleFileUpload`, `removeFile`, `handleSendMessage`.
- Uses `useUserStorySubmit_v2` hook for submission.

**Relation to overall project**
- Located under `work-main/src/Pages/ManualProject/textArea/`, so it appears to be part of the manual project user-story creation flow.
- It integrates with project management ticket data (`jiraData`, `PMTool`, `isPMConnected`) and a submission hook, suggesting it bridges manual input and backend user-story generation.


## Folder: work-main/src/Pages/ManualProject/textArea/sakpilot

### work-main/src/Pages/ManualProject/textArea/sakpilot/chatsession.jsx

This file defines a React `ChatSession` component that renders a modal chat assistant UI.

**What it does**
- Maintains chat state: `messages`, `input`, and `loading`.
- Sends user messages to a streaming HTTP endpoint (`/webhook/github-chat-hook`) via `fetch`.
- Reads the response stream, parses JSON lines, accumulates bot content, converts Markdown to sanitized HTML using `marked` and `DOMPurify`, and updates the latest bot message live.
- Handles Enter-to-send, auto-scrolls the message container, and shows a loading indicator while waiting.
- Renders user messages as plain text and bot messages as sanitized Markdown HTML.

**Important components/functions**
- `ChatSession({ onClose })`: main modal component.
- `parseMarkdown`: safely converts Markdown to sanitized HTML.
- `handleSend`: orchestrates request, streaming, accumulation, and message updates.
- `handleKeyPress`: sends on Enter without Shift.
- Auto-scroll `useEffect`: keeps latest messages visible.

**Relation to overall project**
- Based on its path, it appears to be part of the `ManualProject` feature, specifically under `textArea/sakpilot`, likely used as a chat assistant UI within that area. The provided file does not show where it is imported or how it is wired into the broader app.

### work-main/src/Pages/ManualProject/textArea/sakpilot/generateDoc.jsx

This file defines a React modal component, `GenerateDoc`, that generates and displays technical documentation for a project/story.

**What it does**
- Accepts `projectId`, `selectedStoryId`, `onClose`, and `authToken` props.
- On “Generate Documentation”, sends a POST request to a hardcoded webhook endpoint with `projectId` and `selectedStoryId`.
- Reads the response as a stream, parses newline-delimited JSON, and appends content from objects where `type === 'item'`.
- Converts accumulated Markdown to sanitized HTML using `marked` and `DOMPurify`, then renders it with `dangerouslySetInnerHTML`.
- Shows loading, empty, error, and generated-document states.
- Supports copying the rendered document as plain text.

**Important components/functions**
- `parseMarkdownToHtml`: parses Markdown, sanitizes allowed tags/attributes, wraps output in `.markdown-document`.
- `handleGenerate`: manages streaming fetch, buffering, JSON parsing, real-time HTML updates, and error handling.
- `handleCopy`: extracts plain text from rendered HTML and copies it to the clipboard.
- Inline `<style jsx>` block: custom styling for Markdown elements such as headings, code, tables, blockquotes, and links.
- Modal UI: header, scrollable content area, footer with generate/copy buttons, and status indicator.

**Relation to overall project**
- Located under `work-main/src/Pages/ManualProject/textArea/sakpilot/`, so it appears to be part of the Manual Project feature, specifically a documentation-generation tool within the “sakpilot” text area area.
- It is a self-contained UI component that depends on external AI/documentation webhook streaming and renders the result inside the app.

### work-main/src/Pages/ManualProject/textArea/sakpilot/impactAnalysis.jsx

This file defines a React component, `ImportAnalysis`, that renders a modal “Impact Analysis Report” UI.

What it does:
- Displays an empty state, loading state, and streamed analysis content.
- On “Run Impact Analysis,” sends a POST request with a static message (`DESCRIPTION`) to a webhook endpoint.
- Reads the response as a stream, parses newline-delimited JSON chunks, accumulates `content`, converts accumulated Markdown to sanitized HTML using `marked` and `DOMPurify`, and updates the UI in real time.
- Provides a “Copy Report” button that extracts plain text from the rendered HTML and copies it to the clipboard.
- Includes extensive CSS for Markdown-rendered analysis content.

Important components/functions:
- `ImportAnalysis` (default export): main modal component; accepts `onClose` and `authToken`.
- `parseMarkdownToHtml`: converts Markdown to sanitized HTML with allowed tags/attributes.
- `handleImportAnalysis`: performs streaming fetch and state updates.
- `handleCopy`: copies report text to clipboard.

Project relation:
- Located under `work-main/src/Pages/ManualProject/textArea/sakpilot/`, so it appears to be part of a Manual Project page feature, specifically an impact-analysis tool for a JWT-based authentication module scenario. The provided content does not show how it is imported or routed elsewhere.


## Folder: work-main/src/Pages/ManualProject/tour

### work-main/src/Pages/ManualProject/tour/tour.jsx

This file defines a React component named `Tour` that displays a modal, slide-based image tour.

**What it does**
- Maintains `currentSlide` state starting at `0`.
- Defines 10 image slides imported from `../../../assets/images/slides/`.
- Provides `handleNext`, `handleBack`, and `handleSkip` navigation/completion actions.
- Calls `onComplete` when the user reaches the end and clicks “Get Started” or clicks “Skip Tour”.
- Renders the current slide image and optional description, plus navigation buttons.

**Important components/functions**
- `Tour` (default export): main modal component.
- `currentSlide` state: tracks the active slide.
- `slides`: array of slide objects with `type: 'image'` and image content.
- `handleNext`, `handleBack`, `handleSkip`: control slide movement and tour completion.
- `renderContent`: renders the current image slide.

**Relation to overall project**
- Located under `ManualProject/tour`, so it likely serves as an onboarding/introductory tour for the Manual Project area.
- It expects a parent component to pass an `onComplete` callback to handle tour completion.


## Folder: work-main/src/Pages/ManualProject/userStories

### work-main/src/Pages/ManualProject/userStories/userStories.jsx

This file defines a React component, `UserStories`, that renders a searchable, scrollable list of user stories for a project.

**What it does**
- Receives `userStories`, `setSelectedStory`, `projectId`, `currentProject`, and `onRefetchAvailable` as props.
- Uses `useUserStoriesData(projectId)` to get `loading` and `refetch`.
- Exposes `refetch` to the parent through `onRefetchAvailable`.
- Periodically calls `refetch()` every 1,200,000 ms.
- Filters stories by a display key based on the search term.
- Displays each story with a status icon (`completed`, `in-progress`, `hold`, or a default error icon).
- Tracks the selected story ID and highlights the selected item.
- On click, builds a payload from the selected story and calls `setSelectedStory`.

**Important parts**
- `getDisplayKey`: returns `story.reference_key` when `currentProject.linked` and the key exists; otherwise returns `USER STORY - ${story._id}`.
- `handleStoryClick`: selects a story and passes its details to the parent.
- `getStatusIcon`: maps story status to an icon.
- Search input and filtered list rendering.
- `containerHeight` state is updated on resize, though it is not visibly used in the returned JSX.

**Relation to overall project**
- It appears to be a UI component within `ManualProject`, likely used as a story list/selector for a project.
- It depends on project data passed from a parent and on the `useUserStoriesData` hook for loading/refetching.
- It communicates user selection upward via `setSelectedStory`, allowing another part of the app to show or edit the selected story.


## Folder: work-main/src/Pages/ManualProject/widgets

### work-main/src/Pages/ManualProject/widgets/RequirementTable.jsx

This file defines a React component named `Table` (default export) for the ManualProject widgets area. It manages local state for dashboard data, loading, error, and accordion open/closed state. It uses the `useRequirementGraph` hook to call `requirementTable(projectId, selectedStoryId)`, fetches data in a `useEffect` when `projectId` or `selectedStoryId` changes, and renders a toggle button plus an accordion panel containing a table of features, test case counts, and a coverage indicator. It relates to the overall project as a UI widget that displays requirement/test coverage information for a selected project and story.

### work-main/src/Pages/ManualProject/widgets/allCharts.jsx

This file defines a React component, `DynamicCharts`, that fetches project/story data via `useFetchData(selectedStoryId, projectId, selectedStatus)` and renders four analytics charts using `recharts`.

Important parts:
- `DynamicCharts`: main component; handles loading/error states and transforms fetched data into chart datasets.
- Data processing in `useEffect`: counts Functional vs Non-Functional requirements, total test cases, test cases per requirement, knowledge existence vs gaps, and priority distribution.
- Chart sections: “Specification Risk” pie, “Requirement Details” pie, “Test Cases by Priority” pie with total test cases in the center, and “Test Cases / Requirement” bar chart.

Relation to the project: It appears to be a widget under `ManualProject`, used to visualize manual project metrics for a selected story, project, and status.


## Folder: work-main/src/Pages/Settings

### work-main/src/Pages/Settings/index.jsx

This file defines a React `Settings` page component.

- **What it does:** It renders a settings screen with a title, user information, and a logout button. It shows a loading message while auth data is loading, displays the logged-in user’s `displayName` and optional `role` when available, shows “No user data available” otherwise, and calls `handleLogout` when the Logout button is clicked.
- **Important components/hooks:** `Settings` (default export), `useAuthContext` (provides `authInfo` and `loading`), and `useLogout` (provides `handleLogout`).
- **Relation to overall project:** It appears to be an authenticated settings page in a React app, using shared auth context and a common logout utility to display current user details and allow sign-out.


## Folder: work-main/src/Pages/TDM

### work-main/src/Pages/TDM/index.jsx

This file is the main React page for the TDM (Test Data Management) feature. It manages UI state such as sidebar visibility, selected repository/table, loaded tables, spreadsheet refresh keys, loading status, repository list, and profile dropdown state. It also persists selected repository/table/sidebar state in `localStorage`.

Important components used:
- `Repository`: sidebar repository/table browser.
- `Toolbar`: top controls for table selection/deletion, refresh, repository selection, etc.
- `Spreadsheet`: displays data for the selected table.
- `ToastContainer`: shows toast notifications.

It relates to the overall project as the central page that coordinates repository/table selection and data viewing, passing state and handlers between the sidebar, toolbar, and spreadsheet.


## Folder: work-main/src/Pages/TDM/components

### work-main/src/Pages/TDM/components/ConfirmModal.jsx

This file defines a React component named `ConfirmModal` in `work-main/src/Pages/TDM/components/ConfirmModal.jsx`.

What it does:
- Renders a confirmation modal dialog only when `isOpen` is true.
- Displays a warning icon, a title, and a message.
- Provides two buttons: “Cancel” calls `onClose`, and “Delete” calls `onConfirm`.

Important parts:
- Props: `isOpen`, `onClose`, `onConfirm`, `title`, `message`.
- Default values for `title` and `message`.
- Uses `@fortawesome/react-fontawesome` with `faExclamationTriangle`.
- Styled with Tailwind CSS classes.

Relation to overall project:
- It is located under the TDM pages/components area, suggesting it is a reusable UI component for confirming actions, likely destructive ones such as deletion, within the TDM section.

### work-main/src/Pages/TDM/components/CreateTableModal.jsx

This file defines a React modal component, `CreateTableModal`, used to create a new table in the TDM area of the app.

What it does:
- Collects a table name and one or more column names from the user.
- Validates that a table name and at least one non-empty column are provided.
- Builds a payload with `repo_id`, `table_name`, and comma-joined `columns`.
- Calls `createTable` from the `useTDM` hook, shows success/error toasts, then invokes `onTableCreate` and closes the modal.
- Resets form state on close and auto-scrolls the column list when columns change.

Important components/elements:
- `CreateTableModal` component with props `isOpen`, `onClose`, `repoId`, `onTableCreate`.
- State: `tableName`, `columns`, `loading`.
- Handlers: `handleAddColumn`, `handleColumnChange`, `handleRemoveColumn`, `handleSubmit`, `handleClose`.
- UI: modal overlay, table name input, scrollable column inputs, add/remove column controls, cancel/create buttons.

Relation to overall project:
- Located under `src/Pages/TDM/components`, so it is part of the TDM feature UI.
- Integrates with the TDM data layer through `useTDM().createTable` and with app-wide notifications through `showToast`.
- Likely used by a parent TDM page/component to trigger table creation for a given `repoId`.

### work-main/src/Pages/TDM/components/GenerateDataModal.jsx

This file defines a React modal component, `GenerateDataModal`, for generating synthetic data in the TDM area.

**What it does**
- Renders a modal when `isOpen` is true.
- Lets the user enter a table name and choose how many rows to generate.
- Supports two input modes for source/sample data:
  - **Table mode**: editable columns and rows, with add/remove column and row actions.
  - **JSON mode**: raw JSON textarea.
- Validates the source data before submission:
  - JSON must parse to a non-empty array.
  - Table mode requires at least one column and one row.
- On submit, calls `generateSyntheticData` from `useData()` with:
  - `real_data`
  - `num_rows`
  - `repo_id`
  - `table_name`
- Shows success/error toasts, closes the modal, and calls `onSuccess?.(trimmedTableName)`.

**Important parts**
- `GenerateDataModal` component with props: `isOpen`, `onClose`, `repoId`, `onSuccess`.
- State: `mode`, `tableName`, `numRows`, `rawJson`, `columns`, `rows`.
- `parsedRealData` memoized validation/preview of source data.
- Handlers: `addColumn`, `removeColumn`, `addRow`, `removeRow`, `updateCell`, `resetAndClose`, `handleGenerate`.
- UI sections: table name input, mode toggle, table/JSON editors, row count input, footer actions.

**Relation to overall project**
- It is located under `Pages/TDM/components`, so it is part of the TDM feature’s UI.
- It depends on `useData` for the synthetic data generation request and `showToast` for user feedback.
- It is designed to be controlled by a parent component through `isOpen`, `onClose`, `repoId`, and `onSuccess`.

### work-main/src/Pages/TDM/components/Repository.jsx

This file defines a React component named `Repository` for managing repositories in the TDM area of the app.

What it does:
- Fetches repositories on mount using `getRepositories` from the `useTDM` hook.
- Displays a loading state while initially fetching.
- Shows a repository list with name, table count, selection state, and delete action on hover.
- Allows creating a new repository through an inline input, with validation for empty/duplicate names.
- Allows deleting a repository through a confirmation modal.
- Supports manual refresh and notifies the parent via `onRefresh` and `onRepositoriesLoaded`.
- Calls `onRepoSelect` when a repository is clicked or when the selected repository changes after data loads.

Important parts:
- `Repository` default export component.
- `useTDM` hook usage for `getRepositories`, `createRepository`, and `deleteRepository`.
- `ConfirmModal` for delete confirmation.
- Local state for repositories, input visibility, errors, hover, modal, loading, and refresh status.
- Effects for initial fetch, selected-repository synchronization, and outside-click handling.

Relation to overall project:
- It appears to be a sidebar/list component within the TDM feature, based on its path and props.
- It delegates data operations to `useTDM` and communicates selection/loading/refresh events to its parent through callback props.

### work-main/src/Pages/TDM/components/Toolbar.jsx

This file defines a React `Toolbar` component for the TDM page. It displays repository/table context, lets users create and delete tables, switch/select table tabs, scroll through tabs, and search tables across repositories.

Important parts:
- **Props**: `toggleSidebar`, `repoData`, `selectedRepoId`, `onTableSelect`, `onTableDelete`, `selectedTableId`, `setSelectedTablename`, `repositories`, `onRepoSelect`.
- **State**: tables, modal/delete state, scroll visibility, search term/results/dropdown, highlighted table, pending table selection.
- **Effects**: sync `tables` with `repoData`; complete pending selection after repo switch; close search dropdown on outside click; clear highlight after 3 seconds; update scroll buttons.
- **Handlers**: create table refresh, delete table, scroll, search, select search result, keyboard handling.
- **UI**: top bar with repo/table info and search; table tabs with highlight/delete; empty state; create table modal; delete confirmation modal.

It likely relates to the overall TDM feature as the navigation/action bar for repositories and their tables, coordinating table selection and repository switching with parent components.


## Folder: work-main/src/Pages/TDM/components

### work-main/src/Pages/TDM/components/UploadData.jsx

This file defines a React component named `UploadData` for uploading Excel/CSV files to a backend endpoint.

**What it does**
- Accepts `tableId` and an optional `onUploadSuccess` callback.
- Lets the user select a file with extensions `.xlsx`, `.xls`, or `.csv`.
- Validates the selected file type and shows an error toast if invalid.
- Uploads the selected file and `table_id` as `FormData` via `POST` to `${API_BASE}/upload_excel` (`/sakverse/tdm/upload_excel`), using included credentials.
- Shows success/error toast messages, clears the selected file on success, resets the file input, and calls `onUploadSuccess`.
- Displays an upload button labeled “Excel” and, when a file is selected, a small panel showing the file name with clear and upload actions.

**Important parts**
- `handleFileChange`: validates file extension.
- `handleUpload`: performs the upload request and handles response/errors.
- `clearFile`: resets selected file and input.
- UI: hidden file input, conditional file preview/action panel.

**Relation to overall project**
- It appears to be a TDM (Test Data Management?) page component used to import tabular data into a selected table through the backend API. It depends on the shared toast utility and FontAwesome icons. The exact backend behavior beyond the endpoint path is not shown in this file.


## Folder: work-main/src/Pages/TDM/components/Spreadsheet

### work-main/src/Pages/TDM/components/Spreadsheet/Spreadsheet.jsx

This file defines the `Spreadsheet` React component, which renders and manages an interactive spreadsheet view for a selected table.

What it does:
- Receives `selectedTableId`, `selectedTableName`, `onDataChange`, and `repoName`.
- Uses `useSpreadsheetData` to load and manage table data, rows, headers, editing state, deletion confirmation, loading state, and row/column operations.
- Uses `useTDM` for `downloadTable`.
- Fetches table data on mount/update via `fetchTableData(true)`.
- Supports Escape-key cancellation of row editing.
- Supports downloading the selected table as an `.xlsx` file through `handleDownload`.
- Supports adding a new column through `handleAddColumn` and a modal.
- Renders loading, header, toolbar, table body, and add-column modal states.

Important components/hooks used:
- `useSpreadsheetData`
- `useTDM`
- `TableHeader`
- `TableToolbar`
- `TableBody`
- `AddColumnModal`
- `TableLoading`
- `showToast`

Relation to overall project:
- It appears to be part of the TDM (Test Data Management) pages, specifically the spreadsheet/table editing experience.
- It connects selected table metadata and repository context to data operations and UI components for viewing, editing, adding, deleting, downloading, and refreshing table data.


## Folder: work-main/src/Pages/TDM/components/Spreadsheet/components

### work-main/src/Pages/TDM/components/Spreadsheet/components/AddColumnModal.jsx

This file defines a React modal component, `AddColumnModal`, used to add a new column to a spreadsheet/table.

**What it does**
- Renders only when `isOpen` is true.
- Lets the user enter a column name through a controlled input.
- Prevents duplicate column names by comparing the trimmed, case-insensitive input against `headers`.
- Calls `onAdd` when the user clicks “Add Column” or presses Enter, and `onClose` when canceling or pressing Escape.
- Shows a loading state while `isAdding` is true.
- Includes a hidden, disabled “Column Type” selector fixed to `"string"`.

**Important parts**
- `isDuplicate`: checks whether the entered name already exists in `headers`.
- Controlled `newColumn` state via `newColumn` and `setNewColumn`.
- Validation/disabled logic on the Add button: disabled if adding, empty name, or duplicate.
- Keyboard handling: Enter submits, Escape closes.

**Relation to overall project**
Based on its path and props, it is a UI component within the TDM Spreadsheet feature, likely rendered by a parent spreadsheet component to manage adding columns to a table. The provided file alone does not show where it is imported or how `onAdd` persists data.

### work-main/src/Pages/TDM/components/Spreadsheet/components/TableBody.jsx

This file defines a React presentational component, `TableBody`, that renders the `<tbody>` for a spreadsheet-style table.

What it does:
- Renders existing rows from `data`, with per-row edit and delete confirmation states.
- In edit mode, shows Save/Cancel buttons and text inputs for each header; supports Enter to save and Escape to cancel.
- In delete confirmation mode, shows Yes/No buttons.
- Otherwise, shows Edit and Delete buttons.
- Displays a row number and each cell value, with a hover copy button that copies an address string like `{tableName.rowIdx.header}`.
- Renders `newRows` as blue “NEW” rows with inputs and a remove button.
- Shows an empty-state row when there are no existing or new rows.

Important parts:
- `data.map(...)` existing row rendering and conditional row styling.
- `headers.map(...)` cell rendering, including editing inputs and copy-address button.
- `newRows.map(...)` new row inputs.
- Empty state block.

Relation to overall project:
- It is part of the TDM spreadsheet UI (`work-main/src/Pages/TDM/components/Spreadsheet/components/`), likely used by a parent table/spreadsheet component that manages row data, editing, deletion, new rows, loading state, and callbacks. It focuses only on table body presentation and user interactions delegated through props.

### work-main/src/Pages/TDM/components/Spreadsheet/components/TableHeader.jsx

This file defines a presentational React component, `TableHeader`, used as the header area for a spreadsheet/table view.

What it does:
- Renders the table name, row count, and optional status indicators.
- Shows `+ {newRowsCount} unsaved` when there are unsaved new rows.
- Shows `Editing row {editingRowIndex + 1}` when a row is being edited.
- Renders a Refresh button that calls `onRefresh` and shows a spinning sync icon while `isRefreshing` is true.

Important components/elements:
- `TableHeader` (default export)
- `FontAwesomeIcon` from `@fortawesome/react-fontawesome`
- Icons `faTable` and `faSync`

Relation to the overall project:
- Based on its path, it is part of the TDM Spreadsheet feature and likely provides the header UI for a table component, displaying table metadata and refresh controls. The provided content does not show where it is imported or used.

### work-main/src/Pages/TDM/components/Spreadsheet/components/TableLoading.jsx

This file defines a React functional component named `TableLoading`.

- **What it does:** It renders a centered loading UI with a spinning circle and two loading messages: “Loading table data...” and “Please wait.”
- **Important components:** The default-exported `TableLoading` component; it uses Tailwind CSS utility classes for layout, animation, sizing, and styling.
- **Relation to overall project:** Based on its path (`work-main/src/Pages/TDM/components/Spreadsheet/components/TableLoading.jsx`), it is likely used as a loading state within the TDM Spreadsheet feature, though the provided content does not show where it is imported or used.

### work-main/src/Pages/TDM/components/Spreadsheet/components/TableToolbar.jsx

This file defines a React functional component named `TableToolbar`, exported as the default export. It renders a horizontal toolbar for a spreadsheet/table UI with action buttons and status text.

Important elements:
- **Add Row** button, calls `onAddRow`.
- **Save new rows** button, shown only when `newRowsCount > 0`, calls `onSaveNewRows`, and displays saving state via `isSaving`.
- **Add Column** button, calls `onAddColumn`.
- **Download Excel** button, calls `onDownload`, and displays downloading state via `isDownloading`.
- An informational hint telling users to click the edit icon to edit a row.
- Props include `selectedTableId`, `onUploadSuccess`, and `isRefreshing`, but they are not used in the rendered JSX.

In the overall project, this appears to be part of the TDM spreadsheet feature, providing toolbar controls for adding rows/columns, saving newly added rows, and downloading the table as Excel.


## Folder: work-main/src/Pages/TDM/components/Spreadsheet/hooks

### work-main/src/Pages/TDM/components/Spreadsheet/hooks/useSpreadsheetData.js

This file defines a React custom hook, `useSpreadsheetData`, that manages spreadsheet/table data state and CRUD-style operations for a selected table.

**What it does**
- Fetches table data and headers using `getTableData` from `useTDM`.
- Stores existing rows, headers, new unsaved rows, editing state, table name, delete confirmation, and loading flags.
- Supports saving edited rows, saving new rows, deleting rows, adding rows, starting/canceling edits, updating new-row values, and adding columns.
- Shows success/error toasts and calls `onDataChange` after successful mutations.

**Important parts**
- State: `data`, `headers`, `newRows`, `editingRowIndex`, `editingRowData`, `tableName`, `deleteConfirm`, `isLoading`.
- Key functions: `fetchTableData`, `saveRow`, `saveNewRows`, `deleteRow`, `addRow`, `startEdit`, `cancelEdit`, `handleNewRowChange`, `addColumn`.
- Dependencies: `useTDM` for API operations and `showToast` for notifications.

**Relation to overall project**
- It appears to be a data-management hook for the TDM Spreadsheet feature, likely consumed by a Spreadsheet page/component to handle table records and column changes.


## Folder: work-main/src/Pages/TDM/components/Spreadsheet/utils

### work-main/src/Pages/TDM/components/Spreadsheet/utils/spreadsheetUtils.js

This file provides small utility helpers for a spreadsheet-like table in the TDM area.

Important components:
- `createEmptyRow(headers)`: builds a new row object with each header set to an empty string.
- `validateNewRow(row, headers)`: checks whether any header value is missing or blank after trimming.
- `getCellAddress(tableName, rowIndex, header)`: creates a cell reference string like `{tableName.1.header}`.
- `formatCellValue(value)`: converts a value to a string, or returns `—` for null/empty values.

It likely supports the TDM spreadsheet component by handling row initialization, validation, cell addressing, and display formatting.


## Folder: work-main/src/Pages/TDM/components/Toolbar

### work-main/src/Pages/TDM/components/Toolbar/Toolbar.jsx

This file defines the `Toolbar` React component for the TDM page. It renders the top toolbar and table-tab area for a selected repository, and coordinates table-related actions.

**What it does**
- Maintains local `tables` state, synced from `repoData`.
- Manages modal state for creating tables, generating data, and deleting tables.
- Uses `useToolbarSearch` for cross-repository/table search behavior, including pending selection after a repo switch.
- Handles table creation, deletion, and data generation refresh flows by calling `getRepositories`/`deleteTable` from `useTDM`.
- Auto-selects a newly created/generated table and notifies parent via `onTableSelect`, `setSelectedTablename`, and `onRefresh`.
- Shows empty state when no tables exist for a selected repo.

**Important components/elements used**
- `RepoInfo`
- `SearchBar`
- `CreateTableButton`
- `GenerateDataButton`
- `TableTabs`
- `CreateTableModal`
- `GenerateDataModal`
- `DeleteTableModal`

**Relation to overall project**
- It is part of the TDM feature UI (`work-main/src/Pages/TDM/...`).
- It connects repository/table selection and table management actions to parent-provided callbacks and TDM data hooks.
- It supports navigation/search across repositories and tables, plus create/generate/delete workflows that update the displayed table list.


## Folder: work-main/src/Pages/TDM/components/Toolbar/hooks

### work-main/src/Pages/TDM/components/Toolbar/hooks/useToolbarSearch.js

This file defines a custom React hook, `useToolbarSearch`, that powers search functionality in the TDM Toolbar.

**What it does**
- Maintains search UI state: search term, loading flag, results, dropdown visibility, highlighted table ID, and pending table selection.
- Searches across all provided repositories and their tables by table name, sorting exact matches first.
- Handles selecting a search result:
  - If the table is in the current repository, it calls `onTableSelect`, updates the selected table name, scrolls to the table tab, and highlights it.
  - If it is in another repository, it stores a pending selection and calls `onRepoSelect` to switch repositories.
- Closes the dropdown on outside clicks, clears highlight after 3 seconds, supports Enter/Escape keyboard handling, and clears search input.

**Important parts**
- `performSearch`: filters and sorts table matches.
- `handleSearchSelect`: decides same-repo vs cross-repo selection behavior.
- `scrollToTableTab`: scrolls the table tab into view with retry/backoff and applies temporary highlight.
- `pendingTableSelection`: supports deferred selection after repository switching.
- Refs/effects: `searchInputRef`, `searchDropdownRef`, `highlightTimeoutRef`, outside-click listener, highlight timeout cleanup.

**Relation to overall project**
- It is located under `Pages/TDM/components/Toolbar/hooks`, so it supports the TDM page’s toolbar search experience, likely consumed by a Toolbar component to let users find and navigate to tables across repositories.


## Folder: work-main/src/Pages/TDM/components/Toolbar/toolbar

### work-main/src/Pages/TDM/components/Toolbar/toolbar/CreateTableButton.jsx

This file defines a React component named `CreateTableButton`.

- **What it does:** It renders either an enabled “Create Table” button (with a plus icon) when `selectedRepoId` is truthy, or a disabled “Select Repository First” button when no repository is selected.
- **Important components/props:** The component accepts `selectedRepoId` and `onClick` props. It uses `FontAwesomeIcon` with `faPlus` for the icon.
- **Project relation:** Based on its path, it is part of the TDM page toolbar UI, likely used to initiate table creation after a repository has been selected.

### work-main/src/Pages/TDM/components/Toolbar/toolbar/DeleteTableModal.jsx

This file defines a React component named `DeleteTableModal`.

- **What it does:** It renders a confirmation modal when `isOpen` is true; otherwise it returns `null`. The modal asks whether the user wants to delete a table and states the action cannot be undone. It provides a Cancel button that calls `onClose` and a Delete button that calls `onConfirm`.
- **Important components/elements:** The `DeleteTableModal` component and its props (`isOpen`, `onClose`, `onConfirm`), plus the modal overlay, heading, warning text, and two action buttons.
- **Project relation:** Based on its path under `Pages/TDM/components/Toolbar/toolbar/`, it is likely used in the TDM toolbar area to confirm table deletion before performing the delete action.

### work-main/src/Pages/TDM/components/Toolbar/toolbar/GenerateDataButton.jsx

This file defines a React component, `GenerateDataButton`, used in the TDM toolbar. It accepts `selectedRepoId` and `onClick` props.

- If `selectedRepoId` is truthy, it renders an enabled green “Generate Data” button with a database icon that calls `onClick`.
- Otherwise, it renders a disabled gray button labeled “Select Repository First.”

Based only on the provided content, it appears to gate the “Generate Data” action behind repository selection within the TDM toolbar.

### work-main/src/Pages/TDM/components/Toolbar/toolbar/RepoInfo.jsx

This file defines a React component named `RepoInfo` used in the TDM toolbar area.

What it does:
- Renders a button that calls `toggleSidebar` to open/close the sidebar.
- If `selectedRepoId` exists, displays the selected repository ID and, if `selectedTable` exists, the selected table name.
- If no repository is selected, displays “No repository selected”.

Important components/elements:
- `RepoInfo` component
- Props: `toggleSidebar`, `selectedRepoId`, `selectedTable`
- FontAwesome icons: `faBars`, `faFolderOpen`, `faTable`

Relation to overall project:
- It appears to be part of the TDM page toolbar, providing repository/table context and sidebar toggle functionality. The provided content does not show how it is imported or used elsewhere.

### work-main/src/Pages/TDM/components/Toolbar/toolbar/SearchBar.jsx

This file defines a React presentational component, `SearchBar`, used in the TDM toolbar. It renders a search input for test case IDs, shows a spinner while searching, a clear button when text is present, and a dropdown of search results or a “no results” message. Each result displays the table name, match type, repository name, and whether selecting it would switch repositories.

Its important parts are the controlled input, result dropdown, result selection buttons, and empty-state UI. Based on its path and props, it likely supports searching across repositories/test cases within the TDM feature and delegates search behavior to parent-provided handlers.


## Folder: work-main/src/Pages/TDM/components/Toolbar/toolbar

### work-main/src/Pages/TDM/components/Toolbar/toolbar/TableTabs.jsx

This file defines a React component, `TableTabs`, used to render a horizontally scrollable row of table tabs.

What it does:
- Displays one tab per item in `tables`, showing `table.table_name`.
- Tracks which tab is selected (`selectedTableId`) and which is highlighted (`highlightedTableId`).
- Calls `onTableSelect`, `setSelectedTablename`, and clears highlight when a tab is clicked.
- Supports deleting a table via `onDeleteClick` through a hover-revealed close button.
- Shows left/right scroll buttons when the tab list overflows.
- Scrolls to the highlighted tab when `highlightedTableId` changes.
- Returns `null` when there are no tables.

Important parts:
- `scrollRef` and `checkScrollButtons` manage overflow/scroll button visibility.
- The `highlightedTableId` effect scrolls the highlighted tab into view.
- The tab button uses `data-table-id` to locate the highlighted tab.
- Styling distinguishes selected, highlighted, and default tabs.

Relation to the overall project:
- Based on its path, `work-main/src/Pages/TDM/components/Toolbar/toolbar/TableTabs.jsx`, it is part of the TDM page toolbar UI and likely helps users switch between, identify, and delete tables in that workflow.


## Folder: work-main/src/Routes

### work-main/src/Routes/index.jsx

This file defines the application’s central client-side routing configuration in a React Router setup.

**What it does**
- Exports `AppRoutes`, which renders a `<Routes>` tree.
- Reads authentication state from `useAuthContext()` (`isAuthenticated`, `authInfo`, `loading`).
- Shows a loading message while authentication is loading.
- Redirects authenticated users away from `/login` to `/admin` if their role is `1`, otherwise to `/`.
- For unauthenticated users, redirects all routes to `/login`.
- Provides authenticated routes, some wrapped in `MainLayout`, some not.
- Protects project-related routes with `ProtectedProjectRoute`.
- Restricts `/admin/*` to admins; non-admins are redirected to `/login`.
- Includes a catch-all `*` route rendering `ErrorPage` with a 404 error.

**Important components/routes**
- `MainLayout` wraps Dashboard, Documentation, Settings, TestCasePage, and ManualProject routes.
- `ProtectedProjectRoute` guards:
  - `/ManualProject/:projectId`
  - `/ManualProject/testsuite/:projectId`
  - `/automation`
  - `/testDataManagement`
- `ManualProject` is rendered with `showSuite={true}` for the testsuite path.
- `Admin` is rendered only for admin users.
- `ErrorPage` handles unmatched routes.

**Relation to overall project**
- It acts as the app’s route map, connecting pages such as Dashboard, Settings, Login, Automation, ManualProject, TDM, TestCasePage, Admin, and Documentation.
- It enforces authentication, project access, and admin-only access at the routing level.


## Folder: work-main/src/items

### work-main/src/items/doughnut.jsx

This file defines a React component named `Graph` that renders a doughnut chart using `react-chartjs-2` and `chart.js`.

Important parts:
- `Graph`: the default-exported React component.
- `Doughnut`: the chart component rendered inside a fixed-size container.
- Hardcoded chart data: labels `['Pass %', 'Fail %']`, values `[60, 40]`, with orange/blue colors.
- Chart options: `cutout: 90`, bottom legend, and 10×10 legend boxes.

Relation to the overall project: based only on the provided content, it is a UI chart component located at `work-main/src/items/doughnut.jsx`; no imports or usage elsewhere are shown, so its exact integration point cannot be determined from this file alone.

### work-main/src/items/linechart.jsx

This file defines a React component named `LineChart` that renders a responsive line chart using `react-chartjs-2` and Chart.js.

Important parts:
- `LineChart`: the default-exported component, which renders a rotated date heading (`28/01/2024`) and the `Line` chart.
- `data`: chart configuration with two datasets:
  - “Dataset 1”: blue line with points at `(0,0)`, `(10,15)`, and `(20,30)`.
  - “Dataset 2”: orange line where `y = x` across labels `0` to `100`.
- `options`: chart settings such as responsive mode, visible legend, hidden title, hidden y-axis ticks, and white grid lines.
- `generateRandomData`: defined but not used in the shown code.

Relation to the overall project: based only on the provided path and content, it appears to be a reusable chart UI component located under `src/items/`, likely used somewhere in the application’s interface to display the configured line chart. The provided file does not show where or how it is imported.


## Folder: work-main/src/items/Base64Conversion

### work-main/src/items/Base64Conversion/Base64Image.jsx

This file defines a React component named `Base64Image` that accepts `base64Data` and `altText` props. If `base64Data` is missing, it renders “No image available”; otherwise it builds a `data:image/png;base64,...` URL and renders an `<img>` with that source, the provided alt text, and full-width responsive styling.

Its important parts are the prop handling, the fallback message, the base64 data URL construction, and the image element styling.

Based only on its path and content, it appears to be a reusable UI component for displaying a base64-encoded PNG image, likely within a “Base64Conversion” feature area of the project.


## Folder: work-main/src/items/Pagination

### work-main/src/items/Pagination/Pagination.jsx

This file defines a React component named `Pagination`.

- **What it does:** It calculates the total number of pages from `totalItems` and `itemsPerPage`, then renders a centered list of page-number buttons. Clicking a button calls `paginate(i + 1)`, and the current page is visually highlighted.
- **Important parts:** The `Pagination` component and its props: `totalItems`, `itemsPerPage`, `currentPage`, and `paginate`.
- **Project relation:** Based on its path under `src/items/Pagination/`, it appears to be a reusable pagination UI component for item listings in the project.


## Folder: work-main/src/items/PopUp

### work-main/src/items/PopUp/PopUp.jsx

This file defines a reusable React modal/popup component named `Popup`.

- **What it does:** It conditionally renders a centered overlay modal when `isOpen` is true. The modal shows a “Details” header, a close button (`X`) that calls `onClose`, scrollable content passed via `children`, and an optional screenshot rendered with `Base64Image` when the `screenshot` prop is provided.
- **Important components:** `Popup` (default export) and `Base64Image`, imported from `../Base64Conversion/Base64Image`.
- **Relation to overall project:** Based only on its path and props, it appears to be a shared UI component under `work-main/src/items/PopUp/`, likely used by other parts of the app to display detailed information and an optional base64-encoded screenshot in a modal. The provided content does not show where it is imported or used.


## Folder: work-main/src/items/SearchBar

### work-main/src/items/SearchBar/SearchBar.jsx

This file defines a React functional component named `SearchBar`.

- It renders a controlled text `<input>` with placeholder `"Search..."`.
- It accepts `value` and `onSearch` props.
- On input change, it calls `onSearch(e.target.value)`.
- It applies Tailwind-like classes: `mb-4 p-2 border rounded`.
- It is exported as the default export.

Based only on the provided content, it appears to be a reusable search input component, likely used somewhere in the project’s item-related UI, though its exact usage is not shown.


## Folder: work-main/src/items/SortableTableHeader

### work-main/src/items/SortableTableHeader/SortableTableHeader.jsx

This file defines a React component named `SortableTableHeader`.

What it does:
- Accepts `headers`, `onSort`, and `currentSort` props.
- Renders a table header (`<thead>`) with one row of `<th>` cells.
- For each header, displays `header.label`.
- Makes each header clickable; clicking calls `onSort` with the header key and toggled sort order (`asc`/`desc`).
- Shows a sort indicator (`▲` or `▼`) for the currently sorted column.

Important components:
- `SortableTableHeader` (default export)
- `handleSort` internal function for determining sort order

Project relation:
- Located under `work-main/src/items/SortableTableHeader/`, suggesting it is a reusable UI component for sortable table headers within the project.


## Folder: work-main/src/items/Table

### work-main/src/items/Table/Table.jsx

This file defines a React functional component named `ThirdTable`.

- **What it does:** It renders a modal overlay showing “Step Details” for a selected item. It displays `step_id`, `error_message`, and a screenshot if `thirdTableData.screenshot` exists; otherwise it shows “No screenshot available.” It includes a “Close” button that calls `onClose`.
- **Important components:** The `ThirdTable` component itself, its props `onClose` and `thirdTableData`, and the conditional screenshot rendering.
- **Relation to overall project:** Based on its path (`work-main/src/items/Table/Table.jsx`) and content, it appears to be a detail view/modal used within a Table-related feature to inspect step-level error information. The provided content does not show how it is imported or used elsewhere.


## Folder: work-main/src/items/ToastMessage

### work-main/src/items/ToastMessage/toastUtil.jsx

This file defines a small utility for showing toast notifications using `react-toastify`.

- **What it does:** It exports a default function, `showToast(message, type = 'success')`, that displays a toast notification with a message and a type of either `'success'` or `'error'`.
- **Important components:** The `showToast` function and its `toastOptions` object, which configure position, auto-close duration, progress bar visibility, click-to-close, hover pause, and draggability.
- **Project relation:** Based only on the file, it appears to be a reusable helper for triggering success/error toast messages elsewhere in the project, though the provided content does not show where it is imported or used.


## Folder: work-main/src/items/UploadFile

### work-main/src/items/UploadFile/UploadData.jsx

This file defines a React component named `UploadData` that provides a file upload form for spreadsheet files.

**What it does**
- Accepts `tableId` and `fetchTableData` as props.
- Tracks the selected file in local state.
- When a file is selected, shows an “Upload” button.
- On submit, sends the file and `table_id` as `multipart/form-data` to `${config.TDMIP}/upload_excel`.
- Shows success/error toast messages.
- On successful upload, clears the selected file and calls `fetchTableData()`.

**Important components/elements**
- `UploadData` component
- `file` state and `handleFileChange`
- `handleSubmit` async upload handler
- Hidden `<input type="file">` with accepted types `.xlsx`, `.xls`, `.csv`
- Conditional submit button shown only when a file is selected

**Relation to overall project**
- It appears to be a reusable UI piece for uploading Excel/CSV data associated with a specific table (`tableId`) and refreshing that table’s data after upload. The snippet references `config.TDMIP`, but its definition/import is not shown in this file.


## Folder: work-main/src/items/suiteHelper

### work-main/src/items/suiteHelper/htmlHelper.js

This file is a JavaScript helper that generates a self-contained HTML test execution report from structured execution data.

**What it does**
- `generateExecutionHTML(data)` builds a full HTML document string containing suite info, execution info, summary cards, per-execution accordion sections, step-level tables, error/log expanders, screenshot lightbox markup, CSS, and client-side JavaScript.
- `transformReportData(reportData)` converts a report object with `testcases` and nested `steps` into the shape expected by `generateExecutionHTML`, including extracting error-like logs.

**Important components**
- Grouping by `execution_id` + `data_row_id`.
- Per-execution status calculation (`SUCCESS`, `FAILED`, `IN PROGRESS`, `NOT FOUND`).
- Step table rendering with status badges, error/log preview/full toggle, and screenshot view buttons.
- Lightbox script for viewing screenshots.
- Formatting helpers for dates and duration.
- Responsive/print CSS.

**Relation to overall project**
- It appears to support a suite execution reporting feature, likely producing downloadable/viewable HTML reports from suite execution results.
- It is a presentation/report-generation utility rather than core test execution logic; it depends on callers providing execution/result data in the expected structure.


## Folder: work-main/src/layouts

### work-main/src/layouts/MainLayout.jsx

This file defines a `MainLayout` React component that wraps the main application UI.

- It manages local state for whether the sidebar is open (`isSidebarOpen`) and provides a toggle function.
- It renders `AppHeader`, passing the toggle handler and sidebar state.
- It renders `Sidebar`, passing sidebar state and a close handler.
- It renders a `<main>` area containing React Router’s `<Outlet />`, where nested route content appears.
- It wraps everything in `UserDataProvider`, suggesting user data context is available to the layout and its children.

Overall, it likely serves as the shared layout for authenticated/main app pages, combining header, sidebar, and routed page content.

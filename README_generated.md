# AI SDLC – Code Analysis  

## 1. Project Overview  
The project is a **backend API service** that provides an internal file‑system management system (create, read, update, delete folders/files) and supports multipart file uploads via Multer. It also integrates with JIRA for authentication/authorization and communicates with a front‑end application defined in the configuration. The goal is to centralise all runtime dependencies (environment variables) so that the same codebase can be deployed across different environments without hard‑coding values.

---

## 2. Main Components  

| Component | Description |
|-----------|-------------|
| **`apiConfig.js`** | Loads environment variables from `.env`, builds a single JavaScript object containing all runtime configuration (host/port, internal IPs, JIRA credentials, frontend URL, CORS policy). |
| **`UploadController.js`** | Exposes HTTP endpoints for CRUD operations on folders/files and handles file uploads using Multer. It also defines the root storage path (`BASE_PATH`) from an environment variable. |

---

## 3. Important Files & Their Responsibilities  

### `backend/config/apiConfig.js`

| Section | Purpose |
|---------|---------|
| **`HOST`, `PORT`** | Base network address of the backend server. |
| **`BASE_IP`, `JAVA_IP`** | IP addresses used for internal communication (e.g., Java client). |
| **`JIRA_Config`** | Username, password and URL for JIRA integration. |
| **`FRONTEND`** | Full URL of the front‑end application (`https://${HOST}:${FRONTEND_PORT}`). |
| **`CORS`** | CORS policy that allows cross‑origin requests from the specified origin, including allowed methods, headers and credential flag. |

*Responsibility*: Centralises all external dependencies (environment variables) required for the API to start and communicate with other services.

---

### `backend/controllers/UploadController.js`

| Component | Role |
|-----------|------|
| **`import fs, path, multer, dotenv`** | Core Node.js modules: file‑system access (`fs`), path handling (`path`), multipart upload support (`multer`), and environment loading (`dotenv`). |
| **`BASE_PATH = process.env.PATH`** | Root directory where uploaded files are stored; defined from an env variable. |
| **`formatDate`, `getDirectoryStructure`** | Helper functions: timestamp → readable string, recursive folder‑structure builder. |
| **`getFolderStructure` (GET)** | Returns the current tree of folders/files under `BASE_PATH`. |
| **`createFileOrFolder` (POST `/CreateFile/:folderName`)** | Creates a file or folder at `BASE_PATH/folderName/relativePath`, checks existence, writes content if it’s a file. |
| **`deleteFileOrFolder` (DELETE)** | Removes a single file or an entire directory recursively. |
| **Multer storage config** (`storage.destination`, `storage.filename`) | Saves uploaded files to the same folder hierarchy under `BASE_PATH`. |
| **`uploadFiles` (POST `/UploadFiles/:folderName`)** | Receives multipart request, validates at least one file was sent, returns a JSON list of the uploaded files. |

*Responsibility*: Implements CRUD operations for folders/files and handles file uploads while keeping storage location configurable via environment variables.

---

## 4. Technologies Identified in the Analysis  

| Technology | Status |
|------------|--------|
| **Node.js runtime** (JavaScript/ES6) | ✅ Identified – used throughout the codebase. |
| **dotenv** (environment variable loading) | ✅ Identified – imported via `import dotenv`. |
| **Multer** (multipart file upload handling) | ✅ Identified – imported and configured for storage. |
| **fs / path** (Node.js built‑in modules) | ✅ Identified – used for file system operations. |
| **Express** (web framework) | Not identified in the analysis. |
| **JIRA integration** (authentication/authorization) | Not a technology; only credentials are defined. |
| **CORS policy** (security configuration) | Not a technology per se, but part of `apiConfig.js`. |

*If any information is missing or not covered by the provided analysis, it is marked as “Not identified”.*
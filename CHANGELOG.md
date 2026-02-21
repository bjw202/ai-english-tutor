# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-21

### Added

#### Frontend (SPEC-FRONTEND-001)

- **Project Scaffolding**
  - Next.js 15 with App Router
  - TypeScript 5.9+ with strict mode
  - Tailwind CSS 4 configuration
  - shadcn/ui component library setup
  - Vitest test framework configuration
  - Playwright E2E test configuration

- **Type System**
  - `ReadingResult`, `GrammarResult`, `VocabularyResult` types
  - `AnalyzeResponse` type matching backend API contract
  - `Message`, `UserMessage`, `TutorMessage` chat types
  - API endpoint constants and level definitions

- **API Client**
  - `analyzeText()` - Text analysis with SSE streaming
  - `analyzeImage()` - Image upload with multipart/form-data
  - `sendChat()` - Chat with SSE streaming
  - `ApiError` class for typed error handling
  - `cn()` utility for conditional class names

- **Custom Hooks**
  - `useSession` - Session ID management with localStorage persistence
  - `useLevelConfig` - Comprehension level (1-5) management
  - `useTutorStream` - SSE stream parsing with agent-specific chunk handling

- **UI Components**
  - `ChatContainer` - Two-panel chat layout
  - `MessageList` - Auto-scrolling message list with memoization
  - `UserMessage` - Right-aligned user bubble
  - `TutorMessage` - Left-aligned tutor bubble with streaming indicator
  - `ChatInput` - Textarea with Enter-to-send
  - `ImageUpload` - Drag & drop with file picker, 10MB limit

- **Tutor Panels**
  - `TabbedOutput` - Tabs for Reading/Grammar/Vocabulary
  - `ReadingPanel` - Summary, key points, comprehension level
  - `GrammarPanel` - Issues, score, suggestions
  - `VocabularyPanel` - Words table with difficulty badges

- **Controls**
  - `Header` - App logo and title
  - `LevelSlider` - Level 1-5 slider with Korean labels

- **Route Handlers**
  - `/api/tutor/analyze` - POST proxy to backend (SSE)
  - `/api/tutor/analyze-image` - POST multipart proxy
  - `/api/tutor/chat` - POST chat proxy

- **Pages**
  - Root layout with metadata and Toaster
  - Main page composing all components

- **Testing**
  - 101 unit/integration tests passing
  - 91.98% line coverage, 86.5% branch coverage
  - MSW (Mock Service Worker) for API mocking

#### Backend (SPEC-BACKEND-001)

- FastAPI application with LangGraph orchestration
- Multi-agent system (Supervisor, Reading, Grammar, Vocabulary, Image Processor)
- SSE streaming responses
- Session management
- Health check endpoint

### Technical Details

- **Frontend Stack**: Next.js 15, React 19, TypeScript 5.9+, Tailwind CSS 4, shadcn/ui
- **Backend Stack**: FastAPI, Python 3.13, LangGraph 0.3+, Pydantic 2.10+
- **LLM Models**: GPT-4o-mini, GPT-4o, Claude Sonnet, Claude Haiku
- **Testing**: Vitest (frontend), pytest (backend)
- **Package Managers**: pnpm 10.x (frontend), uv 0.6+ (backend)

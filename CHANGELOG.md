# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.1] - 2026-02-23

### Added
- **LLM Model Optimization (SPEC-MODEL-001)**
  - Unified all agents to gpt-4o-mini model (Supervisor, Reading, Grammar, Vocabulary)
  - Removed Anthropic/Claude dependency entirely
  - Added GLM (Zhipu AI) support via ChatOpenAI base_url (for future OCR feature)
  - New environment variable: GLM_API_KEY (optional)
  - New config setting: OCR_MODEL (default: glm-4v-flash)
  - 95% cost reduction: ~$152/month → ~$7/month (1,000 requests/month)

### Changed
- **Model Configuration**: Removed ANTHROPIC_API_KEY requirement, models now settings-based
- **Backend Tests**: 165 tests → 207 tests (+42 new tests)
- **Backend Coverage**: 96% → 83% (refactored for multi-model support)

### Fixed
- **Model Settings Bug**: Agents now read model names from config (was hardcoded)
- **Type Annotations**: Updated to Python 3.13 modern syntax (`Optional[str]` → `str | None`)

## [1.1.0] - 2026-02-22

### Added
- **Markdown Output Normalizer** (`backend/src/tutor/utils/markdown_normalizer.py`)
  - Post-processing utility applied after LLM calls to normalize heading formats
  - Converts bold text (`**문장 1**`), wrong heading levels, plain text section names to correct Markdown headings
  - Three normalizers: `normalize_reading_output()`, `normalize_grammar_output()`, `normalize_vocabulary_output()`
  - Safety guarantee: returns original content unchanged on any exception

### Fixed
- **Frontend Markdown formatting** - Installed `@tailwindcss/typography 0.5.19` plugin
  - `tailwind.config.js` updated with `plugins: [require("@tailwindcss/typography")]`
  - `prose` class in reading/grammar/vocabulary panels now renders h3/h4 headings with proper styles
  - Resolves issue where ReactMarkdown-rendered headings appeared as plain text due to Tailwind CSS preflight reset

## [1.1.0] - 2026-02-22

### Added

#### Backend (SPEC-UPDATE-001)

- **Supervisor Pre-Analyzer**
  - Claude Haiku LLM-powered pre-analysis node
  - Sentence segmentation with automatic detection
  - Difficulty scoring (1-5 level evaluation)
  - Learning focus area identification
  - SupervisorAnalysis schema with SentenceEntry records

- **Korean Tutoring Prompts Redesign**
  - Reading: Slash Reading Training (슬래시 직독직해) with 4-step structure
  - Grammar: Grammar Structure Understanding with Korean comparative analysis
  - Vocabulary: Etymology Network Learning with 6-step etymology-based explanation
  - All prompts rewritten in Korean following pedagogical best practices

- **Schema Redesign**
  - Content-based Markdown output instead of structured JSON
  - VocabularyWordEntry with word and content fields
  - ReadingResult and GrammarResult with content: str field
  - SentenceEntry and SupervisorAnalysis for pre-analysis

- **Model Upgrade**
  - Vocabulary agent upgraded from Claude Haiku to Claude Sonnet for improved Korean etymology explanations
  - Supervisor agent upgraded from GPT-4o-mini to Claude Haiku for efficient pre-analysis

- **Korean Level Instructions**
  - Level 1-5 instructions rewritten in Korean educational framework
  - Each level tailored for comprehension and learning progression

#### Frontend (SPEC-UPDATE-001)

- **Korean Rendering**
  - ReactMarkdown integration for all content panels
  - Korean tab labels: 독해 (Reading), 문법 (Grammar), 어휘 (Vocabulary)
  - Full markdown support for formatted Korean educational content

- **Component Updates**
  - Reading panel renders Markdown-formatted slash reading analysis
  - Grammar panel renders Markdown-formatted structure-based explanations
  - Vocabulary panel renders Markdown-formatted etymology network content

### Changed

- Backend test count: 165 tests passing (from 34)
- Frontend test count: 97 tests passing (with mobile responsive UI)
- API response format: Content-based instead of structured fields
- Supervisor role: From pure router to LLM-powered pre-analyzer
- All tutoring content: Shifted to Korean language and pedagogical approach

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

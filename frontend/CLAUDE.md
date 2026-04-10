# Frontend context

## Read first (always)
- /docs/api_contracts.md — all endpoints, exact request/response shapes
- /CLAUDE.md (root) — naming conventions, git workflow, phases

## Tech stack
- React 18 + TypeScript 5 + Vite
- TanStack Query v5 (server state)
- Zustand (global client state)
- Axios (HTTP client)
- React Router v6
- Vitest + Testing Library (tests)
- Tailwind CSS

---

## Folder structure

src/
  pages/          one file per route (LoginPage.tsx, DashboardPage.tsx)
  components/
    ui/            generic: Button, Input, Card, Spinner (no business logic)
    nutrition/     NutritionLogForm, DaySummaryCard, MealList
    chat/          ChatWindow, ChatMessage, StreamingIndicator
    user/          ProfileForm, GoalSetupCard, RestrictionsList
  hooks/           useAuth.ts, useNutritionLog.ts, useAiChat.ts
  services/        api.ts (axios instance), auth.service.ts,
                   nutrition.service.ts, ai.service.ts
  stores/          auth.store.ts, ui.store.ts
  types/           api.types.ts (mirrors api_contracts.md schemas)
  utils/           calc.ts (BMI, TDEE), format.ts (dates, numbers)
  constants/       api.constants.ts, nutrition.constants.ts

---

## Naming conventions

Files:
  pages/       PascalCase + Page suffix   → DashboardPage.tsx
  components/  PascalCase                 → NutritionLogForm.tsx
  hooks/       camelCase + use prefix     → useNutritionLog.ts
  services/    camelCase + .service       → nutrition.service.ts
  stores/      camelCase + .store         → auth.store.ts
  types/       camelCase + .types         → api.types.ts
  utils/       camelCase                  → format.ts

Inside files:
  React components:  PascalCase           → NutritionLogForm
  Custom hooks:      camelCase, use*      → useNutritionLog()
  Regular functions: camelCase            → calculateDailyDeficit()
  Constants:         UPPER_SNAKE          → MAX_HISTORY_DAYS = 7
  Types/Interfaces:  PascalCase, I prefix → IUserProfile, INutritionLog
  Props types:       ComponentName+Props  → NutritionLogFormProps

---

## Component rules

- One component per file, always default export
- Props type defined in same file, above the component
- No business logic in components — call hooks instead
- No direct axios calls in components — always via a hook
- Max component length: 80 lines. If longer — extract sub-components
- ui/ components accept no API types — only primitives and callbacks

Good pattern:
  // NutritionLogForm.tsx
  type NutritionLogFormProps = {
    onSuccess: () => void
  }
  export default function NutritionLogForm({ onSuccess }: NutritionLogFormProps) {
    const { addLog, isLoading } = useNutritionLog()
    ...
  }

Bad pattern (never do this):
  // fetching inside a component directly
  const [logs, setLogs] = useState([])
  useEffect(() => { axios.get('/nutrition/logs').then(...) }, [])

---

## State management — when to use what

React Query (TanStack Query):
  All server data — nutrition logs, user profile, goals, recommendations
  useQuery for reads, useMutation for writes
  Cache invalidation after mutations — always invalidate related queries

Zustand (auth.store.ts):
  access_token, current user object, isAuthenticated
  Persist to localStorage via zustand/middleware persist

Zustand (ui.store.ts):
  sidebar open/closed, active modal, toast messages
  Never server data here — that belongs in React Query

Local useState:
  Form field values (controlled inputs)
  Toggle open/closed for a single component (dropdown, accordion)

Never:
  Server data in useState + useEffect fetch pattern
  Auth token in React context (use Zustand store)

---

## API client (services/api.ts)

Single axios instance, configured once:
  baseURL from import.meta.env.VITE_API_URL
  timeout: 10000
  headers: Content-Type application/json

Request interceptor:
  Attach Bearer token from auth.store on every request

Response interceptor:
  On 401 → clear auth store → redirect to /login
  On network error → throw structured AppError

All service functions return typed responses matching api_contracts.md:
  // nutrition.service.ts
  async function addNutritionLog(data: IAddLogRequest): Promise<INutritionLog>
  async function getLogs(date: string, days: number): Promise<ILogsResponse>

---

## SSE streaming (AI chat)

Use native EventSource, not axios (axios doesn't support streaming).
The hook useAiChat.ts owns all streaming logic:

  const [chunks, setChunks] = useState<string[]>([])
  const [isStreaming, setIsStreaming] = useState(false)

  function sendMessage(message: string) {
    setIsStreaming(true)
    setChunks([])
    const source = new EventSource(`${API_URL}/ai/chat/stream?message=...`,
      { withCredentials: true })

    source.onmessage = (e) => {
      if (e.data === '[DONE]') { source.close(); setIsStreaming(false); return }
      setChunks(prev => [...prev, e.data])
    }
    source.onerror = () => { source.close(); setIsStreaming(false) }
  }

ChatWindow renders chunks.join('') — never buffer full response before showing.
Show StreamingIndicator (animated dots) while isStreaming is true.
Disable send button while isStreaming is true.

---

## Testing rules

Test files: co-located next to the file they test
  NutritionLogForm.tsx → NutritionLogForm.test.tsx
  useNutritionLog.ts  → useNutritionLog.test.ts

What to test:
  - All custom hooks (mock API calls with msw or vi.mock)
  - Form validation logic
  - Utility functions in utils/ (100% coverage)
  - Key user flows: login, add nutrition log, send chat message

What NOT to test:
  - ui/ presentational components (Button, Card) — too trivial
  - React Query cache behaviour — it's a library, trust it
  - Exact styles or class names

Pattern for hook tests:
  import { renderHook, act } from '@testing-library/react'
  import { createWrapper } from '../test-utils'  // QueryClient wrapper

  it('adds a log and invalidates query', async () => {
    const { result } = renderHook(() => useNutritionLog(), { wrapper })
    await act(() => result.current.addLog(mockLogData))
    expect(mockMutation).toHaveBeenCalledWith(mockLogData)
  })

---

## Session rules — how to start a Claude Code session

Always open a session with:
  "Working on: <feature name>
   Read these files: <list max 3-4 files>
   Do NOT read: backend/ or mobile/ folders"

Example for adding nutrition log feature:
  "Working on: nutrition log form (Phase 3 frontend)
   Read: src/components/nutrition/NutritionLogForm.tsx,
         src/hooks/useNutritionLog.ts,
         src/services/nutrition.service.ts,
         /docs/api_contracts.md (POST /nutrition/logs only)
   Do not read any other files unless you ask me first."

Never ask Claude Code to read the entire src/ folder.
If a file is >100 lines, tell Claude which function to focus on.
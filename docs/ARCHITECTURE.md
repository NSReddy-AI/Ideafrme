# Ideafrme architecture

## MVP
Idea capture, persistent idea list, AI-generated structured plans, plan history, deletion, responsive UI.

## Request flow
Browser (Next.js React) → Next.js route handlers → Prisma/PostgreSQL. Plan generation calls OpenAI server-side; keys are never sent to the browser.

## Data
`Idea` has many `Plan` records. Deleting an idea cascades to its plans.

## Deployment
Use Node.js 22, managed PostgreSQL, and Vercel. Set `DATABASE_URL`, `OPENAI_API_KEY`, and optionally `OPENAI_MODEL`. Run `npx prisma db push` against the intended database before first deployment. Do not expose secrets in `NEXT_PUBLIC_*` variables.

## Security / production gates
This initial MVP is **single-workspace only**, without authentication. Do not expose it publicly with real user data until authentication, authorization/tenant scoping, rate limiting, abuse prevention, and spending controls are implemented. API calls currently operate on all ideas. AI output is untrusted text; the UI renders it as text, not HTML. Database migrations and backup policy should be established before production.

## Next iterations
Authentication and per-user ownership; edit idea; AI cost limits and rate limits; structured plan schema; audit logging; integration tests; monitoring.

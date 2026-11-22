# Ideafrme

An AI-powered idea workspace: capture ideas and turn them into actionable plans.

## MVP
- Create, list, and delete ideas
- Generate AI plans with summary, audience, value proposition, risks, and next steps
- Persist AI plan history in PostgreSQL
- Responsive Next.js UI

## Stack
Next.js 15, React 19, TypeScript, Prisma, PostgreSQL, OpenAI API, Vitest.

## Quick start
1. Install Node.js 22 and PostgreSQL.
2. `npm install`
3. Copy `.env.example` to `.env` and configure `DATABASE_URL` and `OPENAI_API_KEY`.
4. `npx prisma db push`
5. `npm run dev` and open http://localhost:3000.

## Verify
`npm test` · `npx tsc --noEmit` · `npm run build`

## Deploy
Vercel is supported. Configure environment variables in the host, provision PostgreSQL, and apply the Prisma schema before deploying. See [architecture and security notes](docs/ARCHITECTURE.md).

**Security:** This is an unauthenticated single-workspace prototype, not a production-ready multi-user SaaS. Do not deploy publicly with real data until authentication, authorization, and rate limiting are added.

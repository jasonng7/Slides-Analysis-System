# Slide Analysis System Web Demo

This is the Vercel-ready manager demo UI for the Slide Analysis System.

It intentionally does not run the full Python processing pipeline inside Vercel.
The current deployment goal is to visualize the MVP flow clearly:

1. Source content input
2. Content analysis
3. Recommendation
4. OSK template matching
5. PPTX generation
6. QA review

The production cloud version should add a hosted Python worker and persistent
storage such as Supabase or Vercel Blob.

## Local Run

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000`.

## Vercel Deploy

When importing the GitHub repo into Vercel, set:

- Framework preset: `Next.js`
- Root directory: `web`
- Build command: `npm run build`
- Install command: `npm install`

No environment variables are required for this demo UI.

## Later Cloud Processing

Use Supabase when you want:

- Browser file uploads
- Persistent job records
- Shared generated PPTX files
- Team access to previous recommendations and QA reports

Suggested future environment variables:

```text
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
PYTHON_WORKER_API_URL=
```

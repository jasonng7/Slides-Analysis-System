"use client";

import {
  BadgeCheck,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  ClipboardCheck,
  Database,
  FileInput,
  FileText,
  Layers3,
  LibraryBig,
  Loader2,
  MonitorCheck,
  Presentation,
  Search,
  ShieldCheck,
  UploadCloud
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

type StepStatus = "ready" | "running" | "complete";

type ApiJob = {
  job_id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  download_url?: string | null;
  error?: string | null;
  result?: {
    matching_method?: string;
    number_of_slides?: number;
    number_of_content_slides?: number;
    cloned_slide_count?: number;
    image_fallback_count?: number;
    qa_score?: number;
    qa_rating?: string;
    qa_top_issues?: Array<{ severity?: string; category?: string; message?: string }>;
  } | null;
};

type ApiHealth = {
  status: string;
  deck_count: number;
  slide_count: number;
  classified_slides: number;
  slides_with_text_embeddings: number;
  embedding_model: string;
  cleanup_policy: string;
};

const pipelineSteps = [
  {
    title: "Upload Source",
    description: "PDF, PPTX, DOCX, TXT, MD, CSV or pasted text",
    icon: FileInput
  },
  {
    title: "Analyze Content",
    description: "Summary, audience, entities, metrics, gaps",
    icon: BrainCircuit
  },
  {
    title: "Recommend Storyline",
    description: "Slide or deck structure with consulting logic",
    icon: Layers3
  },
  {
    title: "Match Templates",
    description: "Vector search across OSK slide patterns",
    icon: Search
  },
  {
    title: "Generate PPTX",
    description: "Editable reference-slide first draft",
    icon: Presentation
  },
  {
    title: "QA Review",
    description: "Deck length, duplicates, template fit, fallbacks",
    icon: ClipboardCheck
  }
];

const metrics = [
  { label: "Template decks", value: "2", detail: "OSK libraries indexed" },
  { label: "Classified slides", value: "147", detail: "Reusable patterns" },
  { label: "Text embeddings", value: "147", detail: "Vector search ready" },
  { label: "Automated tests", value: "46", detail: "Passing locally" }
];

const matchedPatterns = [
  {
    slide: "OSK Strategy Template Library · Slide 53",
    type: "market_entry_strategy",
    score: "0.78",
    use: "Board-ready market entry storyline"
  },
  {
    slide: "OSK Strategy Template Library · Slide 39",
    type: "competitor_benchmark",
    score: "0.74",
    use: "Peer comparison and evaluation matrix"
  },
  {
    slide: "OSK Strategy Template Library · Slide 43",
    type: "strategic_options",
    score: "0.72",
    use: "Build, buy, partner options logic"
  },
  {
    slide: "OSK Strategy Template Library · Slide 48",
    type: "risk_assessment",
    score: "0.69",
    use: "Risk and mitigation summary"
  }
];

const recommendedSlides = [
  "Executive decision summary",
  "Market context and opportunity",
  "Competitor landscape",
  "Build / buy / partner options",
  "Evaluation criteria and recommendation",
  "Implementation roadmap",
  "Key risks and mitigations"
];

const defaultText =
  "We are evaluating whether OSK should enter the earned wage access market in Malaysia. The market has emerging competitors, employer adoption is still early, and the key decision is whether to build, buy, or partner.";

function statusFor(index: number, activeStep: number): StepStatus {
  if (index < activeStep) return "complete";
  if (index === activeStep) return "running";
  return "ready";
}

export default function Home() {
  const [sourceText, setSourceText] = useState(defaultText);
  const [goal, setGoal] = useState("Create a board-ready market entry recommendation deck");
  const [mode, setMode] = useState("deck");
  const [activeStep, setActiveStep] = useState(0);
  const [hasRun, setHasRun] = useState(false);
  const [apiHealth, setApiHealth] = useState<ApiHealth | null>(null);
  const [apiError, setApiError] = useState("");
  const [job, setJob] = useState<ApiJob | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const apiBase = (process.env.NEXT_PUBLIC_API_BASE_URL || "").replace(/\/$/, "");
  const backendEnabled = Boolean(apiBase);

  const wordCount = useMemo(() => {
    return sourceText.trim().split(/\s+/).filter(Boolean).length;
  }, [sourceText]);

  useEffect(() => {
    if (!backendEnabled) return;
    fetch(`${apiBase}/api/health`)
      .then((response) => {
        if (!response.ok) throw new Error(`Backend health check failed: ${response.status}`);
        return response.json();
      })
      .then((payload: ApiHealth) => {
        setApiHealth(payload);
        setApiError("");
      })
      .catch((error: Error) => setApiError(error.message));
  }, [apiBase, backendEnabled]);

  function runDemo() {
    setHasRun(true);
    setActiveStep(0);
    pipelineSteps.forEach((_, index) => {
      window.setTimeout(() => setActiveStep(index + 1), 420 * (index + 1));
    });
  }

  async function startGeneration() {
    if (!backendEnabled) {
      runDemo();
      return;
    }

    setIsSubmitting(true);
    setApiError("");
    setJob(null);
    setHasRun(true);
    setActiveStep(1);

    try {
      const response = await fetch(`${apiBase}/api/jobs/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: sourceText, goal, mode })
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `Backend request failed: ${response.status}`);
      }
      const createdJob = (await response.json()) as ApiJob;
      setJob(createdJob);
      pollJob(createdJob.job_id);
    } catch (error) {
      setApiError(error instanceof Error ? error.message : "Generation failed");
      setIsSubmitting(false);
      setActiveStep(0);
    }
  }

  async function pollJob(jobId: string) {
    const startedAt = Date.now();
    const poll = async () => {
      try {
        const response = await fetch(`${apiBase}/api/jobs/${jobId}`);
        if (!response.ok) throw new Error(`Job status failed: ${response.status}`);
        const nextJob = (await response.json()) as ApiJob;
        setJob(nextJob);

        if (nextJob.status === "queued") setActiveStep(2);
        if (nextJob.status === "running") setActiveStep(4);
        if (nextJob.status === "succeeded") {
          setActiveStep(pipelineSteps.length);
          setIsSubmitting(false);
          return;
        }
        if (nextJob.status === "failed") {
          setApiError(nextJob.error || "Generation job failed");
          setIsSubmitting(false);
          return;
        }
        if (Date.now() - startedAt > 10 * 60 * 1000) {
          setApiError("Generation is taking longer than expected. Check EC2 logs or retry.");
          setIsSubmitting(false);
          return;
        }
        window.setTimeout(poll, 3000);
      } catch (error) {
        setApiError(error instanceof Error ? error.message : "Polling failed");
        setIsSubmitting(false);
      }
    };
    window.setTimeout(poll, 1500);
  }

  const finished = hasRun && activeStep >= pipelineSteps.length;
  const downloadHref = job?.download_url && backendEnabled ? `${apiBase}${job.download_url}` : "";
  const displayedQaScore = job?.result?.qa_score ?? 80;
  const displayedQaRating = job?.result?.qa_rating ?? "Usable with minor review";

  return (
    <main className="page-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Slide Analysis System MVP</p>
          <h1>Demo dashboard for content-to-deck intelligence</h1>
          <p className="subcopy">
            A Vercel-ready interface connected to an EC2 processing backend:
            content understanding, recommendation, OSK template matching,
            editable PPTX generation, and QA review.
          </p>
        </div>
        <div className="status-panel">
          <span className="status-dot" />
          <div>
            <strong>{backendEnabled ? "EC2 backend configured" : "Demo mode"}</strong>
            <span>
              {backendEnabled
                ? apiHealth
                  ? `${apiHealth.slide_count} slides, ${apiHealth.slides_with_text_embeddings} embeddings ready`
                  : "Checking backend health..."
                : "Set NEXT_PUBLIC_API_BASE_URL to enable real generation"}
            </span>
          </div>
        </div>
      </section>

      <section className="metrics-grid" aria-label="System status">
        {metrics.map((metric) => (
          <article className="metric-card" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            <p>{metric.detail}</p>
          </article>
        ))}
      </section>

      <section className="workspace-grid">
        <article className="input-panel">
          <div className="section-heading">
            <UploadCloud size={22} />
            <div>
              <h2>Demo Input</h2>
              <p>
                {backendEnabled
                  ? "Paste content and generate a real PPTX through the EC2 backend."
                  : "Paste content or show where a source file would be uploaded."}
              </p>
            </div>
          </div>

          <label className="field-label" htmlFor="goal">
            User goal
          </label>
          <input
            id="goal"
            value={goal}
            onChange={(event) => setGoal(event.target.value)}
            className="text-input"
          />

          <div className="field-row">
            <div>
              <label className="field-label" htmlFor="mode">
                Output mode
              </label>
              <select
                id="mode"
                value={mode}
                onChange={(event) => setMode(event.target.value)}
                className="text-input"
              >
                <option value="deck">Deck</option>
                <option value="slide">Single slide</option>
                <option value="audit">Audit</option>
                <option value="auto">Auto</option>
              </select>
            </div>
            <div className="file-drop">
              <FileText size={19} />
              <span>{backendEnabled ? "File upload API ready; UI upload comes next" : "File upload connects after API setup"}</span>
            </div>
          </div>

          <label className="field-label" htmlFor="source">
            Source content
          </label>
          <textarea
            id="source"
            value={sourceText}
            onChange={(event) => setSourceText(event.target.value)}
            className="text-area"
          />

          <div className="input-footer">
            <span>{wordCount} words</span>
            <button onClick={startGeneration} disabled={isSubmitting} className="primary-button">
              {isSubmitting
                ? "Generating..."
                : backendEnabled
                  ? "Generate real PPTX"
                  : "Run demo flow"}
            </button>
          </div>
          {apiError ? <p className="error-message">{apiError}</p> : null}
          {job ? (
            <div className="job-panel">
              <strong>Job {job.job_id.slice(0, 8)}</strong>
              <span>Status: {job.status}</span>
              {downloadHref ? (
                <a href={downloadHref} className="download-link">
                  Download generated PPTX
                </a>
              ) : null}
            </div>
          ) : null}
        </article>

        <article className="flow-panel">
          <div className="section-heading">
            <MonitorCheck size={22} />
            <div>
              <h2>Project Flow</h2>
              <p>What your manager will see this tool doing end to end.</p>
            </div>
          </div>

          <div className="pipeline-list">
            {pipelineSteps.map((step, index) => {
              const Icon = step.icon;
              const status = statusFor(index, activeStep);
              return (
                <div className={`pipeline-step ${status}`} key={step.title}>
                  <div className="step-icon">
                    {status === "complete" ? (
                      <CheckCircle2 size={20} />
                    ) : status === "running" ? (
                      <Loader2 className="spin" size={20} />
                    ) : (
                      <Icon size={20} />
                    )}
                  </div>
                  <div>
                    <strong>{step.title}</strong>
                    <span>{step.description}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </article>
      </section>

      <section className="result-grid">
        <article className="result-panel">
          <div className="section-heading">
            <BarChart3 size={22} />
            <div>
              <h2>Recommended Deck</h2>
              <p>
                {finished
                  ? backendEnabled
                    ? "Generated by the EC2 backend."
                    : "Generated from the demo input."
                  : backendEnabled
                    ? "Submit content to generate and download a real deck."
                    : "Run the demo flow to reveal the output."}
              </p>
            </div>
          </div>
          <ol className="slide-list">
            {recommendedSlides.map((title, index) => (
              <li key={title} className={finished ? "visible" : ""}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{title}</strong>
              </li>
            ))}
          </ol>
        </article>

        <article className="result-panel">
          <div className="section-heading">
            <LibraryBig size={22} />
            <div>
              <h2>Matched OSK Patterns</h2>
              <p>Examples of vector-search template matches used by the generator.</p>
            </div>
          </div>
          <div className="pattern-list">
            {matchedPatterns.map((pattern) => (
              <div className="pattern-card" key={pattern.slide}>
                <div>
                  <strong>{pattern.slide}</strong>
                  <span>{pattern.use}</span>
                </div>
                <div className="pattern-meta">
                  <span>{pattern.type}</span>
                  <b>{pattern.score}</b>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="result-panel qa-card">
          <div className="section-heading">
            <ShieldCheck size={22} />
            <div>
              <h2>QA Review</h2>
              <p>{job?.result ? "Latest generated deck result." : "Current local generated deck result."}</p>
            </div>
          </div>
          <div className="score-ring">{displayedQaScore}</div>
          <h3>{displayedQaRating}</h3>
          <ul className="qa-list">
            <li>
              {job?.result
                ? `${job.result.cloned_slide_count ?? 0} content slides cloned from matched source PPTX`
                : "23 / 23 content slides cloned from matched source PPTX"}
            </li>
            <li>{job?.result ? `${job.result.image_fallback_count ?? 0} image fallbacks detected` : "0 image fallbacks detected"}</li>
            <li>{job?.result?.matching_method ? `Matching method: ${job.result.matching_method}` : "Deck may need condensing for a board-ready first draft"}</li>
          </ul>
        </article>
      </section>

      <section className="deployment-panel">
        <div className="section-heading">
          <Database size={22} />
          <div>
            <h2>Deployment Model</h2>
            <p>The Vercel MVP is the demo interface. Full cloud processing can be added next.</p>
          </div>
        </div>
        <div className="deployment-grid">
          <div>
            <BadgeCheck size={20} />
              <strong>Vercel now</strong>
            <span>Dashboard, content input, job polling, and PPTX download link.</span>
          </div>
          <div>
            <BadgeCheck size={20} />
            <strong>EC2 backend</strong>
            <span>LibreOffice rendering, OpenAI calls, PPTX generation, QA jobs.</span>
          </div>
          <div>
            <BadgeCheck size={20} />
            <strong>Temporary storage</strong>
            <span>Generated files are kept briefly on EC2 and cleaned after 15 minutes.</span>
          </div>
        </div>
      </section>
    </main>
  );
}

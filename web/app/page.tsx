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
import { useMemo, useState } from "react";

type StepStatus = "ready" | "running" | "complete";

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

  const wordCount = useMemo(() => {
    return sourceText.trim().split(/\s+/).filter(Boolean).length;
  }, [sourceText]);

  function runDemo() {
    setHasRun(true);
    setActiveStep(0);
    pipelineSteps.forEach((_, index) => {
      window.setTimeout(() => setActiveStep(index + 1), 420 * (index + 1));
    });
  }

  const finished = hasRun && activeStep >= pipelineSteps.length;

  return (
    <main className="page-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Slide Analysis System MVP</p>
          <h1>Demo dashboard for content-to-deck intelligence</h1>
          <p className="subcopy">
            A Vercel-ready interface that explains the current working pipeline:
            content understanding, recommendation, OSK template matching,
            editable PPTX generation, and QA review.
          </p>
        </div>
        <div className="status-panel">
          <span className="status-dot" />
          <div>
            <strong>Demo-safe deployment</strong>
            <span>No Supabase required for this version</span>
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
              <p>Paste content or show where a source file would be uploaded.</p>
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
              <span>File upload connects in Stage 9B</span>
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
            <button onClick={runDemo} className="primary-button">
              Run demo flow
            </button>
          </div>
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
              <p>{finished ? "Generated from the demo input." : "Run the demo flow to reveal the output."}</p>
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
              <p>Current local generated deck result.</p>
            </div>
          </div>
          <div className="score-ring">80</div>
          <h3>Usable with minor review</h3>
          <ul className="qa-list">
            <li>23 / 23 content slides cloned from matched source PPTX</li>
            <li>0 image fallbacks detected</li>
            <li>Deck may need condensing for a board-ready first draft</li>
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
            <span>Dashboard, flow visualization, demo input, manager walkthrough.</span>
          </div>
          <div>
            <BadgeCheck size={20} />
            <strong>Python backend later</strong>
            <span>LibreOffice rendering, OpenAI calls, PPTX generation, QA jobs.</span>
          </div>
          <div>
            <BadgeCheck size={20} />
            <strong>Supabase optional</strong>
            <span>Needed only when you want cloud uploads, persistent jobs, and team access.</span>
          </div>
        </div>
      </section>
    </main>
  );
}

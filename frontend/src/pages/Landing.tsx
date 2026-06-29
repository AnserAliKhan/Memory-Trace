import { lazy, Suspense, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBackend } from '../hooks/useBackend';
import { BackendModal } from '../components/ui/BackendModal';
import { NavCapsule } from '../components/ui/NavCapsule';
import { SplitText } from '../components/ui/SplitText';
import { ScrollReveal } from '../components/ui/ScrollReveal';
import Aurora from '../components/reactbits/Aurora';
import CircularText from '../components/reactbits/CircularText';


export default function Landing() {
  const navigate = useNavigate();
  const { isConnected } = useBackend();
  const [isModalOpen, setIsModalOpen] = useState(false);

  // If already connected, redirect to the app
  if (isConnected) {
    navigate('/app/search');
    return null;
  }

  return (
    <div className="min-h-screen bg-canvas text-cream">
      <NavCapsule isAppMode={false} />

      {/* ── HERO SECTION ── */}
      <section className="relative min-h-screen flex items-center justify-center px-4 overflow-hidden">
        {/* Aurora background */}
        <Aurora
          colorStops={['#2a1e00', '#e8a838', '#ffedd7']}
          amplitude={0.8}
          blend={0.4}
          speed={0.4}
        />

        {/* Content – left aligned on desktop, center on mobile */}
        <div className="relative z-10 w-full max-w-6xl mx-auto px-4">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div className="text-center md:text-left">
              <p className="text-label font-label text-amber uppercase tracking-[0.2em] mb-4">
                LOCAL-FIRST KNOWLEDGE RETRIEVAL
              </p>
              <h1 className="text-display-lg font-display font-bold leading-[0.92] tracking-[-0.04em] mb-6">
                <SplitText text="A private search engine" /> <br />
                <span className="text-amber"><SplitText text="for your own notes." /></span>
              </h1>
              <p className="text-body text-muted max-w-xl mx-auto md:mx-0 mb-8">
                No cloud, no tracking, no subscriptions. Just answers from your own documents — running entirely on your machine.
              </p>
              <button
                onClick={() => setIsModalOpen(true)}
                className="px-8 py-3 bg-amber text-canvas font-bold rounded-md hover:brightness-110 transition-all"
              >
                Connect your backend →
              </button>
              <p className="text-label text-dim mt-8 text-[10px] tracking-[0.2em] uppercase">
                SCROLL TO EXPLORE
              </p>
            </div>

            {/* Right column – CircularText (desktop only) */}
            <div className="hidden md:flex justify-center items-center">
              <div className="relative w-[140px] h-[140px] opacity-40">
                <CircularText
                  text="LOCAL · PRIVATE · YOURS · OPEN · "
                  spinDuration={25}
                  onHover="slowDown"
                  className="!w-[140px] !h-[140px] [&_span]:!text-[9px] [&_span]:!text-amber [&_span]:!font-label [&_span]:!tracking-[0.1em]"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── FEATURES SECTION ── */}
      <section className="py-24 px-4 border-t border-border-dim">
        <div className="max-w-layout mx-auto">
          <p className="text-label font-label text-amber uppercase tracking-[0.2em] mb-8 text-center">
            What It Does
          </p>
          <ScrollReveal className="grid md:grid-cols-3 gap-12">
            <div className="text-center">
              <h3 className="text-heading-sm font-display font-bold text-cream mb-3">
                Semantic Search
              </h3>
              <p className="text-body text-muted">
                Not keyword matching — meaning matching. Ask in natural language, and find the right chunk of your knowledge.
              </p>
            </div>
            <div className="text-center">
              <h3 className="text-heading-sm font-display font-bold text-cream mb-3">
                Synthesized Answers
              </h3>
              <p className="text-body text-muted">
                Gemini reads your retrieved chunks and writes an answer in your own voice — citing every source it used.
              </p>
            </div>
            <div className="text-center">
              <h3 className="text-heading-sm font-display font-bold text-cream mb-3">
                Nothing Leaves Your Machine
              </h3>
              <p className="text-body text-muted">
                The backend runs locally. No telemetry, no cloud, no third-party access. Your data never leaves your computer.
              </p>
            </div>
          </ScrollReveal>
        </div>

      </section>



      {/* ── ABOUT / BUILT BY SECTION ── */}
      <section className="py-24 px-4 border-t border-border-dim">
        <div className="max-w-layout mx-auto grid md:grid-cols-2 gap-16 items-start">
          <ScrollReveal delay={0}>
            <div>
              <p className="text-label font-label text-amber uppercase tracking-[0.2em] mb-4">
                About ReFound
              </p>
              <h2 className="text-heading font-display font-bold text-cream mb-4">
                Rediscover what you already know.
              </h2>
              <p className="text-body text-muted mb-4">
                ReFound is a local‑first memory retrieval system. Import your documents — markdown, text, PDFs, or ChatGPT exports — and ask anything. The system finds the most relevant passages, reranks them, and synthesizes a coherent answer.
              </p>
              <p className="text-body text-muted">
                Built by a solo developer who believes that AI should work <em>for</em> you, not <em>on</em> you. Open source, self‑hosted, and completely private.
              </p>
            </div>
          </ScrollReveal>


          <div className="h-[500px] bg-raised border border-border rounded-lg flex items-center justify-center text-muted">
            {/* Lanyard */}
            <ScrollReveal delay={0.1}>
              <div className="h-[500px] bg-raised border border-border rounded-lg flex items-center justify-center text-muted">
                <div className="text-center">
                  <span className="text-label block text-amber">⚡</span>
                  <p className="text-sm mt-2">Lanyard card removed</p>
                  <p className="text-xs text-dim">(Placeholder – you can add your own image here)</p>
                </div>
              </div>
            </ScrollReveal>
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS SECTION ── */}
      <section className="py-24 px-4 border-t border-border-dim">
        <div className="max-w-layout mx-auto">
          <p className="text-label font-label text-amber uppercase tracking-[0.2em] mb-8 text-center">
            How It Works
          </p>
          <div className="grid md:grid-cols-3 gap-12 text-center">
            <div>
              <div className="text-amber text-4xl font-bold font-mono mb-4">01</div>
              <h3 className="text-heading-sm font-display font-bold text-cream mb-3">
                Import
              </h3>
              <p className="text-body text-muted">
                Drop your files (.md, .txt, .pdf, or ChatGPT JSON). The system chunks them, creates embeddings, and stores them locally.
              </p>
            </div>
            <div>
              <div className="text-amber text-4xl font-bold font-mono mb-4">02</div>
              <h3 className="text-heading-sm font-display font-bold text-cream mb-3">
                Ask
              </h3>
              <p className="text-body text-muted">
                Type a question in natural language. The system retrieves the most relevant chunks from your knowledge base.
              </p>
            </div>
            <div>
              <div className="text-amber text-4xl font-bold font-mono mb-4">03</div>
              <h3 className="text-heading-sm font-display font-bold text-cream mb-3">
                Get Answers
              </h3>
              <p className="text-body text-muted">
                Gemini synthesizes a coherent answer from your own words, complete with source citations. Everything stays local.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="py-8 px-4 border-t border-border-dim">
        <div className="max-w-layout mx-auto flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="text-cream font-bold font-display">ReFound</span>
            <span className="text-muted text-body-sm ml-4">Built locally, stays local.</span>
          </div>
          <div className="flex gap-6 text-body-sm text-muted">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-cream transition-colors"
            >
              GitHub
            </a>
            <button
              onClick={() => setIsModalOpen(true)}
              className="text-amber hover:text-cream transition-colors"
            >
              Connect your backend →
            </button>
          </div>
        </div>
      </footer>

      {/* Backend Modal */}
      <BackendModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConnected={() => navigate('/app/search')}
      />
    </div>
  );
}
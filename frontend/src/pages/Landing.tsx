import { useEffect, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'motion/react';
import { useNavigate } from 'react-router-dom';
import { BackendModal } from '../components/ui/BackendModal';
import { NavCapsule } from '../components/ui/NavCapsule';
import { useBackend } from '../hooks/useBackend';

const panels = [
  {
    number: '01',
    title: 'Find the thread',
    text: 'Semantic search moves past keywords and brings the right passage back into view.',
    accent: 'bg-amber',
  },
  {
    number: '02',
    title: 'Read the context',
    text: 'Retrieved chunks stay visible, so every answer has a trail back to your words.',
    accent: 'bg-[#e0683a]',
  },
  {
    number: '03',
    title: 'Keep ownership',
    text: 'Your index runs locally. Your notes remain yours before, during, and after every search.',
    accent: 'bg-[#5a8a9a]',
  },
];

const process = [
  ['01', 'Import', 'Notes, PDFs, images, text, and shared AI conversations.'],
  ['02', 'Ask', 'A natural question, not a keyword puzzle.'],
  ['03', 'Get answers', 'A grounded response with source citations.'],
];

function BootOverlay({ onComplete }: { onComplete: () => void }) {
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    const timer = window.setTimeout(onComplete, reduceMotion ? 450 : 1750);
    return () => window.clearTimeout(timer);
  }, [onComplete, reduceMotion]);

  return (
    <motion.div
      initial={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: reduceMotion ? 0.2 : 0.7 }}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-canvas"
      aria-label="Loading ReFound"
    >
      <div className="relative w-64 text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.92, filter: 'blur(10px)' }}
          animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
          transition={{ duration: 0.7 }}
          className="font-display text-5xl font-bold tracking-[-0.08em]"
        >
          RF<span className="text-amber">.</span>
        </motion.div>
        <motion.p
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35, duration: 0.55 }}
          className="mt-4 text-label uppercase tracking-[0.28em] text-muted"
        >
          Finding your way back
        </motion.p>
        <div className="mt-8 h-px overflow-hidden bg-border">
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ delay: 0.45, duration: reduceMotion ? 0.2 : 1.1, ease: [0.2, 0.6, 0.2, 1] }}
            className="h-full origin-left bg-amber"
          />
        </div>
      </div>
    </motion.div>
  );
}

function ProductWalkthrough() {
  return (
    <section className="border-y border-border-dim px-6 py-24 sm:px-10 lg:px-16">
      <div className="mx-auto grid max-w-layout items-center gap-14 lg:grid-cols-[0.7fr_1.3fr]">
        <div>
          <p className="text-label font-label uppercase tracking-[0.24em] text-amber">Not a promise. A pipeline.</p>
          <h2 className="mt-5 text-heading font-display font-bold leading-tight">See what happens after you press search.</h2>
          <p className="mt-6 max-w-md text-body leading-relaxed text-muted">
            ReFound parses your material, builds a local index, retrieves the closest passages, then shows the evidence beside its answer.
          </p>
          <div className="mt-8 space-y-3 font-mono text-xs text-muted">
            <p><span className="text-amber">$</span> refound import ./your-library</p>
            <p><span className="text-[#5a8a9a]">ok</span> 24 documents indexed locally</p>
            <p><span className="text-[#e0683a]">-&gt;</span> ready for your question</p>
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 35, rotateX: 8 }}
          whileInView={{ opacity: 1, y: 0, rotateX: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.9, ease: [0.2, 0.6, 0.2, 1] }}
          className="relative overflow-hidden border border-border bg-surface/70 shadow-[0_28px_90px_rgba(0,0,0,0.35)]"
        >
          <div className="flex items-center justify-between border-b border-border-dim px-5 py-3 font-mono text-[10px] uppercase tracking-[0.18em] text-muted">
            <span><span className="mr-2 inline-block h-2 w-2 rounded-full bg-[#5a8a9a]" /> local index</span>
            <span>24 docs / 186 chunks</span>
          </div>
          <div className="p-5 sm:p-8">
            <div className="border-b border-border-dim pb-5 font-mono text-sm text-cream">
              <span className="mr-3 text-amber">&gt;</span> What did I write about keeping systems private?
            </div>
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.35, duration: 0.7 }}
              className="py-6"
            >
              <p className="text-body leading-relaxed text-cream">Your notes return to the same principle: keep computation close to the source, expose the reasoning, and make ownership visible.</p>
              <p className="mt-4 border-l-2 border-amber pl-4 text-body-sm leading-relaxed text-muted">ReFound keeps retrieval local and cites the passages used to form this answer.</p>
            </motion.div>
            <div className="space-y-2 border-t border-border-dim pt-5 font-mono text-[11px] text-muted">
              <div className="flex items-center justify-between"><span>01 / privacy-notes.md</span><span className="text-amber">0.94</span></div>
              <div className="flex items-center justify-between"><span>02 / architecture-chat.json</span><span className="text-amber">0.87</span></div>
              <div className="flex items-center justify-between"><span>03 / local-first.txt</span><span className="text-amber">0.81</span></div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function MemoryFlow() {
  return (
    <div className="relative mt-20 hidden h-20 md:block">
      <svg viewBox="0 0 1000 80" className="absolute inset-0 h-full w-full overflow-visible" aria-hidden="true">
        <motion.path
          d="M 40 40 C 230 5, 300 75, 500 40 S 770 5, 960 40"
          fill="none"
          stroke="rgba(232,168,56,0.55)"
          strokeWidth="1"
          initial={{ pathLength: 0 }}
          whileInView={{ pathLength: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 1.8, ease: [0.2, 0.6, 0.2, 1] }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-between">
        {process.map(([number, title]) => (
          <div key={number} className="flex flex-col items-center gap-2 bg-canvas px-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-full border border-amber text-[10px] font-mono text-amber">{number}</span>
            <span className="text-label uppercase tracking-[0.16em] text-muted">{title}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Landing() {
  const navigate = useNavigate();
  const { isConnected } = useBackend();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isBooting, setIsBooting] = useState(true);

  if (isConnected) {
    navigate('/app/search');
    return null;
  }

  return (
    <div className="min-h-screen overflow-hidden bg-canvas text-cream">
      <AnimatePresence>
        {isBooting && <BootOverlay onComplete={() => setIsBooting(false)} />}
      </AnimatePresence>
      <NavCapsule isAppMode={false} />

      <main>
        <section className="relative flex min-h-[92vh] items-center overflow-hidden px-6 pb-20 pt-32 sm:px-10 lg:px-16">
          <div className="pointer-events-none absolute -right-40 top-20 h-[38rem] w-[38rem] rounded-full bg-amber/10 blur-[120px]" />
          <div className="pointer-events-none absolute bottom-0 left-0 h-64 w-2/3 bg-[#e0683a]/5 blur-[100px]" />

          <div className="relative z-10 mx-auto grid w-full max-w-layout items-center gap-16 lg:grid-cols-[1.05fr_0.95fr]">
            <motion.div
              initial={{ opacity: 0, y: 18, filter: 'blur(10px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              transition={{ duration: 0.8, ease: [0.2, 0.6, 0.2, 1] }}
            >
              <p className="mb-5 text-label font-label uppercase tracking-[0.24em] text-amber">Rediscover what you already know</p>
              <h1 className="max-w-4xl text-[clamp(3.4rem,8vw,8rem)] font-display font-bold leading-[0.88] tracking-[-0.07em]">
                Search your past.
                <span className="block text-muted">Move forward.</span>
              </h1>
              <p className="mt-8 max-w-xl text-body-lg leading-relaxed text-muted">
                ReFound is a local-first memory assistant for the ideas, notes, and conversations that should not disappear into a folder.
              </p>
              <div className="mt-9 flex flex-wrap items-center gap-5">
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="group rounded-md bg-amber px-7 py-3.5 font-bold text-canvas transition duration-300 hover:-translate-y-1 hover:brightness-110"
                >
                  Start with your library <span className="ml-2 inline-block transition-transform group-hover:translate-x-2">-&gt;</span>
                </button>
                <span className="text-label uppercase tracking-[0.18em] text-dim">No cloud / no tracking</span>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 34 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3, duration: 0.9 }}
              className="relative mx-auto h-[25rem] w-full max-w-md"
            >
              <div className="absolute right-[10%] top-[8%] h-40 w-40 rotate-12 border border-amber/40 bg-amber/5 shadow-[20px_24px_80px_rgba(232,168,56,0.14)] [transform:perspective(700px)_rotateX(46deg)_rotateZ(14deg)]" />
              <div className="absolute left-[12%] top-[28%] h-52 w-52 -rotate-12 border border-[#e0683a]/40 bg-[#e0683a]/5 [transform:perspective(700px)_rotateX(52deg)_rotateY(-20deg)_rotateZ(-12deg)]" />
              <div className="absolute bottom-[5%] right-[18%] h-44 w-64 border border-[#5a8a9a]/40 bg-[#5a8a9a]/5 [transform:perspective(700px)_rotateX(55deg)_rotateY(18deg)_rotateZ(8deg)]" />
              <div className="absolute left-1/2 top-1/2 h-24 w-24 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle_at_35%_30%,#ffedd7,#e8a838_30%,#513217_70%,#100904)] shadow-[0_0_70px_rgba(232,168,56,0.3)]" />
              <div className="absolute bottom-0 left-0 border-l border-amber/50 pl-3 font-mono text-xs leading-relaxed text-muted">LOCAL INDEX<br /><span className="text-amber">READY TO SEARCH</span></div>
            </motion.div>
          </div>
        </section>

        <ProductWalkthrough />

        <section className="border-y border-border-dim px-6 py-24 sm:px-10 lg:px-16">
          <div className="mx-auto max-w-layout">
            <div className="mb-14 max-w-xl">
              <p className="text-label font-label uppercase tracking-[0.24em] text-amber">What you get</p>
              <h2 className="mt-4 text-heading font-display font-bold leading-tight">A short path from scattered material to useful memory.</h2>
            </div>
            <div className="space-y-4">
              {panels.map((panel, index) => (
                <motion.article
                  key={panel.number}
                  initial={{ opacity: 0, x: index % 2 ? 42 : -42 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: '-70px' }}
                  transition={{ duration: 0.65, delay: index * 0.08 }}
                  className="group relative grid gap-6 overflow-hidden border border-border bg-surface/50 px-6 py-7 transition duration-500 hover:-translate-y-1 hover:border-amber/50 hover:bg-raised/70 md:grid-cols-[7rem_1fr_1.4fr] md:items-center md:px-8"
                >
                  <div className={`absolute inset-y-0 left-0 w-1 ${panel.accent}`} />
                  <span className="font-mono text-4xl text-muted transition-colors group-hover:text-amber">{panel.number}</span>
                  <h3 className="text-heading-sm font-display font-bold">{panel.title}</h3>
                  <p className="max-w-lg text-body text-muted">{panel.text}</p>
                </motion.article>
              ))}
            </div>
            <MemoryFlow />
          </div>
        </section>

        <section className="px-6 py-24 sm:px-10 lg:px-16">
          <div className="mx-auto grid max-w-layout gap-16 lg:grid-cols-[0.75fr_1.25fr]">
            <div className="lg:sticky lg:top-32 lg:self-start">
              <p className="text-label font-label uppercase tracking-[0.24em] text-amber">Built for recall</p>
              <h2 className="mt-5 text-heading font-display font-bold leading-tight">Your thinking deserves more than a search bar.</h2>
              <p className="mt-6 text-body leading-relaxed text-muted">Import the material you already have. ReFound handles chunking, embeddings, retrieval, and source-aware answers while keeping the index on your machine.</p>
            </div>
            <div className="relative pl-8 md:pl-16">
              <div className="absolute bottom-0 left-2 top-0 w-px bg-border md:left-8" />
              <motion.div
                initial={{ scaleY: 0 }}
                whileInView={{ scaleY: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 1.4, ease: [0.2, 0.6, 0.2, 1] }}
                className="absolute left-2 top-0 h-full w-px origin-top bg-gradient-to-b from-amber via-[#e0683a] to-[#5a8a9a] md:left-8"
              />
              <div className="space-y-20">
                {process.map(([number, title, text]) => (
                  <motion.div
                    key={number}
                    initial={{ opacity: 0, y: 22 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, margin: '-100px' }}
                    transition={{ duration: 0.6 }}
                    className="relative"
                  >
                    <span className="absolute -left-[2.05rem] top-0 flex h-8 w-8 items-center justify-center rounded-full border border-amber bg-canvas font-mono text-[10px] text-amber md:-left-[3.05rem]">{number}</span>
                    <h3 className="text-heading-sm font-display font-bold">{title}</h3>
                    <p className="mt-3 max-w-lg text-body text-muted">{text}</p>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border-dim px-6 py-8 sm:px-10 lg:px-16">
        <div className="mx-auto flex max-w-layout flex-wrap items-center justify-between gap-4">
          <span className="font-display font-bold">ReFound <span className="ml-3 font-sans text-body-sm font-normal text-muted">Built locally, stays local.</span></span>
          <button onClick={() => setIsModalOpen(true)} className="text-body-sm text-amber transition-colors hover:text-cream">Connect your backend -&gt;</button>
        </div>
      </footer>

      <BackendModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onConnected={() => navigate('/app/search')} />
    </div>
  );
}

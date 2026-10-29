import { useEffect, useState } from 'react';
import { useBackend } from '../../hooks/useBackend';

/**
 * Labels hosted preview / UAT deployments (Cloudflare Pages) so testers know
 * what they're looking at and that the backend must run on their machine.
 * Renders nothing on production (main) and local builds. See docs/DEPLOYMENT.md.
 */

const BRANCH = __APP_BRANCH__;
const COMMIT = __APP_COMMIT__.slice(0, 7);
const DOCS_URL = 'https://github.com/mrkhan3870/Memory-Trace-/blob/main/docs/DEPLOYMENT.md';

interface ManifestPR {
  number: number;
  title: string;
  url: string;
  reason?: string;
}

interface UatManifest {
  main_sha: string;
  included: ManifestPR[];
  not_included: ManifestPR[];
  overrides: { winner: number; loser: number; files: string[] }[];
}

export function EnvBanner() {
  const { isConnected } = useBackend();
  const [manifest, setManifest] = useState<UatManifest | null>(null);
  const [open, setOpen] = useState(true);

  useEffect(() => {
    if (BRANCH !== 'uat') return;
    fetch('/uat-manifest.json')
      .then((res) => (res.ok ? res.json() : null))
      .then(setManifest)
      .catch(() => setManifest(null));
  }, []);

  if (!BRANCH || BRANCH === 'main') return null;

  const isUat = BRANCH === 'uat';
  const label = isUat ? 'UAT' : 'Preview';
  const checkout = isUat ? 'git fetch origin && git checkout origin/uat' : `git checkout ${BRANCH}`;

  return (
    <div className="fixed bottom-4 left-4 z-50 max-w-sm bg-raised border border-amber rounded-md shadow-lg text-xs text-cream">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center gap-2 px-3 py-2 text-left"
        aria-expanded={open}
      >
        <span className="font-bold text-amber tracking-wider">{label}</span>
        <span className="text-muted truncate">
          {isUat ? `main@${manifest?.main_sha.slice(0, 7) ?? '…'}` : BRANCH}
          {COMMIT && ` · ${COMMIT}`}
        </span>
        <span className="ml-auto text-muted">{open ? '–' : '+'}</span>
      </button>

      {open && (
        <div className="px-3 pb-3 space-y-2">
          {isUat && manifest && <UatDetails manifest={manifest} />}

          <p className={isConnected ? 'text-muted' : 'text-cream'}>
            {isConnected ? 'Backend connected. ' : 'Backend offline. '}
            Run it locally from the matching code:{' '}
            <code className="font-mono text-amber break-words">{checkout}</code>, then{' '}
            <code className="font-mono text-amber">uvicorn main:app --port 8000</code> in{' '}
            <code className="font-mono">backend/</code>.
          </p>
          {!isConnected && (
            <p className="text-muted">
              Use Chrome, Edge or Firefox and allow local network access when asked.{' '}
              <a href={DOCS_URL} target="_blank" rel="noreferrer" className="text-amber underline">
                Troubleshooting
              </a>
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function UatDetails({ manifest }: { manifest: UatManifest }) {
  return (
    <div className="space-y-1">
      {manifest.included.length === 0 ? (
        <p className="text-muted">No open PRs in UAT — this is main.</p>
      ) : (
        <ul className="space-y-0.5">
          {manifest.included.map((pr) => (
            <li key={pr.number} className="truncate">
              <PrLink pr={pr} /> {pr.title}
            </li>
          ))}
        </ul>
      )}
      {manifest.overrides.map((o) => (
        <p key={`${o.winner}-${o.loser}`} className="text-muted">
          #{o.winner} overrides #{o.loser} in {o.files.join(', ')}
        </p>
      ))}
      {manifest.not_included.length > 0 && (
        <p className="text-muted">
          Not included:{' '}
          {manifest.not_included.map((pr, i) => (
            <span key={pr.number} title={pr.reason}>
              {i > 0 && ', '}
              <PrLink pr={pr} />
            </span>
          ))}
        </p>
      )}
    </div>
  );
}

function PrLink({ pr }: { pr: ManifestPR }) {
  return (
    <a href={pr.url} target="_blank" rel="noreferrer" className="text-amber underline">
      #{pr.number}
    </a>
  );
}

import { NavLink, useNavigate } from 'react-router-dom';
import { useBackend } from '../../hooks/useBackend';
import { useTheme } from '../../hooks/useTheme';
import { motion } from 'motion/react';

interface NavCapsuleProps {
  /** If true, shows app links (Search, Import, History). Otherwise shows "Connect" CTA. */
  isAppMode?: boolean;
}

export function NavCapsule({ isAppMode = false }: NavCapsuleProps) {
  const navigate = useNavigate();
  const { isConnected } = useBackend();
  const { theme, toggle } = useTheme();

  const linkClasses = ({ isActive }: { isActive: boolean }) =>
    `text-label font-label text-muted hover:text-cream transition-colors px-3 py-1 ${isActive ? 'text-cream border-b border-amber' : ''
    }`;

  return (
    <nav className="fixed top-4 left-1/2 -translate-x-1/2 z-50 bg-raised border border-border rounded-pill px-[18px] py-2 flex items-center gap-2 shadow-lg">
      {/* Brand mark */}
      <span className="text-cream font-bold font-display text-label tracking-wider mr-2">
        RF·
      </span>

      {isAppMode ? (
        // App mode: show Search, Import, History
        <>
          <NavLink to="/app/search" className={linkClasses}>
            Search
          </NavLink>
          <NavLink to="/app/import" className={linkClasses}>
            Import
          </NavLink>
          <NavLink to="/app/history" className={linkClasses}>
            History
          </NavLink>
        </>
      ) : (
        // Landing mode: show "Connect" button
        <button
          onClick={() => navigate('/')}
          className="text-label font-label text-amber hover:text-cream transition-colors px-3 py-1"
        >
          Connect
        </button>
      )}

      {/* Connection indicator */}
      <div className="flex items-center gap-1 ml-2 text-label font-label">
        <span
          className={`inline-block w-2 h-2 rounded-full ${isConnected ? 'bg-amber' : 'bg-dim'
            } animate-pulse`}
        />
        <span className={isConnected ? 'text-amber' : 'text-dim'}>
          {isConnected ? 'Connected' : 'Offline'}
        </span>
      </div>

      {/* Theme toggle */}
      <motion.button
        onClick={toggle}
        className="text-muted hover:text-cream transition-colors ml-1 text-label"
        aria-label="Toggle theme"
        whileTap={{ rotate: 180 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      >
        {theme === 'dark' ? '☀️' : '🌙'}
      </motion.button>
    </nav>
  );
}
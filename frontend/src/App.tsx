import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'motion/react';
import { useRef, useEffect, useState } from 'react';
import { PageTransition } from './components/layout/PageTransition';
import { CurtainTransition } from './components/layout/CurtainTransition';
import { EnvBanner } from './components/ui/EnvBanner';

// Page imports
import Landing from './pages/Landing';
import Search from './pages/app/Search';
import Import from './pages/app/Import';
import History from './pages/app/History';
import Settings from './pages/app/Settings';

function AppRoutes() {
  const location = useLocation();
  const prevPathRef = useRef(location.pathname);
  const [showCurtain, setShowCurtain] = useState(false);

  useEffect(() => {
    const prevPath = prevPathRef.current;
    const isLandingNow = location.pathname === '/';
    const wasLanding = prevPath === '/';
    const isAppNow = location.pathname.startsWith('/app');
    const wasApp = prevPath.startsWith('/app');

    // Show curtain only when switching between landing and app
    const transitioningBetweenLayers = (isLandingNow && wasApp) || (isAppNow && wasLanding);
    
    if (transitioningBetweenLayers) {
      setShowCurtain(true);
      // Hide after the curtain animation completes (500ms)
      setTimeout(() => setShowCurtain(false), 500);
    }

    prevPathRef.current = location.pathname;
  }, [location.pathname]);

  return (
    <CurtainTransition isActive={showCurtain}>
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<PageTransition><Landing /></PageTransition>} />
          <Route path="/app/search" element={<PageTransition><Search /></PageTransition>} />
          <Route path="/app/import" element={<PageTransition><Import /></PageTransition>} />
          <Route path="/app/history" element={<PageTransition><History /></PageTransition>} />
          <Route path="/app/settings" element={<PageTransition><Settings /></PageTransition>} />
        </Routes>
      </AnimatePresence>
    </CurtainTransition>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
      <EnvBanner />
    </BrowserRouter>
  );
}

export default App;
import { motion, AnimatePresence } from 'motion/react';

interface CurtainTransitionProps {
  isActive: boolean;
  children: React.ReactNode;
}

export function CurtainTransition({ isActive, children }: CurtainTransitionProps) {
  return (
    <div className="relative overflow-hidden">
      {children}
      <AnimatePresence>
        {isActive && (
          <motion.div
            className="fixed inset-0 z-[100] bg-canvas origin-bottom"
            initial={{ scaleY: 0 }}
            animate={{ scaleY: 1 }}
            exit={{ scaleY: 0 }}
            transition={{ duration: 0.5, ease: [0.4, 0.0, 0.2, 1.0] }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
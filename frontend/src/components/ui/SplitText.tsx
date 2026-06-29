import { motion } from 'motion/react';
import { useReducedMotion } from 'motion/react';

interface SplitTextProps {
  text: string;
  className?: string;
  stagger?: number;
  duration?: number;
}

export function SplitText({ text, className = '', stagger = 0.022, duration = 0.4 }: SplitTextProps) {
  const prefersReduced = useReducedMotion();

  // If reduced motion, render the text as-is
  if (prefersReduced) {
    return <span className={className}>{text}</span>;
  }

  const chars = text.split('');

  return (
    <span className={className}>
      {chars.map((char, i) => (
        <motion.span
          key={i}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration,
            delay: i * stagger,
            ease: [0.0, 0.0, 0.2, 1.0],
          }}
          className="inline-block"
        >
          {char === ' ' ? '\u00A0' : char}
        </motion.span>
      ))}
    </span>
  );
}
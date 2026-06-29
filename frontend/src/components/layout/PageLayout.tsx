import { NavCapsule } from '../ui/NavCapsule';

interface PageLayoutProps {
  children: React.ReactNode;
}

export function PageLayout({ children }: PageLayoutProps) {
  return (
    <>
      <NavCapsule />
      <main className="pt-20 px-4 max-w-layout mx-auto min-h-screen">
        {children}
      </main>
    </>
  );
}
import type { ReactNode } from 'react';
import { useLocation } from 'react-router-dom';
import { TerminalDrawer } from '../components/terminal/TerminalDrawer';
import { Sidebar } from '../components/layout/Sidebar';
import { PageContainer } from '../components/layout/LayoutPack';
import { cn } from '../lib/utils/cn';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const location = useLocation();
  const isPlayground = location.pathname.startsWith('/playground');
  const isDocs = location.pathname.startsWith('/documentation');

  return (
    <div className="min-h-screen th-bg th-text font-sans flex overflow-x-hidden theme-transition">
      {/* Sidebar Navigation — hidden on docs (docs has its own sidebar) */}
      {!isDocs && <Sidebar />}

      {/* Main App Workspace */}
      {isDocs ? (
        <main className="flex-1 relative z-10 min-w-0">
          {children}
        </main>
      ) : (
        <PageContainer>
          <main className={cn("flex-1 relative z-10", !isPlayground && "pb-24")}>
            {children}
          </main>
        </PageContainer>
      )}

      {/* Global Terminal Console - Hidden on Playground and Docs */}
      {!isPlayground && !isDocs && <TerminalDrawer />}
      
      {/* Aesthetic Background Grain/Glow */}
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_top_right,rgba(0,0,0,0.01)_0%,transparent_50%)] dark:bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.01)_0%,transparent_50%)] pointer-events-none z-0" />
    </div>
  );
}

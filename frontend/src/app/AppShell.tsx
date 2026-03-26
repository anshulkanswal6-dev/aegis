import type { ReactNode } from 'react';
import { useLocation } from 'react-router-dom';
import { TerminalDrawer } from '../components/terminal/TerminalDrawer';
import { Sidebar } from '../components/layout/Sidebar';
import { PageContainer } from '../components/layout/LayoutPack';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const location = useLocation();
  const isPlayground = location.pathname.startsWith('/playground');

  return (
    <div className="min-h-screen bg-[#f9f9f9] text-black font-sans selection:bg-black selection:text-white flex overflow-x-hidden">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main App Workspace */}
      <PageContainer>
        <main className="flex-1 pb-24 relative z-10">
          {children}
        </main>
      </PageContainer>

      {/* Global Terminal Console - Hidden on Playground */}
      {!isPlayground && <TerminalDrawer />}
      
      {/* Aesthetic Background Grain/Glow */}
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_top_right,rgba(0,0,0,0.01)_0%,transparent_50%)] pointer-events-none z-0" />
    </div>
  );
}


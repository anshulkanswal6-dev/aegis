import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './app/AppShell';
import LandingPage from './pages/LandingPage';
import WalletPage from './pages/WalletPage';
import PlaygroundPage from './pages/PlaygroundPage';
import ProjectsPage from './pages/ProjectsPage';
import ProjectDetailPage from './pages/ProjectDetailPage';

function App() {
  return (
    <Router>
      <AppShell>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/wallet" element={<WalletPage />} />
          
          {/* Phase 2 Routes */}
          <Route path="/playground" element={<PlaygroundPage />} />
          <Route path="/playground/:projectId" element={<PlaygroundPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          
          <Route path="/404" element={<div className="p-20 text-center font-bold">404 - Not Found</div>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell>
    </Router>
  );
}

export default App;

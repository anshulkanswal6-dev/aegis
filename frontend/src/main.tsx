import { StrictMode, Component, type ErrorInfo, type ReactNode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { Web3Provider } from './app/providers/Web3Provider'
import { ToastProvider } from './hooks/useToast'

// Error boundary to catch render crashes
class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('React Error Boundary caught:', error, info);
  }
  
  render() {
    if (this.state.error) {
      return (
        <div style={{ background: '#000', color: '#fff', minHeight: '100vh', padding: '60px', fontFamily: 'monospace' }}>
          <h1 style={{ fontSize: '2rem', marginBottom: '20px', color: '#f43f5e' }}>⚠️ Runtime Error</h1>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: '14px', color: '#a1a1aa', lineHeight: '1.8' }}>
            {this.state.error.message}
          </pre>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: '11px', color: '#52525b', marginTop: '20px', lineHeight: '1.6' }}>
            {this.state.error.stack}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}

const root = document.getElementById('root')!;
createRoot(root).render(
  <StrictMode>
    <ErrorBoundary>
      <Web3Provider>
        <ToastProvider>
          <App />
        </ToastProvider>
      </Web3Provider>
    </ErrorBoundary>
  </StrictMode>,
)

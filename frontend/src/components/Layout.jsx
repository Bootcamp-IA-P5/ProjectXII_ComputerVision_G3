import React from 'react';
import { Link } from 'react-router-dom';
import { Camera, Github } from 'lucide-react';
import { useLocation } from 'react-router-dom';

const Layout = ({ children }) => {
  const location = useLocation();

  return (
    <div className="layout">
      <header className="header glass-panel">
        <div className="container header-content">
          <Link to="/" className="logo">
            <Camera className="logo-icon" />
            <span className="logo-text">BrandDetector<span className="accent">AI</span></span>
          </Link>

          <nav className="nav">
            <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}>
              Upload
            </Link>
            <Link to="/videos" className={`nav-link ${location.pathname === '/videos' ? 'active' : ''}`}>
              History
            </Link>
          </nav>

          <a href="https://github.com/project-xii" target="_blank" rel="noreferrer" className="github-link">
            <Github size={20} />
          </a>
        </div>
      </header>

      <main className="main-content container">
        {children}
      </main>

      <footer className="footer">
        <div className="container">
          <p>© 2026 Project XII - Computer Vision Group 3</p>
        </div>
      </footer>

      <style>{`
        .layout {
          display: flex;
          flex-direction: column;
          min-height: 100vh;
        }

        .header {
          position: sticky;
          top: 0;
          z-index: 50;
          margin: 1rem;
          border-radius: var(--radius-lg);
        }

        .header-content {
          display: flex;
          align-items: center;
          justify-content: space-between;
          height: 4rem;
        }

        .logo {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-weight: 700;
          font-size: 1.25rem;
          color: var(--text-primary);
        }

        .logo-icon {
          color: var(--primary-color);
        }

        .accent {
          color: var(--primary-color);
        }

        .nav {
          display: flex;
          gap: 2rem;
        }

        .nav-link {
          color: var(--text-secondary);
          font-weight: 500;
          position: relative;
        }

        .nav-link:hover, .nav-link.active {
          color: var(--text-primary);
        }

        .nav-link.active::after {
          content: '';
          position: absolute;
          bottom: -4px;
          left: 0;
          right: 0;
          height: 2px;
          background-color: var(--primary-color);
          border-radius: 2px;
        }

        .github-link {
          color: var(--text-secondary);
        }

        .github-link:hover {
          color: var(--text-primary);
        }

        .main-content {
          flex: 1;
          width: 100%;
          padding-top: 2rem;
          padding-bottom: 2rem;
        }

        .footer {
          margin-top: auto;
          padding: 2rem 0;
          text-align: center;
          color: var(--text-secondary);
          font-size: 0.875rem;
        }
      `}</style>
    </div>
  );
};

export default Layout;

import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        <meta name="description" content="Widget2Code Viewer" />
        <style
          id="ssr-styles"
          dangerouslySetInnerHTML={{
            __html: `
              /* Hide everything until fully loaded */
              html {
                visibility: hidden;
              }

              html.loaded {
                visibility: visible;
              }

              body {
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: #fff;
                overflow: hidden;
              }

              /* Loading screen */
              #loading-screen {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: #fff;
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                visibility: visible;
              }

              html.loaded #loading-screen {
                opacity: 0;
                pointer-events: none;
                transition: opacity 0.3s ease-out;
              }

              /* Spinner */
              .spinner {
                width: 48px;
                height: 48px;
                border: 4px solid #f0f0f0;
                border-top-color: #1677ff;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
              }

              @keyframes spin {
                to { transform: rotate(360deg); }
              }

              /* Critical styles that must be applied immediately */
              * {
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
                box-sizing: border-box;
              }

              #__next {
                height: 100%;
                width: 100%;
                position: relative;
              }
            `,
          }}
        />
      </Head>
      <body>
        <div id="loading-screen">
          <div className="spinner"></div>
        </div>
        <Main />
        <NextScript />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // Mark as loaded after styles are ready
              window.addEventListener('DOMContentLoaded', function() {
                // Small delay to ensure all styles are applied
                requestAnimationFrame(function() {
                  requestAnimationFrame(function() {
                    document.documentElement.classList.add('loaded');
                  });
                });
              });
            `,
          }}
        />
      </body>
    </Html>
  );
}

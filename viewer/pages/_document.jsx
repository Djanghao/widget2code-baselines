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
              /* Critical CSS for preventing FOUC */
              * {
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
              }

              body {
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: #fff;
                overflow: hidden;
              }

              #__next {
                height: 100%;
                width: 100%;
                position: relative;
              }

              /* Prevent layout shift during initial load */
              .ant-layout-header {
                background: #001529;
                height: 64px;
              }

              /* Prevent button icon shift */
              .ant-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
              }
            `,
          }}
        />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}

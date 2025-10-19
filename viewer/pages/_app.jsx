import { StyleProvider } from '@ant-design/cssinjs';
import { ConfigProvider } from 'antd';
import "antd/dist/reset.css";
import "../styles/globals.css";

export default function App({ Component, pageProps }) {
  return (
    <StyleProvider hashPriority="high">
      <ConfigProvider
        theme={{
          cssVar: true,
          hashed: false,
        }}
      >
        <Component {...pageProps} />
      </ConfigProvider>
    </StyleProvider>
  );
}


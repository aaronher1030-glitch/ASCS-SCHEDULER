import type { AppProps } from 'next/app';
import { ThemeProvider } from '../components/ThemeProvider';
import '../styles/globals.css';

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <ThemeProvider>
      <Component {...pageProps} />
    </ThemeProvider>
  );
}

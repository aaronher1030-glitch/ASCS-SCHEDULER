import { useState, useEffect } from 'react';

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState<boolean>(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQueryList = window.matchMedia(query);
    const documentChangeHandler = () => setMatches(mediaQueryList.matches);

    // Initial check
    setMatches(mediaQueryList.matches);

    // Modern browsers
    if (mediaQueryList.addEventListener) {
      mediaQueryList.addEventListener('change', documentChangeHandler);
      return () => mediaQueryList.removeEventListener('change', documentChangeHandler);
    } 
    // Fallback for older browsers
    else if (mediaQueryList.addListener) {
      mediaQueryList.addListener(documentChangeHandler);
      return () => mediaQueryList.removeListener(documentChangeHandler);
    }
  }, [query]);

  return matches;
}

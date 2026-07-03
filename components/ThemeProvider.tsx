import React, { createContext, useContext, useEffect, useMemo } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { useMediaQuery } from '../hooks/useMediaQuery';
import designTokens from '../design_tokens.json';

type Theme = 'light' | 'dark' | 'system';
type ResolvedTheme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useLocalStorage<Theme>('scas_theme', 'system');
  const systemPrefersDark = useMediaQuery('(prefers-color-scheme: dark)');

  const resolvedTheme: ResolvedTheme = useMemo(() => {
    if (theme === 'system') {
      return systemPrefersDark ? 'dark' : 'light';
    }
    return theme;
  }, [theme, systemPrefersDark]);

  useEffect(() => {
    const root = document.documentElement;
    const tokens = designTokens.themes[resolvedTheme] as Record<string, string>;
    
    // Set color tokens as CSS variables
    Object.entries(tokens).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value);
    });

    // Set typography tokens
    Object.entries(designTokens.typography).forEach(([key, value]) => {
      root.style.setProperty(`--font-${key}`, value);
    });

    // Set radius, spacing, transitions, shadows
    Object.entries(designTokens.radius).forEach(([key, value]) => {
      root.style.setProperty(`--radius-${key}`, value);
    });
    Object.entries(designTokens.spacing).forEach(([key, value]) => {
      root.style.setProperty(`--spacing-${key}`, value);
    });
    Object.entries(designTokens.transitions).forEach(([key, value]) => {
      root.style.setProperty(`--transition-${key}`, value);
    });
    Object.entries(designTokens.shadows).forEach(([key, value]) => {
      root.style.setProperty(`--shadow-${key}`, value);
    });

    // Also toggle a class on the body for easy Tailwind/global dark mode selection if needed
    if (resolvedTheme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }

  }, [resolvedTheme]);

  const toggleTheme = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
  };

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

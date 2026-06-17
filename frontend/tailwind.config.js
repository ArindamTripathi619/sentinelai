/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
        body: ['"DM Sans"', 'system-ui', 'sans-serif'],
        heading: ['Syne', 'system-ui', 'sans-serif'],
        headline: ['"Public Sans"', 'system-ui', 'sans-serif'],
        label: ['"DM Sans"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        cyber: {
          black: '#0a0a0f',
          dark: '#0f0f1a',
          deeper: '#07070d',
          surface: '#14142a',
          card: '#1a1a2e',
          border: '#2a2a4a',
          cyan: '#00f0ff',
          magenta: '#ff00e4',
          amber: '#ffbf00',
          red: '#ff3355',
          green: '#00ff87',
        },
        primary: '#00f0ff',
        accent: '#ff00e4',
        warning: '#ffbf00',
        critical: '#ff3355',
        safe: '#00ff87',
        surface: '#0a0a0f',
        panel: 'rgba(10, 10, 15, 0.8)',
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'scan-line': 'scanLine 4s linear infinite',
        'data-stream': 'dataStream 8s linear infinite',
        'float': 'float 6s ease-in-out infinite',
        'scanline': 'scanline 8s linear infinite',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { opacity: '0.4', transform: 'scale(1)' },
          '50%': { opacity: '0.8', transform: 'scale(1.05)' },
        },
        scanLine: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        dataStream: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
      },
      backgroundImage: {
        'cyber-grid': 'linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px)',
        'cyber-gradient': 'linear-gradient(135deg, rgba(0, 240, 255, 0.15), rgba(255, 0, 228, 0.1))',
        'glass': 'linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01))',
      },
      boxShadow: {
        'neon-cyan': '0 0 15px rgba(0, 240, 255, 0.3), 0 0 45px rgba(0, 240, 255, 0.1)',
        'neon-magenta': '0 0 15px rgba(255, 0, 228, 0.3), 0 0 45px rgba(255, 0, 228, 0.1)',
        'glass': '0 8px 32px rgba(0, 0, 0, 0.4)',
      },
    },
  },
  plugins: [],
}

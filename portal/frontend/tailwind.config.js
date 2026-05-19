/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        base: '#F5F7FA',
        surface: '#FFFFFF',
        elevated: '#FAFBFC',
        hover: '#F2F3F5',
        active: '#E5E8ED',
        accent: { DEFAULT: '#2B5AED', hover: '#3A69F5', muted: 'rgba(43,90,237,0.08)' },
        border: { subtle: '#F2F3F5', DEFAULT: '#E5E8ED', strong: '#C9CDD4' },
        txt: { primary: '#1D2129', secondary: '#4E5969', tertiary: '#86909C', disabled: '#C9CDD4' },
        success: { DEFAULT: '#00B42A', muted: 'rgba(0,180,42,0.08)' },
        warning: { DEFAULT: '#FF7D00', muted: 'rgba(255,125,0,0.08)' },
        danger: { DEFAULT: '#F53F3F', muted: 'rgba(245,63,63,0.08)' },
        info: { DEFAULT: '#2B5AED', muted: 'rgba(43,90,237,0.08)' },
        teal: { DEFAULT: '#00C9A7', muted: 'rgba(0,201,167,0.08)' },
      },
      fontFamily: {
        sans: ['Inter', 'PingFang SC', 'Microsoft YaHei', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'SF Mono', 'Consolas', 'monospace'],
        display: ['DM Sans', 'Inter', 'sans-serif'],
      },
      borderRadius: { sm: '6px', md: '10px', lg: '16px' },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.08)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(8px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
      },
    },
  },
  plugins: [],
}

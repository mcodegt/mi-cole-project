/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'var(--mc-primary)',
          hover: 'var(--mc-primary-hover)',
        },
        sidebar: {
          platform: 'var(--mc-sidebar-bg)',
          staff: 'var(--mc-sidebar-bg-staff)',
        },
      },
    },
  },
  plugins: [],
};

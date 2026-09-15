tailwind.config = {
    darkMode: 'class',

    theme: {
        extend: {
            colors: {
                brand: {
                    red: '#D61A22',
                    redDark: '#B8141B',
                    white: '#F9FBFD',
                    black: '#171A1D',
                    green: '#66764A',
                    greenBright: '#6D8A4E'
                },

                light: {
                    bg: '#F4F6F8',
                    surface: '#FFFFFF',
                    raised: '#FFFFFF',
                    hover: '#EEF1F4',
                    border: '#E5E9EE'
                },

                dark: {
                    bg: '#0D1014',
                    surface: '#13171C',
                    raised: '#191E24',
                    hover: '#20262D',
                    border: '#282F37'
                }
            },

            fontFamily: {
                sans: [
                    'Inter',
                    'system-ui',
                    '-apple-system',
                    'BlinkMacSystemFont',
                    'Segoe UI',
                    'sans-serif'
                ]
            },

            boxShadow: {
                soft: '0 8px 30px rgba(17, 24, 39, 0.05)',

                card:
                    '0 8px 30px rgba(15, 23, 42, 0.055)',

                'card-hover':
                    '0 16px 45px rgba(15, 23, 42, 0.09)',

                'dark-card':
                    '0 14px 35px rgba(0, 0, 0, 0.22)',

                'glow-red':
                    '0 10px 30px rgba(214, 26, 34, 0.20)',

                'glow-green':
                    '0 10px 30px rgba(102, 118, 74, 0.20)'
            },

            borderRadius: {
                '4xl': '2rem'
            },

            transitionTimingFunction: {
                smooth: 'cubic-bezier(.2,.8,.2,1)'
            }
        }
    }
};
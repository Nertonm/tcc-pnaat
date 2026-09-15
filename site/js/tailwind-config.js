// js/tailwind-config.js
tailwind.config = {
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                brand: {
                    red: '#D61A22',
                    white: '#F9FBFD',
                    black: '#1E2022',
                    green: '#5D6B42'
                },
                dark: {
                    bg: '#0F1115',      // Fundo super escuro (moderno)
                    card: '#181A1F',    // Cards um pouco mais claros
                    border: '#272A30'   // Bordas sutis
                },
                light: {
                    bg: '#F3F5F8',      // Fundo cinza bem claro/azulado
                    card: '#FFFFFF',
                    border: '#E2E8F0'
                }
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
            boxShadow: {
                'soft': '0 4px 20px -2px rgba(0, 0, 0, 0.05)',
                'glow-red': '0 0 15px rgba(214, 26, 34, 0.3)',
                'glow-green': '0 0 15px rgba(93, 107, 66, 0.3)',
            },
            borderRadius: {
                'xl': '1rem',
                '2xl': '1.5rem',
                '3xl': '2rem',
            }
        }
    }
};

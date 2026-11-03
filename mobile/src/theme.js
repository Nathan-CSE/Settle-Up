import { useColorScheme } from 'react-native';

const palettes = {
  light: {
    background: '#FFFFFF',
    surface: '#F2F2F7',
    text: '#111111',
    subtleText: '#666666',
    border: '#DDDDDD',
    primary: '#0A84FF',
    danger: '#D70015',
  },
  dark: {
    background: '#000000',
    surface: '#1C1C1E',
    text: '#FFFFFF',
    subtleText: '#AAAAAA',
    border: '#3A3A3C',
    primary: '#0A84FF',
    danger: '#FF453A',
  },
};

export function useTheme() {
  const scheme = useColorScheme();
  return palettes[scheme === 'dark' ? 'dark' : 'light'];
}

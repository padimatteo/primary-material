import { createTheme } from '@mui/material/styles'

export const theme = createTheme({
  cssVariables: true,
  palette: {
    mode: 'light',
    primary: { main: '#284e3b', light: '#dce5d8', contrastText: '#ffffff' },
    secondary: { main: '#a65d42' },
    background: { default: '#f5f1e8', paper: '#fffdfa' },
    text: { primary: '#203027', secondary: '#6e756f', disabled: '#9c9c91' },
    divider: '#dcd7cb',
  },
  typography: {
    fontFamily: "'DM Sans', system-ui, sans-serif",
    h1: { fontFamily: "'Newsreader', Georgia, serif", fontWeight: 600 },
    h2: { fontFamily: "'Newsreader', Georgia, serif", fontWeight: 600 },
    h3: { fontFamily: "'Newsreader', Georgia, serif", fontWeight: 600 },
    h4: { fontFamily: "'Newsreader', Georgia, serif", fontWeight: 600 },
    h5: { fontFamily: "'Newsreader', Georgia, serif", fontWeight: 600 },
    h6: { fontFamily: "'Newsreader', Georgia, serif", fontWeight: 600 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  shape: { borderRadius: 10 },
  components: {
    MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } },
    MuiButton: { defaultProps: { disableElevation: true } },
    MuiTextField: { defaultProps: { variant: 'outlined', size: 'small' } },
  },
})

import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'
import { Alert, Box, Button, CircularProgress, Paper, Snackbar, Stack, Typography } from '@mui/material'
import { listRecipes } from './api'
import type { Recipe } from './api'

const recipeNames: Record<Recipe['recipe_type'], string> = {
  espresso: 'Espresso', pour_over: 'Pour over', drip: 'Drip', french_press: 'French press',
}

function dateLabel(date: string): string {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(`${date}T12:00:00`))
}

export default function CoffeeList() {
  const location = useLocation()
  const navigate = useNavigate()
  const [showSaved, setShowSaved] = useState(Boolean((location.state as { saved?: boolean } | null)?.saved))
  const [items, setItems] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    if (showSaved) navigate('/coffee', { replace: true, state: null })
  }, [showSaved, navigate])

  useEffect(() => {
    const controller = new AbortController()
    listRecipes(controller.signal)
      .then((data) => { setItems(data.items); setError(false) })
      .catch(() => { if (!controller.signal.aborted) setError(true) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [retry])

  return (
    <Box component="main" className="coffee-content">
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 3, justifyContent: 'space-between', alignItems: { sm: 'center' } }}>
        <Box>
          <Typography component="h1" variant="h3" sx={{ fontSize: { xs: '2.6rem', sm: '3.25rem' } }}>Coffee</Typography>
          <Typography color="text.secondary">Recent recipes</Typography>
        </Box>
        <Button component={Link} to="/coffee/new" variant="contained">New Recipe</Button>
      </Stack>
      {loading ? <Box sx={{ py: 8, textAlign: 'center' }}><CircularProgress aria-label="Loading recipes" /></Box> :
        error ? <Alert severity="error" action={<Button color="inherit" size="small" onClick={() => { setLoading(true); setRetry((value) => value + 1) }}>Retry</Button>}>Could not load recipes.</Alert> :
        items.length === 0 ? (
          <Paper variant="outlined" sx={{ p: 5, textAlign: 'center' }}>
            <Typography component="h2" variant="h5" sx={{ mb: 1 }}>No recipes yet</Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>Save your first brew to see it here.</Typography>
            <Button component={Link} to="/coffee/new" variant="outlined">New Recipe</Button>
          </Paper>
        ) : (
          <Stack spacing={1.5} component="section" aria-label="Recent recipes">
            {items.map((entry) => (
              <Paper key={entry.id} variant="outlined" component="article" sx={{ p: 2.5, boxShadow: 'none' }}>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ justifyContent: 'space-between' }}>
                  <Box>
                    <Typography component="h2" variant="h6">{entry.product}</Typography>
                    <Typography color="text.secondary">{entry.roaster} · {recipeNames[entry.recipe_type]} · {entry.grinder}</Typography>
                  </Box>
                  <Box sx={{ textAlign: { sm: 'right' }, flexShrink: 0 }}>
                    <Typography>{dateLabel(entry.date)}</Typography>
                    <Typography color="secondary.main" aria-label={`${entry.rating} out of 5 stars`}>{'★'.repeat(entry.rating)}{'☆'.repeat(5 - entry.rating)}</Typography>
                  </Box>
                </Stack>
              </Paper>
            ))}
          </Stack>
        )}
      <Snackbar open={showSaved} autoHideDuration={4000} onClose={() => setShowSaved(false)} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert severity="success" onClose={() => setShowSaved(false)}>Recipe saved.</Alert>
      </Snackbar>
    </Box>
  )
}

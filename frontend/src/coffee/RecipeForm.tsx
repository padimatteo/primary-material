import { useEffect, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { Link, useNavigate } from 'react-router'
import {
  Alert, Autocomplete, Box, Button, CircularProgress, FormControl, FormLabel,
  Paper, Rating, Stack, TextField, ToggleButton, ToggleButtonGroup, Typography,
} from '@mui/material'
import { ApiError, createRecipe, getSuggestions } from './api'
import type { RecipeInput, RecipeType, SuggestionField } from './api'

type FormState = {
  date: string
  roaster: string
  product: string
  roast_level: number | null
  recipe_type: RecipeType | ''
  coffee_weight_g: string
  brew_time: string
  total_yield_g: string
  grind_setting: string
  grinder: string
  rating: number | null
  notes: string
}

type Field = keyof FormState
type Errors = Partial<Record<Field, string>>

function localToday(): string {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function initialForm(): FormState {
  return {
    date: localToday(), roaster: '', product: '', roast_level: null, recipe_type: '',
    coffee_weight_g: '', brew_time: '', total_yield_g: '', grind_setting: '',
    grinder: '', rating: null, notes: '',
  }
}

function parseAmount(value: string, positive: boolean): number | null {
  if (!/^-?\d{1,6}(?:\.\d{1,2})?$/.test(value.trim())) return null
  const number = Number(value)
  return Number.isFinite(number) && (!positive || number > 0) ? number : null
}

function validateRecipe(form: FormState): { errors: Errors; payload?: RecipeInput } {
  const errors: Errors = {}
  const date = form.date.trim()
  const parsedDate = new Date(`${date}T00:00:00`)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || Number.isNaN(parsedDate.getTime()) ||
      `${parsedDate.getFullYear()}-${String(parsedDate.getMonth() + 1).padStart(2, '0')}-${String(parsedDate.getDate()).padStart(2, '0')}` !== date) {
    errors.date = 'Enter a valid date.'
  }
  for (const field of ['roaster', 'product', 'grinder'] as const) {
    const name = form[field].trim()
    if (!name) errors[field] = 'Required.'
    else if (name.length > 255) errors[field] = 'Use 255 characters or fewer.'
  }
  if (!Number.isInteger(form.roast_level) || form.roast_level! < 1 || form.roast_level! > 5) errors.roast_level = 'Choose a roast level.'
  if (!form.recipe_type) errors.recipe_type = 'Choose a recipe type.'
  if (!Number.isInteger(form.rating) || form.rating! < 1 || form.rating! > 5) errors.rating = 'Choose a rating.'

  const weight = parseAmount(form.coffee_weight_g, true)
  const yieldAmount = parseAmount(form.total_yield_g, true)
  const grind = parseAmount(form.grind_setting, false)
  if (weight === null) errors.coffee_weight_g = 'Enter a positive value with up to 2 decimals.'
  if (yieldAmount === null) errors.total_yield_g = 'Enter a positive value with up to 2 decimals.'
  if (grind === null) errors.grind_setting = 'Enter a value with up to 2 decimals.'

  const time = /^(\d+):([0-5]\d)$/.exec(form.brew_time.trim())
  const seconds = time ? Number(time[1]) * 60 + Number(time[2]) : 0
  if (!time || seconds < 1 || seconds > 2147483647) errors.brew_time = 'Use m:ss, with seconds from 00 to 59.'
  if (form.notes.length > 10000) errors.notes = 'Use 10,000 characters or fewer.'

  if (Object.keys(errors).length) return { errors }
  return {
    errors,
    payload: {
      date,
      roaster: form.roaster.trim(),
      product: form.product.trim(),
      roast_level: form.roast_level!,
      recipe_type: form.recipe_type as RecipeType,
      coffee_weight_g: weight!,
      brew_time_seconds: seconds,
      total_yield_g: yieldAmount!,
      grind_setting: grind!,
      grinder: form.grinder.trim(),
      rating: form.rating!,
      notes: form.notes || null,
    },
  }
}

function useSuggestions(field: SuggestionField, query: string, roaster: string): string[] {
  const [options, setOptions] = useState<string[]>([])
  useEffect(() => {
    if (field === 'product' && !roaster.trim()) return
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      getSuggestions(field, query, roaster, controller.signal)
        .then(setOptions)
        .catch(() => { if (!controller.signal.aborted) setOptions([]) })
    }, 250)
    return () => { window.clearTimeout(timer); controller.abort() }
  }, [field, query, roaster])
  return field === 'product' && !roaster.trim() ? [] : options
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Paper variant="outlined" sx={{ overflow: 'hidden', borderColor: 'divider', boxShadow: 'none' }}>
      <Box sx={{ bgcolor: 'primary.light', px: 2.5, py: 1.1 }}>
        <Typography component="h2" variant="h5">{title}</Typography>
      </Box>
      <Box sx={{ p: { xs: 2, sm: 2.5 } }}>{children}</Box>
    </Paper>
  )
}

export default function RecipeForm() {
  const navigate = useNavigate()
  const [form, setForm] = useState<FormState>(initialForm)
  const [errors, setErrors] = useState<Errors>({})
  const [submitError, setSubmitError] = useState('')
  const [saving, setSaving] = useState(false)
  const roasters = useSuggestions('roaster', form.roaster, '')
  const products = useSuggestions('product', form.product, form.roaster)
  const grinders = useSuggestions('grinder', form.grinder, '')

  function change<K extends Field>(field: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [field]: value, ...(field === 'roaster' && current.roaster !== value ? { product: '' } : {}) }))
    setErrors((current) => ({ ...current, [field]: undefined, ...(field === 'roaster' ? { product: undefined } : {}) }))
  }

  function lookup(field: 'roaster' | 'product' | 'grinder', options: string[]) {
    return (
      <Autocomplete
        freeSolo
        selectOnFocus
        handleHomeEndKeys
        filterOptions={(values) => values}
        options={options}
        value={form[field] || null}
        inputValue={form[field]}
        onInputChange={(_, value) => change(field, value)}
        onChange={(_, value) => change(field, value ?? '')}
        renderInput={(params) => (
          <TextField {...params} label={field[0].toUpperCase() + field.slice(1)} required
            error={Boolean(errors[field])} helperText={errors[field]} />
        )}
      />
    )
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving) return
    const result = validateRecipe(form)
    setErrors(result.errors)
    setSubmitError('')
    if (!result.payload) return
    setSaving(true)
    try {
      await createRecipe(result.payload)
      navigate('/coffee', { state: { saved: true } })
    } catch (error) {
      if (error instanceof ApiError && error.status === 422 && Array.isArray(error.detail)) {
        const serverErrors: Errors = {}
        for (const item of error.detail) {
          const field = item?.loc?.[1] === 'brew_time_seconds' ? 'brew_time' : item?.loc?.[1]
          if (field && field in form) serverErrors[field as Field] = String(item.msg)
        }
        setErrors((current) => ({ ...current, ...serverErrors }))
      }
      setSubmitError(error instanceof Error ? error.message : 'Could not save the recipe. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const amountInput = { inputMode: 'decimal' as const }
  const fieldGrid = { display: 'grid', gap: 2.5, gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))', md: 'repeat(3, minmax(0, 1fr))' } }

  return (
    <Box className="coffee-content" component="main">
      <Typography variant="body2" className="coffee-breadcrumb" sx={{ mb: 1.5 }}>
        <Link to="/coffee">Coffee</Link> &nbsp;/&nbsp; New Recipe
      </Typography>
      <Typography component="h1" variant="h3" sx={{ mb: 2.5, fontSize: { xs: '2.6rem', sm: '3.25rem' } }}>New Recipe</Typography>
      <Box component="form" noValidate onSubmit={submit}>
        <Stack spacing={1.5}>
          <Section title="Coffee">
            <Box sx={{ display: 'grid', gap: 2.5, gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))', lg: 'repeat(4, minmax(0, 1fr))' }, alignItems: 'start' }}>
              <TextField label="Date" type="date" required value={form.date}
                onChange={(event) => change('date', event.target.value)}
                error={Boolean(errors.date)} helperText={errors.date}
                slotProps={{ inputLabel: { shrink: true } }} />
              {lookup('roaster', roasters)}
              {lookup('product', products)}
              <FormControl error={Boolean(errors.roast_level)}>
                <FormLabel id="roast-label" required>Roast level</FormLabel>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', color: 'text.secondary', fontSize: '.75rem', mb: .4 }}>
                  <span>Lighter</span><span aria-hidden="true">⟵────⟶</span><span>Darker</span>
                </Box>
                <ToggleButtonGroup exclusive size="small" color="primary" fullWidth
                  aria-labelledby="roast-label" value={form.roast_level}
                  onChange={(_, value: number | null) => { if (value !== null) change('roast_level', value) }}>
                  {[1, 2, 3, 4, 5].map((level) => <ToggleButton key={level} value={level} aria-label={`Roast level ${level}`}>{level}</ToggleButton>)}
                </ToggleButtonGroup>
                {errors.roast_level && <Typography variant="caption" color="error">{errors.roast_level}</Typography>}
              </FormControl>
            </Box>
          </Section>
          <Section title="Recipe">
            <FormControl error={Boolean(errors.recipe_type)} sx={{ mb: 2.5, width: '100%' }}>
              <FormLabel id="recipe-type-label" required sx={{ mb: 1 }}>Recipe type</FormLabel>
              <ToggleButtonGroup exclusive size="small" color="primary" aria-labelledby="recipe-type-label"
                value={form.recipe_type} onChange={(_, value: RecipeType | null) => { if (value !== null) change('recipe_type', value) }}
                sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, '& .MuiToggleButtonGroup-grouped': { borderRadius: '24px !important', border: '1px solid' } }}>
                <ToggleButton value="espresso">Espresso</ToggleButton>
                <ToggleButton value="pour_over">Pour over</ToggleButton>
                <ToggleButton value="drip">Drip</ToggleButton>
                <ToggleButton value="french_press">French press</ToggleButton>
              </ToggleButtonGroup>
              {errors.recipe_type && <Typography variant="caption" color="error">{errors.recipe_type}</Typography>}
            </FormControl>
            <Box sx={fieldGrid}>
              <TextField label="Coffee weight" required value={form.coffee_weight_g} onChange={(event) => change('coffee_weight_g', event.target.value)}
                error={Boolean(errors.coffee_weight_g)} helperText={errors.coffee_weight_g} slotProps={{ htmlInput: amountInput, input: { endAdornment: <Typography variant="body2" color="text.secondary">g</Typography> } }} />
              <TextField label="Brew time" required placeholder="m:ss" value={form.brew_time} onChange={(event) => change('brew_time', event.target.value)}
                error={Boolean(errors.brew_time)} helperText={errors.brew_time} slotProps={{ input: { endAdornment: <Typography variant="body2" color="text.secondary">m:ss</Typography> } }} />
              <TextField label="Total yield" required value={form.total_yield_g} onChange={(event) => change('total_yield_g', event.target.value)}
                error={Boolean(errors.total_yield_g)} helperText={errors.total_yield_g} slotProps={{ htmlInput: amountInput, input: { endAdornment: <Typography variant="body2" color="text.secondary">g</Typography> } }} />
              <TextField label="Grind setting" required value={form.grind_setting} onChange={(event) => change('grind_setting', event.target.value)}
                error={Boolean(errors.grind_setting)} helperText={errors.grind_setting} slotProps={{ htmlInput: amountInput }} />
              {lookup('grinder', grinders)}
            </Box>
          </Section>
          <Section title="Tasting">
            <Box sx={{ display: 'grid', gap: 2.5, gridTemplateColumns: { xs: '1fr', sm: '1fr 2fr' } }}>
              <FormControl error={Boolean(errors.rating)}>
                <FormLabel id="rating-label" required>Rating</FormLabel>
                <Rating name="recipe-rating" value={form.rating} max={5} size="large"
                  onChange={(_, value) => { if (value === null || Number.isInteger(value)) change('rating', value) }} aria-labelledby="rating-label"
                  sx={{ color: 'secondary.main', mt: 1 }} />
                {errors.rating && <Typography variant="caption" color="error">{errors.rating}</Typography>}
              </FormControl>
              <TextField label="Notes" multiline minRows={3} value={form.notes} onChange={(event) => change('notes', event.target.value)}
                error={Boolean(errors.notes)} helperText={errors.notes} />
            </Box>
          </Section>
          {submitError && <Alert severity="error" role="alert">{submitError}</Alert>}
          <Stack direction="row" spacing={1.5} sx={{ pt: 1, justifyContent: 'flex-end' }}>
            <Button component={Link} to="/coffee" color="primary">Cancel</Button>
            <Button type="submit" variant="contained" disabled={saving} startIcon={saving ? <CircularProgress size={16} color="inherit" /> : undefined}>Save entry</Button>
          </Stack>
        </Stack>
      </Box>
    </Box>
  )
}

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router'
import { ThemeProvider } from '@mui/material'
import { theme } from '../theme'
import RecipeForm from './RecipeForm'
import CoffeeList from './CoffeeList'

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

function renderRoutes(start = '/coffee/new') {
  return render(
    <ThemeProvider theme={theme}>
      <MemoryRouter initialEntries={[start]}>
        <Routes>
          <Route path="/coffee/new" element={<RecipeForm />} />
          <Route path="/coffee" element={<CoffeeList />} />
        </Routes>
      </MemoryRouter>
    </ThemeProvider>,
  )
}

async function fillValidForm(user: ReturnType<typeof userEvent.setup>) {
  fireEvent.change(screen.getByLabelText(/Roaster/i), { target: { value: 'New Roaster' } })
  fireEvent.change(screen.getByLabelText(/Product/i), { target: { value: 'House Blend' } })
  fireEvent.change(screen.getByLabelText(/Grinder/i), { target: { value: 'Hand Grinder' } })
  fireEvent.change(screen.getByLabelText(/Coffee weight/i), { target: { value: '18' } })
  fireEvent.change(screen.getByLabelText(/Brew time/i), { target: { value: '2:30' } })
  fireEvent.change(screen.getByLabelText(/Total yield/i), { target: { value: '300' } })
  fireEvent.change(screen.getByLabelText(/Grind setting/i), { target: { value: '18.5' } })
  await user.click(screen.getByRole('button', { name: 'Roast level 3' }))
  await user.click(screen.getByRole('button', { name: 'Pour over' }))
  fireEvent.click(screen.getByRole('radio', { name: '4 Stars' }))
}

describe('coffee pages', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(json({ values: [] }))))
  })
  afterEach(() => { cleanup(); vi.unstubAllGlobals() })

  it('requires the recipe fields before sending a request', async () => {
    const user = userEvent.setup()
    renderRoutes()
    await user.click(screen.getByRole('button', { name: 'Save entry' }))
    expect(screen.getByText('Choose a roast level.')).toBeInTheDocument()
    expect(screen.getByText('Choose a recipe type.')).toBeInTheDocument()
    expect(screen.getByText('Choose a rating.')).toBeInTheDocument()
    expect((fetch as ReturnType<typeof vi.fn>).mock.calls.some(([url, options]) =>
      url === '/api/coffee/recipes' && options?.method === 'POST')).toBe(false)
  })

  it('saves a free-text recipe with time converted to seconds and navigates to recent recipes', async () => {
    const user = userEvent.setup()
    const calls: { url: string; body?: Record<string, unknown> }[] = []
    vi.stubGlobal('fetch', vi.fn((url: string, options?: RequestInit) => {
      if (options?.method === 'POST') {
        const body = JSON.parse(options.body as string)
        calls.push({ url, body })
        return Promise.resolve(json({ ...body, id: '1', created_at: '', updated_at: '' }, 201))
      }
      if (url.startsWith('/api/coffee/recipes?')) return Promise.resolve(json({ items: [], total: 0, limit: 20, offset: 0 }))
      return Promise.resolve(json({ values: [] }))
    }))
    renderRoutes()

    await fillValidForm(user)
    await user.click(screen.getByRole('button', { name: 'Save entry' }))

    await waitFor(() => expect(calls).toHaveLength(1))
    expect(calls[0].body).toMatchObject({
      roaster: 'New Roaster', product: 'House Blend', grinder: 'Hand Grinder',
      roast_level: 3, recipe_type: 'pour_over', brew_time_seconds: 150, rating: 4,
    })
    expect(await screen.findByText('No recipes yet')).toBeInTheDocument()
  })

  it('scopes product suggestions to the entered roaster', async () => {
    const urls: string[] = []
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      urls.push(url)
      return Promise.resolve(json({ values: ['House Blend'] }))
    }))
    renderRoutes()
    fireEvent.change(screen.getByLabelText(/Roaster/i), { target: { value: 'North Roaster' } })
    fireEvent.change(screen.getByLabelText(/Product/i), { target: { value: 'H' } })
    await waitFor(() => expect(urls.some((url) => {
      const params = new URL(url, 'http://localhost').searchParams
      return params.get('field') === 'product' && params.get('roaster') === 'North Roaster' && params.get('q') === 'H'
    })).toBe(true))
  })

  it('preserves entered fields when saving fails', async () => {
    const user = userEvent.setup()
    vi.stubGlobal('fetch', vi.fn((_: string, options?: RequestInit) =>
      Promise.resolve(options?.method === 'POST' ? json({ detail: 'Server unavailable' }, 500) : json({ values: [] }))))
    renderRoutes()
    await fillValidForm(user)
    await user.click(screen.getByRole('button', { name: 'Save entry' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not save the recipe')
    expect(screen.getByLabelText(/Roaster/i)).toHaveValue('New Roaster')
    expect(screen.getByLabelText(/Brew time/i)).toHaveValue('2:30')
  })

  it('shows recent recipes', async () => {
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce(json({ items: [{ id: '1', date: '2026-09-24', product: 'House Blend', roaster: 'Example Roaster', grinder: 'Example Grinder', recipe_type: 'pour_over', rating: 4 }], total: 1, limit: 20, offset: 0 })))
    renderRoutes('/coffee')
    expect(await screen.findByText('House Blend')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'New Recipe' })).toHaveAttribute('href', '/coffee/new')
  })

  it('shows the recent-recipes error and offers retry', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    renderRoutes('/coffee')
    expect(await screen.findByText('Could not load recipes.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
  })
})

import { useColorMode } from '@vueuse/core'

// Single source of truth for the theme. The same storage key is read by the
// inline bootstrap script in index.html, which paints the class before Vue
// mounts so the first frame is never the wrong colour.
export const THEME_STORAGE_KEY = 'saiddit-theme'

export function useTheme() {
  const mode = useColorMode({
    storageKey: THEME_STORAGE_KEY,
    initialValue: 'dark',
    // No 'auto': the toggle is an explicit two-way switch.
    modes: { light: 'light', dark: 'dark' },
  })

  function toggle() {
    mode.value = mode.value === 'dark' ? 'light' : 'dark'
  }

  return { mode, toggle }
}

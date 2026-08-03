import { defineStore } from 'pinia'

const THEME_KEY = 'kf_theme'

function applyTheme(isDark: boolean) {
  const root = document.documentElement
  if (isDark) root.setAttribute('data-theme', 'dark')
  else root.removeAttribute('data-theme')
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    isDark: localStorage.getItem(THEME_KEY) === 'dark',
  }),
  actions: {
    init() {
      applyTheme(this.isDark)
    },
    toggle() {
      this.isDark = !this.isDark
      localStorage.setItem(THEME_KEY, this.isDark ? 'dark' : 'light')
      applyTheme(this.isDark)
    },
  },
})

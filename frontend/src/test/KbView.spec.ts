import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import KbView from '../views/KbView.vue'

describe('KbView', () => {
  it('should render', () => {
    const wrapper = mount(KbView, {
      global: {
        plugins: [createPinia()]
      }
    })
    expect(wrapper.exists()).toBe(true)
  })
})

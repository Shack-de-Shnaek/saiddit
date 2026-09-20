<script setup>
import { computed } from 'vue'
import { Moon, Sun } from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { useTheme } from '@/composables/useTheme'

const { mode, toggle } = useTheme()

const isDark = computed(() => mode.value === 'dark')
const label = computed(() => (isDark.value ? 'Switch to light mode' : 'Switch to dark mode'))
</script>

<template>
  <Button
    variant="ghost"
    size="icon-sm"
    class="rounded-full"
    :title="label"
    :aria-label="label"
    @click="toggle"
  >
    <Sun v-if="isDark" />
    <Moon v-else />
  </Button>
</template>

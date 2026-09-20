<script setup>
import { Card } from '@/components/ui/card'
import ThemeToggle from '@/components/layout/ThemeToggle.vue'
</script>

<template>
  <div class="relative flex min-h-svh items-center justify-center bg-muted p-4">
    <!-- No header on this layout, so the toggle sits in the corner. -->
    <div class="absolute right-4 top-4">
      <ThemeToggle />
    </div>

    <Card class="w-full max-w-md shadow-lg">
      <RouterView />
    </Card>
  </div>
</template>

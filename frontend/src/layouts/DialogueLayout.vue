<script setup>
import { Card } from '@/components/ui/card'
</script>

<template>
  <div class="flex min-h-svh items-center justify-center bg-muted p-4">
    <Card class="w-full max-w-md shadow-lg">
      <RouterView />
    </Card>
  </div>
</template>

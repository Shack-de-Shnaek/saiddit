<script setup>
import { ref } from 'vue';
import { House, Plus, TrendingUp, Users } from '@lucide/vue';
import { useUserStore } from '@/stores/user';
import { Button } from '@/components/ui/button';

const userStore = useUserStore();

const links = [
    { label: 'Home', icon: House, to: { name: 'home' } },
];

</script>

<template>
    <aside class="sticky top-14 h-[calc(100svh-3.5rem)] w-60 shrink-0 border-r bg-sidebar p-3 text-sidebar-foreground">
        <nav class="flex flex-col gap-1">
            <RouterLink v-for="link in links" :key="link.label" :to="link.to"
                class="flex items-center gap-3 rounded-md px-3 py-2 text-sm hover:bg-sidebar-accent hover:text-sidebar-accent-foreground">
                <component :is="link.icon" class="size-4" />
                {{ link.label }}
            </RouterLink>
            <div>
                <div>
                    <span
                        class="flex items-center gap-3 rounded-md px-3 py-2 text-sm hover:bg-sidebar-accent hover:text-sidebar-accent-foreground">
                        <Users class="size-4" />
                        <span>Spaces ({{ userStore?.spaces?.length }})</span>
                    </span>
                </div>
                <div v-for="space in userStore?.spaces" :key="space.id">
                    <RouterLink :to="{ name: 'space', params: { slug: space.slug } }"
                        class="flex items-center gap-3 rounded-md px-3 py-2 text-sm hover:bg-sidebar-accent hover:text-sidebar-accent-foreground">
                        <span>{{ space.name }}</span>
                    </RouterLink>
                </div>
                <Button v-if="userStore.isAuthenticated" as-child variant="ghost" size="sm"
                    class="mt-1 w-full justify-start gap-3 px-3 font-normal hover:bg-sidebar-accent hover:text-sidebar-accent-foreground">
                    <RouterLink :to="{ name: 'space-create' }">
                        <Plus class="size-4" />
                        Create a space
                    </RouterLink>
                </Button>
            </div>
        </nav>
    </aside>
</template>

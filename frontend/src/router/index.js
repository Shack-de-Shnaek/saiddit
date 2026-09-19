import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import DialogueLayout from '@/layouts/DialogueLayout.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        { path: '', name: 'home', component: () => import('@/views/HomeView.vue') },
        {
          path: 'spaces/create',
          name: 'space-create',
          component: () => import('@/views/CreateSpaceView.vue'),
        },
        {
          path: 'spaces/:slug',
          name: 'space',
          component: () => import('@/views/SpaceView.vue'),
          props: true,
        },
        {
          path: 'spaces/:slug/members',
          name: 'space-members',
          component: () => import('@/views/SpaceMembersView.vue'),
          props: true,
        },
        {
          path: 'spaces/:slug/posts/create',
          name: 'post-create',
          component: () => import('@/views/CreatePostView.vue'),
          props: true,
        },
        {
          path: 'posts/:id',
          name: 'post',
          component: () => import('@/views/PostView.vue'),
          // Route params are strings; the API wants the id as a number.
          props: (route) => ({ id: Number(route.params.id) }),
        },
        {
          path: 'spaces/:slug/posts/create',
          name: 'post-create',
          component: () => import('@/views/CreatePostView.vue'),
          props: true,
        },
      ],
    },
    {
      path: '/',
      component: DialogueLayout,
      children: [
        { path: 'login', name: 'login', component: () => import('@/views/LoginView.vue') },
        { path: 'register', name: 'register', component: () => import('@/views/RegisterView.vue') },
      ],
    },
  ],
})

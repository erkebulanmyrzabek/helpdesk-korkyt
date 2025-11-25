<script setup>
import { RouterView } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const logout = () => {
  authStore.logout()
}
</script>

<template>
  <div>
    <nav class="navbar navbar-expand-lg mb-4" v-if="authStore.isAuthenticated">
      <div class="container">
        <a class="navbar-brand fw-bold" href="#">
            <i class="bi bi-life-preserver me-2"></i>
            Helpdesk Коркыт Ата
        </a>
        <div class="d-flex align-items-center">
          <span class="navbar-text text-white me-3" v-if="authStore.user">
            <i class="bi bi-person-circle me-1"></i>
            {{ authStore.user.first_name || authStore.user.username }}
            <small class="opacity-75">({{ authStore.user.role }})</small>
          </span>
          <button class="btn btn-sm btn-light text-primary fw-bold" @click="logout">Выйти</button>
        </div>
      </div>
    </nav>
    <div class="container py-2">
      <RouterView />
    </div>
  </div>
</template>

<style>
/* App specific styles if needed */
</style>

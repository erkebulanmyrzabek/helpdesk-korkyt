<script setup>
import { RouterView } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'
import { ref } from 'vue'

const authStore = useAuthStore()
const router = useRouter()
const isMobileMenuOpen = ref(false)

const logout = async () => {
  await authStore.logout()
  isMobileMenuOpen.value = false
}

const toggleMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}
</script>

<template>
  <div>
    <nav class="navbar navbar-expand-lg mb-4 shadow-sm" v-if="authStore.isAuthenticated">
      <div class="container">
        <a class="navbar-brand fw-bold d-flex align-items-center text-truncate" href="#" style="max-width: 70%;">
            <i class="bi bi-mortarboard-fill me-2 fs-4"></i>
            <span class="text-truncate">Helpdesk Коркыт Ата</span>
        </a>
        
        <!-- Mobile Toggle Button -->
        <button class="navbar-toggler border-0 text-white" type="button" @click="toggleMenu">
           <i class="bi" :class="isMobileMenuOpen ? 'bi-x-lg' : 'bi-list'" style="font-size: 1.5rem;"></i>
        </button>

        <!-- Desktop Menu -->
        <div class="collapse navbar-collapse justify-content-end" id="navbarNav">
          <div class="d-flex align-items-center">
            <span class="navbar-text text-white me-3" v-if="authStore.user">
              <i class="bi bi-person-circle me-1"></i>
              {{ authStore.user.first_name || authStore.user.username }}
              <small class="opacity-75">({{ authStore.user.role }})</small>
            </span>
            <button class="btn btn-sm btn-light text-primary fw-bold shadow-sm" @click="logout">Выйти</button>
          </div>
        </div>

         <!-- Mobile Menu Overlay -->
         <div v-if="isMobileMenuOpen" class="d-lg-none w-100 mt-3 border-top border-white border-opacity-25 pt-3 pb-2 animate-fade-in">
            <div class="d-flex flex-column gap-3 text-white px-2">
               <div v-if="authStore.user" class="d-flex align-items-center">
                  <div class="bg-white bg-opacity-10 rounded-circle p-2 me-3">
                      <i class="bi bi-person-circle fs-4"></i>
                  </div>
                  <div>
                      <div class="fw-bold">{{ authStore.user.first_name || authStore.user.username }}</div>
                      <small class="opacity-75">{{ authStore.user.role }}</small>
                  </div>
               </div>
               <button class="btn btn-light text-primary w-100 fw-bold py-2 mt-2" @click="logout">
                  <i class="bi bi-box-arrow-right me-2"></i>Выйти
               </button>
            </div>
         </div>
      </div>
    </nav>
    <div class="container py-2 pb-5">
      <RouterView />
    </div>
  </div>
</template>

<style>
/* Navbar mobile adjustments */
.navbar {
  padding-top: 0.8rem;
  padding-bottom: 0.8rem;
}

@media (max-width: 991.98px) {
    .navbar-collapse {
        display: none !important; /* Force hide default collapse on mobile to use custom overlay */
    }
}

.animate-fade-in {
    animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>

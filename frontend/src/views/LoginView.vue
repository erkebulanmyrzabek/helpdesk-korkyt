<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const username = ref('')
const password = ref('')
const error = ref('')
const authStore = useAuthStore()

const login = async () => {
    try {
        await authStore.login(username.value, password.value)
    } catch (e) {
        error.value = 'Неверный логин или пароль'
    }
}
</script>

<template>
    <div class="min-vh-100 d-flex align-items-center justify-content-center bg-light-pattern px-3">
        <div class="card shadow-lg border-0 w-100" style="max-width: 400px;">
            <div class="card-header bg-primary text-white text-center py-4">
                <div class="mb-2">
                    <i class="bi bi-mortarboard-fill display-4"></i>
                </div>
                <h4 class="mb-0 fw-bold">Helpdesk</h4>
                <small>Korkyt Ata University</small>
            </div>
            <div class="card-body p-4">
                <form @submit.prevent="login">
                    <div class="mb-3">
                        <label class="form-label text-muted">Логин</label>
                        <div class="input-group input-group-lg">
                            <span class="input-group-text bg-light border-end-0"><i class="bi bi-person text-muted"></i></span>
                            <input v-model="username" type="text" class="form-control bg-light border-start-0" placeholder="Введите логин" required>
                        </div>
                    </div>
                    <div class="mb-4">
                        <label class="form-label text-muted">Пароль</label>
                        <div class="input-group input-group-lg">
                            <span class="input-group-text bg-light border-end-0"><i class="bi bi-lock text-muted"></i></span>
                            <input v-model="password" type="password" class="form-control bg-light border-start-0" placeholder="Введите пароль" required>
                        </div>
                    </div>
                    <div class="text-danger mb-3 text-center bg-danger bg-opacity-10 p-2 rounded" v-if="error">
                        <i class="bi bi-exclamation-circle me-1"></i>{{ error }}
                    </div>
                    <button type="submit" class="btn btn-primary w-100 btn-lg fw-bold shadow-sm">
                        Войти <i class="bi bi-arrow-right ms-2"></i>
                    </button>
                </form>
            </div>
            <div class="card-footer text-center py-3 text-muted bg-light border-top-0">
                <small>&copy; 2025 Korkyt Ata University</small>
            </div>
        </div>
    </div>
</template>

<style scoped>
.bg-light-pattern {
    background-color: #f4f6f9;
    background-image: radial-gradient(#e2e8f0 1px, transparent 1px);
    background-size: 20px 20px;
}
.input-group-text {
    border-right: none;
}
.form-control:focus {
    border-color: #dee2e6;
    box-shadow: none;
    background-color: #fff;
}
.form-control:focus + .input-group-text, 
.input-group-text:has(+ .form-control:focus) {
    background-color: #fff;
    border-color: var(--primary-color);
}
</style>

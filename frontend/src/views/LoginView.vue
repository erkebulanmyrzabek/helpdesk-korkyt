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
    <div class="login-wrapper min-vh-100 d-flex align-items-center justify-content-center px-3">
        <div class="login-overlay"></div>
        <div class="card shadow-lg border-0 w-100 overflow-hidden main-card" style="max-width: 420px;">
            <div class="card-header bg-primary text-white text-center py-5 border-0 position-relative">
                <div class="mb-3 position-relative z-1">
                    <i class="bi bi-mortarboard-fill display-4"></i>
                </div>
                <h3 class="mb-0 fw-bold position-relative z-1">Helpdesk</h3>
                <p class="mb-0 opacity-75 position-relative z-1">Korkyt Ata University</p>
                <div class="header-shape"></div>
            </div>
            <div class="card-body p-4 p-md-5">
                <h5 class="text-center mb-4 fw-bold text-dark">Вход в систему</h5>
                <form @submit.prevent="login">
                    <div class="mb-3">
                        <label class="form-label text-muted small fw-bold">Логин</label>
                        <div class="input-group">
                            <span class="input-group-text bg-white border-end-0"><i class="bi bi-person text-primary"></i></span>
                            <input v-model="username" type="text" class="form-control border-start-0 ps-0" placeholder="Username" required>
                        </div>
                    </div>
                    <div class="mb-4">
                        <label class="form-label text-muted small fw-bold">Пароль</label>
                        <div class="input-group">
                            <span class="input-group-text bg-white border-end-0"><i class="bi bi-lock text-primary"></i></span>
                            <input v-model="password" type="password" class="form-control border-start-0 ps-0" placeholder="••••••••" required>
                        </div>
                    </div>
                    <div class="text-danger mb-3 text-center bg-danger bg-opacity-10 p-2 rounded small" v-if="error">
                        <i class="bi bi-exclamation-circle me-1"></i>{{ error }}
                    </div>
                    <button type="submit" class="btn btn-primary w-100 btn-lg fw-bold shadow-sm py-3 mb-3">
                        Войти <i class="bi bi-arrow-right ms-2"></i>
                    </button>
                    <div class="text-center">
                        <router-link to="/register" class="text-decoration-none small fw-bold">Нет аккаунта? Зарегистрироваться</router-link>
                    </div>
                </form>
            </div>
            <div class="card-footer text-center py-3 text-muted bg-white border-top-0">
                <small class="opacity-75">&copy; 2025 Korkyt Ata University</small>
            </div>
        </div>
    </div>
</template>

<style scoped>
.login-wrapper {
    background-image: url('/assets/bg.png');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    position: relative;
}

.login-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(0, 40, 85, 0.7), rgba(0, 80, 157, 0.5));
    backdrop-filter: blur(2px);
}

.main-card {
    backdrop-filter: blur(10px);
    background: rgba(255, 255, 255, 0.95);
    border-radius: 20px;
    z-index: 1;
}

.header-shape {
    position: absolute;
    bottom: -50px;
    left: -10%;
    width: 120%;
    height: 100px;
    background: rgba(255, 255, 255, 0.95);
    transform: rotate(-5deg);
}

.input-group-text {
    border-color: #e2e8f0;
    font-size: 1.2rem;
}

.form-control {
    border-color: #e2e8f0;
    padding: 0.75rem 1rem;
}

.form-control:focus {
    border-color: var(--bs-primary);
    box-shadow: none;
}

.btn-primary {
    border-radius: 12px;
    transition: all 0.3s ease;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 15px rgba(13, 110, 253, 0.2);
}
</style>

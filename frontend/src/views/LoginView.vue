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
    <div class="min-vh-100 d-flex align-items-center justify-content-center bg-light-pattern">
        <div class="card shadow-lg border-0" style="width: 100%; max-width: 400px;">
            <div class="card-header bg-primary text-white text-center py-4">
                <h4 class="mb-0 fw-bold">Helpdesk</h4>
                <small>Университет Коркыт Ата</small>
            </div>
            <div class="card-body p-4">
                <form @submit.prevent="login">
                    <div class="mb-3">
                        <label class="form-label text-muted">Логин</label>
                        <input v-model="username" type="text" class="form-control form-control-lg" placeholder="Введите ваш логин" required>
                    </div>
                    <div class="mb-4">
                        <label class="form-label text-muted">Пароль</label>
                        <input v-model="password" type="password" class="form-control form-control-lg" placeholder="Введите ваш пароль" required>
                    </div>
                    <div class="text-danger mb-3 text-center" v-if="error">{{ error }}</div>
                    <button type="submit" class="btn btn-primary w-100 btn-lg fw-bold">Войти</button>
                </form>
            </div>
            <div class="card-footer text-center py-3 text-muted bg-light">
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
</style>

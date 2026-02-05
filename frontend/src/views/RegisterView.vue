<script setup>
import { ref } from 'vue'
import axios from '../axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const form = ref({
    full_name: '',
    username: '',
    password: '',
    institute: '',
    position: ''
})

const institutes = [
    'Ректорат',
    'Институт педагогики и традиционного искусства',
    'Институт естествознания',
    'Инженерно-технологический институт',
    'Институт экономики и права',
    'Гуманитарно-педагогический институт',
    'Институт искусственного интеллекта'
]

const error = ref('')
const successMessage = ref('')
const isSubmitting = ref(false)

const register = async () => {
    error.value = ''
    successMessage.value = ''
    isSubmitting.value = true
    
    try {
        await axios.post('auth/registration-request/', form.value)
        successMessage.value = '✅ Запрос на регистрацию успешно отправлен и ожидает подтверждения администратора'
        form.value = { full_name: '', username: '', password: '', institute: '', position: '' }
        
        // Wait 5 seconds and redirect to login
        setTimeout(() => {
            router.push('/login')
        }, 5000)
    } catch (e) {
        console.error(e)
        if (e.response && e.response.data) {
            const data = e.response.data
            if (typeof data === 'object') {
                error.value = Object.values(data).flat().join(' ')
            } else {
                error.value = data
            }
        } else {
            error.value = 'Ошибка при отправке запроса. Попробуйте позже.'
        }
    } finally {
        isSubmitting.value = false
    }
}
</script>

<template>
    <div class="register-wrapper min-vh-100 d-flex align-items-center justify-content-center px-3 py-5">
        <div class="register-overlay"></div>
        <div class="card shadow-lg border-0 w-100 overflow-hidden main-card" style="max-width: 600px;">
            <div class="card-header bg-primary text-white text-center py-4 border-0 position-relative">
                <div class="mb-2 position-relative z-1">
                    <i class="bi bi-person-plus-fill display-4"></i>
                </div>
                <h4 class="mb-0 fw-bold position-relative z-1">Регистрация</h4>
                <p class="mb-0 opacity-75 position-relative z-1">Helpdesk Korkyt Ata University</p>
                <div class="header-shape"></div>
            </div>
            <div class="card-body p-4 p-md-5">
                <div v-if="successMessage" class="alert alert-success text-center mb-0 py-4 shadow-sm">
                    <div class="display-4 mb-3 text-success"><i class="bi bi-check-circle-fill"></i></div>
                    <h5 class="fw-bold">{{ successMessage }}</h5>
                    <div class="mt-3 small opacity-75">Вы будете перенаправлены на страницу логина через 5 секунд...</div>
                    <router-link to="/login" class="btn btn-success mt-4 px-4 fw-bold">Вернуться сейчас</router-link>
                </div>
                
                <form v-else @submit.prevent="register">
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label text-muted small fw-bold text-uppercase">Фамилия и имя</label>
                            <input v-model="form.full_name" type="text" class="form-control" placeholder="Айдос Қуанышұлы" required pattern="^[а-яА-ЯёЁӘәҒғҚқҢңӨөҰұҮүҺһІі\s-]+$" title="Введите Фамилию и имя на русском или казахском языке. Английские буквы запрещены.">
                        </div>

                        <div class="col-md-6 mb-3">
                            <label class="form-label text-muted small fw-bold text-uppercase">Логин (на англ.)</label>
                            <input v-model="form.username" type="text" class="form-control" placeholder="Username" required pattern="^[a-zA-Z0-9]{3,}$">
                        </div>

                        <div class="col-12 mb-3">
                            <label class="form-label text-muted small fw-bold text-uppercase">Пароль</label>
                            <input v-model="form.password" type="password" class="form-control" placeholder="Мин. 8 символов, цифры, заглавные" required minlength="8">
                            <div class="form-text x-small">Должен содержать цифры, заглавные и строчные буквы.</div>
                        </div>

                        <div class="col-12 mb-3">
                            <label class="form-label text-muted small fw-bold text-uppercase d-block mb-3">Институт / подразделение КУ</label>
                            <div class="institute-selector p-3 bg-light rounded-3 border">
                                <div v-for="inst in institutes" :key="inst" class="form-check mb-2">
                                    <input class="form-check-input" type="radio" :value="inst" :id="inst" v-model="form.institute" required>
                                    <label class="form-check-label small" :for="inst">
                                        {{ inst }}
                                    </label>
                                </div>
                            </div>
                        </div>

                        <div class="col-12 mb-4">
                            <label class="form-label text-muted small fw-bold text-uppercase">Должность</label>
                            <input v-model="form.position" type="text" class="form-control" placeholder="Старший преподаватель" required>
                        </div>
                    </div>

                    <div class="text-danger mb-4 text-center bg-danger bg-opacity-10 p-3 rounded small" v-if="error">
                        <i class="bi bi-exclamation-circle me-1"></i>{{ error }}
                    </div>

                    <button type="submit" class="btn btn-primary w-100 btn-lg fw-bold shadow-sm py-3" :disabled="isSubmitting">
                        <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2"></span>
                        Отправить запрос на регистрацию
                    </button>
                    
                    <div class="text-center mt-4">
                        <router-link to="/login" class="text-decoration-none small fw-bold">Уже есть аккаунт? Войти</router-link>
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
.register-wrapper {
    background-image: url('/assets/bg.png');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    position: relative;
}

.register-overlay {
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
    border-radius: 24px;
    z-index: 1;
}

.header-shape {
    position: absolute;
    bottom: -40px;
    left: -5%;
    width: 110%;
    height: 80px;
    background: rgba(255, 255, 255, 0.95);
    transform: rotate(-3deg);
}

.form-control {
    padding: 0.75rem 1rem;
    border-color: #e2e8f0;
    background-color: #fff;
    border-radius: 10px;
}

.form-control:focus {
    border-color: var(--bs-primary);
    box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.1);
}

.institute-selector {
    max-height: 200px;
    overflow-y: auto;
}

.x-small {
    font-size: 0.7rem;
}

.btn-primary {
    border-radius: 12px;
    transition: all 0.3s ease;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 15px rgba(13, 110, 253, 0.2);
}

.institute-selector::-webkit-scrollbar {
    width: 6px;
}
.institute-selector::-webkit-scrollbar-thumb {
    background: #cbd5e0;
    border-radius: 3px;
}
</style>

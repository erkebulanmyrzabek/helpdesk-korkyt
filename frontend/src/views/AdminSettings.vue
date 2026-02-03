<script setup>
import { ref, onMounted } from 'vue'
import axios from '../axios'

const settings = ref({
    work_start_time: '09:00',
    work_end_time: '18:00',
    allow_outside_working_hours: false
})

const isLoading = ref(false)
const saveSuccess = ref(false)

const fetchSettings = async () => {
    try {
        const response = await axios.get('settings/current/')
        settings.value = response.data
    } catch (error) {
        console.error('Failed to fetch settings:', error)
    }
}

const saveSettings = async () => {
    isLoading.value = true
    saveSuccess.value = false
    try {
        // Since it's a singleton reached by /settings/1/ usually, 
        // but we can check the ID from fetch.
        await axios.patch(`settings/${settings.value.id}/`, settings.value)
        saveSuccess.value = true
        setTimeout(() => saveSuccess.value = false, 3000)
    } catch (error) {
        console.error('Failed to save settings:', error)
        alert('Ошибка при сохранении настроек')
    } finally {
        isLoading.value = false
    }
}

onMounted(fetchSettings)
</script>

<template>
    <div class="container-fluid">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="text-primary mb-0"><i class="bi bi-gear-fill me-2"></i>Настройки системы</h2>
            <router-link to="/admin" class="btn btn-outline-secondary">
                <i class="bi bi-arrow-left me-1"></i>Назад
            </router-link>
        </div>

        <div class="row">
            <div class="col-md-3">
                <div class="list-group shadow-sm">
                    <button class="list-group-item list-group-item-action active">
                        <i class="bi bi-clock me-2"></i>Рабочее время
                    </button>
                    <!-- Future settings can be added here -->
                    <button class="list-group-item list-group-item-action disabled">
                        <i class="bi bi-envelope me-2"></i>Уведомления (скоро)
                    </button>
                </div>
            </div>
            
            <div class="col-md-9">
                <div class="card shadow-sm">
                    <div class="card-header bg-white border-bottom">
                        <h5 class="mb-0">Настройка рабочего времени</h5>
                    </div>
                    <div class="card-body">
                        <form @submit.prevent="saveSettings">
                            <div class="row mb-4">
                                <div class="col-md-6">
                                    <label class="form-label text-muted small fw-bold">Начало работы</label>
                                    <input type="time" v-model="settings.work_start_time" class="form-control form-control-lg" required>
                                    <div class="form-text">Время, с которого пользователи могут отправлять заявки.</div>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label text-muted small fw-bold">Конец работы</label>
                                    <input type="time" v-model="settings.work_end_time" class="form-control form-control-lg" required>
                                    <div class="form-text">Время, после которого отправка заявок будет ограничена.</div>
                                </div>
                            </div>

                            <div class="mb-4 p-3 bg-light rounded-3 border">
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="allowOutside" v-model="settings.allow_outside_working_hours">
                                    <label class="form-check-label fw-bold" for="allowOutside">
                                        Разрешить заявки вне рабочего времени
                                    </label>
                                </div>
                                <div class="form-text ms-4 mt-2">
                                    Если включено, пользователи смогут отправлять заявки в любое время, но будут предупреждены о нерабочем времени.
                                </div>
                            </div>

                            <div class="d-flex align-items-center gap-3">
                                <button type="submit" class="btn btn-primary px-5 py-2 fw-bold" :disabled="isLoading">
                                    <span v-if="isLoading" class="spinner-border spinner-border-sm me-2"></span>
                                    Сохранить изменения
                                </button>
                                <span v-if="saveSuccess" class="text-success animate-fade-in">
                                    <i class="bi bi-check-circle-fill me-1"></i> Сохранено успешно!
                                </span>
                            </div>
                        </form>
                    </div>
                </div>

                <!-- Guidance for Users Card -->
                <div class="card mt-4 border-info bg-info bg-opacity-10">
                    <div class="card-body">
                        <h6 class="text-info fw-bold mb-2"><i class="bi bi-info-circle me-2"></i>Как это работает?</h6>
                        <ul class="mb-0 small text-secondary">
                            <li>Система автоматически блокирует кнопку «Отправить заявку» за пределами указанного интервала.</li>
                            <li>Все временные зоны учитываются по локальному времени (Asia/Almaty).</li>
                            <li>Изменения вступают в силу мгновенно для всех пользователей.</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.form-check-input {
    cursor: pointer;
    width: 3em;
    height: 1.5em;
}
.form-check-label {
    cursor: pointer;
    padding-left: 0.5em;
    padding-top: 0.2em;
}
.animate-fade-in {
    animation: fadeIn 0.3s ease-out;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateX(-10px); }
    to { opacity: 1; transform: translateX(0); }
}
</style>

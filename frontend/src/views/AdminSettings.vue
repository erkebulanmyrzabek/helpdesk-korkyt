<script setup>
import { ref, onMounted } from 'vue'
import axios from '../axios'

// Tabs
const currentTab = ref('worktime') // 'worktime' or 'buildings'

// System Settings
const settings = ref({
    work_start_time: '09:00',
    work_end_time: '18:00',
    allow_outside_working_hours: false
})
const isLoadingSettings = ref(false)
const saveSuccess = ref(false)

// Buildings (Corpuses)
const corpuses = ref([])
const isLoadingCorpuses = ref(false)
const showCorpusModal = ref(false)
const editingCorpus = ref({ id: null, name: '' })

const fetchSettings = async () => {
    try {
        const response = await axios.get('settings/current/')
        settings.value = response.data
    } catch (error) {
        console.error('Failed to fetch settings:', error)
    }
}

const saveSettings = async () => {
    isLoadingSettings.value = true
    saveSuccess.value = false
    try {
        await axios.patch(`settings/${settings.value.id}/`, settings.value)
        saveSuccess.value = true
        setTimeout(() => saveSuccess.value = false, 3000)
    } catch (error) {
        console.error('Failed to save settings:', error)
        alert('Ошибка при сохранении настроек')
    } finally {
        isLoadingSettings.value = false
    }
}

// Corpus Actions
const fetchCorpuses = async () => {
    isLoadingCorpuses.value = true
    try {
        const response = await axios.get('corpuses/')
        corpuses.value = response.data
    } catch (error) {
        console.error('Failed to fetch corpuses:', error)
    } finally {
        isLoadingCorpuses.value = false
    }
}

const openAddCorpus = () => {
    editingCorpus.value = { id: null, name: '' }
    showCorpusModal.value = true
}

const openEditCorpus = (corpus) => {
    editingCorpus.value = { ...corpus }
    showCorpusModal.value = true
}

const saveCorpus = async () => {
    try {
        if (editingCorpus.value.id) {
            await axios.put(`corpuses/${editingCorpus.value.id}/`, editingCorpus.value)
        } else {
            await axios.post('corpuses/', editingCorpus.value)
        }
        showCorpusModal.value = false
        fetchCorpuses()
    } catch (error) {
        alert(error.response?.data?.error || error.response?.data?.name?.[0] || 'Ошибка при сохранении')
    }
}

const deleteCorpus = async (corpus) => {
    if (!confirm(`Вы уверены, что хотите удалить здание "${corpus.name}"?`)) return
    try {
        await axios.delete(`corpuses/${corpus.id}/`)
        fetchCorpuses()
    } catch (error) {
        alert(error.response?.data?.error || 'Ошибка при удалении')
    }
}

onMounted(() => {
    fetchSettings()
    fetchCorpuses()
})
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
                <div class="list-group shadow-sm mb-4">
                    <button 
                        class="list-group-item list-group-item-action d-flex align-items-center" 
                        :class="{ active: currentTab === 'worktime' }"
                        @click="currentTab = 'worktime'"
                    >
                        <i class="bi bi-clock me-2"></i>Рабочее время
                    </button>
                    <button 
                        class="list-group-item list-group-item-action d-flex align-items-center" 
                        :class="{ active: currentTab === 'buildings' }"
                        @click="currentTab = 'buildings'"
                    >
                        <i class="bi bi-building me-2"></i>Здания
                    </button>
                    <button class="list-group-item list-group-item-action disabled d-flex align-items-center">
                        <i class="bi bi-envelope me-2"></i>Уведомления (скоро)
                    </button>
                </div>
            </div>
            
            <div class="col-md-9">
                <!-- WORK TIME TAB -->
                <div v-if="currentTab === 'worktime'">
                    <div class="card shadow-sm mb-4">
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
                                    <button type="submit" class="btn btn-primary px-5 py-2 fw-bold" :disabled="isLoadingSettings">
                                        <span v-if="isLoadingSettings" class="spinner-border spinner-border-sm me-2"></span>
                                        Сохранить изменения
                                    </button>
                                    <span v-if="saveSuccess" class="text-success animate-fade-in">
                                        <i class="bi bi-check-circle-fill me-1"></i> Сохранено успешно!
                                    </span>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>

                <!-- BUILDINGS TAB -->
                <div v-if="currentTab === 'buildings'">
                    <div class="card shadow-sm">
                        <div class="card-header bg-white border-bottom d-flex justify-content-between align-items-center">
                            <h5 class="mb-0">Управление зданиями</h5>
                            <button class="btn btn-sm btn-success" @click="openAddCorpus">
                                <i class="bi bi-plus-lg me-1"></i>Добавить здание
                            </button>
                        </div>
                        <div class="card-body p-0">
                            <div v-if="isLoadingCorpuses" class="text-center py-5">
                                <div class="spinner-border text-primary" role="status"></div>
                            </div>
                            <div v-else-if="corpuses.length === 0" class="text-center py-5 text-muted">
                                Здания не найдены. Добавьте первое здание.
                            </div>
                            <div v-else class="table-responsive">
                                <table class="table table-hover align-middle mb-0">
                                    <thead class="table-light">
                                        <tr>
                                            <th style="width: 80px;">№</th>
                                            <th>Название здания</th>
                                            <th class="text-end">Действия</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="corpus in corpuses" :key="corpus.id">
                                            <td><span class="badge bg-light text-primary border">#{{ corpus.id }}</span></td>
                                            <td class="fw-bold">{{ corpus.name }}</td>
                                            <td class="text-end">
                                                <div class="btn-group btn-group-sm">
                                                    <button class="btn btn-outline-primary" @click="openEditCorpus(corpus)">
                                                        <i class="bi bi-pencil"></i>
                                                    </button>
                                                    <button class="btn btn-outline-danger" @click="deleteCorpus(corpus)">
                                                        <i class="bi bi-trash"></i>
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Corpus Modal (Improved UI) -->
    <div v-if="showCorpusModal" class="modal-overlay" @click.self="showCorpusModal = false">
        <div class="modal-dialog animate-slide-up">
            <div class="modal-content border-0 shadow-lg" style="border-radius: 1.25rem; overflow: hidden;">
                <div class="modal-header bg-primary text-white p-4 border-0">
                    <h5 class="modal-title fw-bold">
                        <i class="bi" :class="editingCorpus.id ? 'bi-pencil-square' : 'bi-plus-circle-dotted'"></i>
                        {{ editingCorpus.id ? ' Редактировать здание' : ' Новое здание' }}
                    </h5>
                    <button type="button" class="btn-close btn-close-white" @click="showCorpusModal = false"></button>
                </div>
                <form @submit.prevent="saveCorpus">
                    <div class="modal-body p-4 bg-white">
                        <div class="mb-4">
                            <label class="form-label text-uppercase small fw-black text-muted mb-2 ls-1">Название здания</label>
                            <div class="input-group input-group-lg">
                                <span class="input-group-text bg-light border-end-0"><i class="bi bi-building text-primary"></i></span>
                                <input 
                                    v-model="editingCorpus.name" 
                                    class="form-control bg-light border-start-0 ps-0" 
                                    placeholder="Например: Главный корпус" 
                                    required
                                    autofocus
                                >
                            </div>
                            <div class="form-text mt-2 small">Введите уникальное название для идентификации здания.</div>
                        </div>

                        <div v-if="editingCorpus.id" class="alert alert-light border small text-muted">
                            <i class="bi bi-info-circle me-1"></i> Системный номер: <strong>#{{ editingCorpus.id }}</strong>
                        </div>
                    </div>
                    <div class="modal-footer p-4 bg-light border-0 d-flex gap-3">
                        <button type="button" class="btn btn-link text-secondary text-decoration-none fw-bold flex-grow-1" @click="showCorpusModal = false">
                            Отмена
                        </button>
                        <button type="submit" class="btn btn-primary px-4 py-2 fw-bold shadow-sm flex-grow-1" style="border-radius: 0.75rem;">
                            {{ editingCorpus.id ? 'Обновить' : 'Создать здание' }}
                        </button>
                    </div>
                </form>
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

/* Modal Styling */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(8px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 2000;
    padding: 1rem;
}

.modal-dialog {
    width: 100%;
    max-width: 480px;
}

.animate-slide-up {
    animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px) scale(0.95); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

.ls-1 { letter-spacing: 1px; }
.fw-black { font-weight: 800; }

.input-group-text {
    border-color: #e2e8f0;
}
.form-control:focus {
    box-shadow: none;
    background-color: #fff !important;
}
.btn-primary {
    transition: all 0.2s;
}
.btn-primary:active {
    transform: scale(0.98);
}
</style>

<script setup>
import { ref, onMounted } from 'vue'
import axios from '../axios'
import AdminSubNav from '../components/AdminSubNav.vue'

// Tabs
const currentTab = ref('worktime') // 'worktime', 'buildings'

// System Settings
const settings = ref({
    work_start_time: '09:00',
    work_end_time: '18:00',
    allow_outside_working_hours: false,
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
    <div class="container-fluid pb-5 bg-light-subtle">
        <AdminSubNav />

        <div class="row">
            <!-- Sidebar Navigation -->
            <div class="col-lg-3 mb-4">
                <div class="card border-0 shadow-sm overflow-hidden" style="border-radius: 1rem;">
                    <div class="list-group list-group-flush p-2">
                        <button 
                            class="list-group-item list-group-item-action border-0 mb-1 rounded-3 d-flex align-items-center py-3" 
                            :class="{ 'bg-primary text-white shadow-sm': currentTab === 'worktime' }"
                            @click="currentTab = 'worktime'"
                        >
                            <i class="bi bi-clock-history me-3 fs-5"></i>
                            <div>
                                <div class="fw-bold">Рабочее время</div>
                                <div class="small opacity-75">График приема заявок</div>
                            </div>
                        </button>
                        <button 
                            class="list-group-item list-group-item-action border-0 mb-1 rounded-3 d-flex align-items-center py-3" 
                            :class="{ 'bg-primary text-white shadow-sm': currentTab === 'buildings' }"
                            @click="currentTab = 'buildings'"
                        >
                            <i class="bi bi-buildings me-3 fs-5"></i>
                            <div>
                                <div class="fw-bold">Здания</div>
                                <div class="small opacity-75">Список корпусов университета</div>
                            </div>
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-9">
                <!-- WORK TIME TAB -->
                <div v-if="currentTab === 'worktime'" class="animate-fade-in">
                    <div class="card border-0 shadow-sm" style="border-radius: 1rem;">
                        <div class="card-header bg-white p-4 border-0">
                            <h5 class="fw-bold mb-0">Управление рабочим графиком</h5>
                        </div>
                        <div class="card-body p-4 pt-0">
                            <form @submit.prevent="saveSettings">
                                <div class="row g-4 mb-4">
                                    <div class="col-md-6">
                                        <div class="p-4 bg-light rounded-4 border border-light-subtle">
                                            <label class="form-label text-uppercase small fw-bold text-muted mb-3">Начало работы</label>
                                            <div class="input-group input-group-lg shadow-sm">
                                                <span class="input-group-text bg-white border-end-0"><i class="bi bi-sunrise text-warning"></i></span>
                                                <input type="time" v-model="settings.work_start_time" class="form-control border-start-0" required>
                                            </div>
                                            <p class="form-text mt-3 mb-0 small text-muted">Время, с которого пользователи могут отправлять заявки.</p>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="p-4 bg-light rounded-4 border border-light-subtle">
                                            <label class="form-label text-uppercase small fw-bold text-muted mb-3">Конец работы</label>
                                            <div class="input-group input-group-lg shadow-sm">
                                                <span class="input-group-text bg-white border-end-0"><i class="bi bi-sunset text-primary"></i></span>
                                                <input type="time" v-model="settings.work_end_time" class="form-control border-start-0" required>
                                            </div>
                                            <p class="form-text mt-3 mb-0 small text-muted">После этого времени отправка будет ограничена.</p>
                                        </div>
                                    </div>
                                </div>

                                <div class="mb-5 p-4 bg-primary bg-opacity-10 rounded-4 border border-primary-subtle">
                                    <div class="form-check form-switch d-flex align-items-center">
                                        <input class="form-check-input custom-switch me-3" type="checkbox" id="allowOutside" v-model="settings.allow_outside_working_hours">
                                        <label class="form-check-label fw-bold mb-0" for="allowOutside">
                                            Разрешить заявки вне рабочего времени
                                        </label>
                                    </div>
                                    <div class="ms-5 mt-2 text-muted small">
                                        Пользователи смогут отправлять заявки в любое время, но будут предупреждены о нерабочем времени.
                                    </div>
                                </div>

                                <div class="d-flex align-items-center gap-3">
                                    <button type="submit" class="btn btn-primary px-5 py-3 fw-bold rounded-pill shadow" :disabled="isLoadingSettings">
                                        <span v-if="isLoadingSettings" class="spinner-border spinner-border-sm me-2"></span>
                                        <i v-else class="bi bi-cloud-upload me-2"></i>
                                        Сохранить настройки
                                    </button>
                                    <div v-if="saveSuccess" class="badge bg-success-subtle text-success p-2 rounded-pill px-3 py-2">
                                        <i class="bi bi-check-circle-fill me-1"></i> Сохранено!
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>

                <!-- BUILDINGS TAB -->
                <div v-if="currentTab === 'buildings'" class="animate-fade-in">
                    <div class="card border-0 shadow-sm overflow-hidden" style="border-radius: 1rem;">
                        <div class="card-header bg-white p-4 border-0 d-flex justify-content-between align-items-center">
                            <h5 class="fw-bold mb-0">Реестр зданий (корпусов)</h5>
                            <button class="btn btn-primary rounded-pill px-4 shadow-sm" @click="openAddCorpus">
                                <i class="bi bi-plus-lg me-1"></i>Добавить здание
                            </button>
                        </div>
                        <div class="card-body p-0">
                            <div v-if="isLoadingCorpuses" class="text-center py-5">
                                <div class="spinner-border text-primary" role="status"></div>
                            </div>
                            <div v-else-if="corpuses.length === 0" class="text-center py-5">
                                <i class="bi bi-building-slash fs-1 text-muted mb-3 d-block"></i>
                                <p class="text-muted">Здания не найдены. Добавьте первое здание.</p>
                            </div>
                            <div v-else class="table-responsive">
                                <table class="table table-hover align-middle mb-0">
                                    <thead class="bg-light">
                                        <tr>
                                            <th class="ps-4 py-3" style="width: 100px;">ID</th>
                                            <th class="py-3">Наименование корпуса</th>
                                            <th class="text-end pe-4 py-3">Управление</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="corpus in corpuses" :key="corpus.id" class="transition-all hover-row">
                                            <td class="ps-4">
                                                <span class="badge bg-light text-secondary border">#{{ corpus.id }}</span>
                                            </td>
                                            <td class="fw-bold text-dark">{{ corpus.name }}</td>
                                            <td class="text-end pe-4">
                                                <div class="btn-group shadow-sm rounded-3 overflow-hidden">
                                                    <button class="btn btn-white btn-sm px-3 py-2 border" @click="openEditCorpus(corpus)" title="Редактировать">
                                                        <i class="bi bi-pencil text-primary"></i>
                                                    </button>
                                                    <button class="btn btn-white btn-sm px-3 py-2 border" @click="deleteCorpus(corpus)" title="Удалить">
                                                        <i class="bi bi-trash text-danger"></i>
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
                            <label class="form-label text-uppercase small fw-bold text-muted mb-2 ls-1">Название здания</label>
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
                            <div class="form-text mt-2 small text-muted">Введите уникальное название корпуса университета.</div>
                        </div>

                        <div v-if="editingCorpus.id" class="p-3 bg-light rounded-3 border-start border-primary border-4 small text-muted">
                            <i class="bi bi-info-circle me-1"></i> Системный идентификатор: <strong>#{{ editingCorpus.id }}</strong>
                        </div>
                    </div>
                    <div class="modal-footer p-4 bg-light border-0 d-flex gap-3">
                        <button type="button" class="btn btn-link text-secondary text-decoration-none fw-bold flex-grow-1" @click="showCorpusModal = false">
                            Отмена
                        </button>
                        <button type="submit" class="btn btn-primary px-4 py-3 fw-bold shadow-sm flex-grow-1 rounded-3">
                            {{ editingCorpus.id ? 'Обновить данные' : 'Создать здание' }}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</template>

<style scoped>
.transition-all {
    transition: all 0.2s ease;
}

.hover-row:hover {
    background-color: rgba(67, 97, 238, 0.02) !important;
}

.custom-switch {
    width: 3.5rem !important;
    height: 1.75rem !important;
    cursor: pointer;
}

.ls-1 { letter-spacing: 0.5px; }

.card {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.animate-fade-in {
    animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(15, 23, 42, 0.7);
    backdrop-filter: blur(8px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 2000;
    padding: 1rem;
}

.animate-slide-up {
    animation: slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(40px) scale(0.95); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

.btn-white {
    background: #fff;
    border-color: #e2e8f0;
}

.btn-white:hover {
    background: #f8fafc;
    border-color: #ccc;
}

.form-control:focus, .form-select:focus {
    border-color: #4361ee;
    box-shadow: 0 0 0 0.25rem rgba(67, 97, 238, 0.15);
}

.breadcrumb-item a {
    text-decoration: none;
    color: #64748b;
}

.breadcrumb-item.active {
    color: #4361ee;
    font-weight: 500;
}
</style>

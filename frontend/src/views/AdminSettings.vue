<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from '../axios'

// Tabs
const currentTab = ref('worktime') // 'worktime', 'buildings', or 'notifications'

// System Settings
const settings = ref({
    work_start_time: '09:00',
    work_end_time: '18:00',
    allow_outside_working_hours: false,
    // SMTP & Email
    email_from_name: 'HelpDesk',
    email_from_address: '',
    smtp_host: 'smtp.gmail.com',
    smtp_port: 587,
    smtp_user: '',
    smtp_password: '',
    smtp_use_tls: true,
    smtp_use_ssl: false,
    // Notify toggles
    notify_on_create: true,
    notify_on_comment: true,
    notify_on_complete: true,
    notify_on_overdue: true,
    overdue_notification_email: ''
})
const isLoadingSettings = ref(false)
const saveSuccess = ref(false)

// Buildings (Corpuses)
const corpuses = ref([])
const isLoadingCorpuses = ref(false)
const showCorpusModal = ref(false)
const editingCorpus = ref({ id: null, name: '' })

// Notifications - Templates
const templates = ref([])
const isLoadingTemplates = ref(false)
const selectedTemplateType = ref('new_ticket')

// Notifications - Logs
const logs = ref([])
const isLoadingLogs = ref(false)
const logSearch = ref('')
const logStatus = ref('')
const logPage = ref(1)

// Test Email
const testRecipient = ref('')
const isSendingTest = ref(false)
const testResult = ref(null)

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

// Template Actions
const fetchTemplates = async () => {
    isLoadingTemplates.value = true
    try {
        const response = await axios.get('email-templates/')
        templates.value = response.data
    } catch (error) {
        console.error('Failed to fetch templates:', error)
    } finally {
        isLoadingTemplates.value = false
    }
}

const activeTemplate = computed(() => {
    return templates.value.find(t => t.type === selectedTemplateType.value) || { subject: '', body: '', is_active: true }
})

const saveTemplate = async () => {
    try {
        const t = activeTemplate.value
        await axios.patch(`email-templates/${t.id}/`, t)
        alert('Шаблон сохранен')
    } catch (error) {
        console.error('Failed to save template:', error)
        alert('Ошибка при сохранении шаблона')
    }
}

// Log Actions
const fetchLogs = async () => {
    isLoadingLogs.value = true
    try {
        let url = 'email-logs/'
        const params = new URLSearchParams()
        if (logSearch.value) params.append('to_email', logSearch.value)
        if (logStatus.value) params.append('status', logStatus.value)
        
        const response = await axios.get(`${url}?${params.toString()}`)
        logs.value = response.data
    } catch (error) {
        console.error('Failed to fetch logs:', error)
    } finally {
        isLoadingLogs.value = false
    }
}

// Test Email Actions
const sendTestEmail = async () => {
    if (!testRecipient.value) return
    isSendingTest.value = true
    testResult.value = null
    try {
        const response = await axios.post('settings/send_test_email/', { to_email: testRecipient.value })
        testResult.value = { success: true, message: response.data.message }
    } catch (error) {
        testResult.value = { success: false, message: error.response?.data?.error || 'Ошибка при отправке теста' }
    } finally {
        isSendingTest.value = false
    }
}

onMounted(() => {
    fetchSettings()
    fetchCorpuses()
    fetchTemplates()
    fetchLogs()
})
</script>

<template>
    <div class="container-fluid py-4 min-vh-100 bg-light-subtle">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <nav aria-label="breadcrumb">
                    <ol class="breadcrumb mb-1">
                        <li class="breadcrumb-item"><router-link to="/admin">Администрирование</router-link></li>
                        <li class="breadcrumb-item active">Настройки</li>
                    </ol>
                </nav>
                <h2 class="text-primary fw-bold mb-0">
                    <i class="bi bi-gear-wide-connected me-2"></i>Настройки системы
                </h2>
            </div>
            <router-link to="/admin" class="btn btn-outline-secondary rounded-pill px-4">
                <i class="bi bi-arrow-left me-1"></i>Назад
            </router-link>
        </div>

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
                        <button 
                            class="list-group-item list-group-item-action border-0 rounded-3 d-flex align-items-center py-3 transition-all" 
                            :class="{ 'bg-primary text-white shadow-sm': currentTab === 'notifications' }"
                            @click="currentTab = 'notifications'"
                        >
                            <i class="bi bi-envelope-at me-3 fs-5"></i>
                            <div>
                                <div class="fw-bold">Уведомления</div>
                                <div class="small" :class="currentTab === 'notifications' ? 'text-white-50' : 'text-muted'">Email и SMTP настройки</div>
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

                <!-- NOTIFICATIONS TAB -->
                <div v-if="currentTab === 'notifications'" class="animate-fade-in pb-5">
                    <!-- SMTP Settings -->
                    <div class="card border-0 shadow-sm mb-4 overflow-hidden" style="border-radius: 1rem;">
                        <div class="card-header bg-white p-4 border-0">
                            <h5 class="fw-bold mb-0"><i class="bi bi-server me-2 text-primary"></i>Настройки SMTP сервера</h5>
                        </div>
                        <div class="card-body p-4 pt-0">
                            <form @submit.prevent="saveSettings">
                                <div class="row g-4 mb-4">
                                    <div class="col-md-6">
                                        <label class="form-label small fw-bold text-muted">SMTP Host</label>
                                        <input type="text" v-model="settings.smtp_host" class="form-control" placeholder="smtp.gmail.com">
                                    </div>
                                    <div class="col-md-3">
                                        <label class="form-label small fw-bold text-muted">Port</label>
                                        <input type="number" v-model="settings.smtp_port" class="form-control" placeholder="587">
                                    </div>
                                    <div class="col-md-3 d-flex align-items-end mb-1">
                                        <div class="form-check form-switch">
                                            <input class="form-check-input" type="checkbox" id="smtpTls" v-model="settings.smtp_use_tls">
                                            <label class="form-check-label small" for="smtpTls">Use TLS</label>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label small fw-bold text-muted">SMTP Username</label>
                                        <input type="text" v-model="settings.smtp_user" class="form-control" placeholder="example@gmail.com">
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label small fw-bold text-muted">SMTP Password</label>
                                        <input type="password" v-model="settings.smtp_password" class="form-control" placeholder="••••••••••••">
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label small fw-bold text-muted">From Address</label>
                                        <input type="email" v-model="settings.email_from_address" class="form-control" placeholder="helpdesk@university.edu">
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label small fw-bold text-muted">From Name</label>
                                        <input type="text" v-model="settings.email_from_name" class="form-control" placeholder="HelpDesk Korkyt">
                                    </div>
                                </div>
                                <div class="d-flex align-items-center gap-3">
                                    <button type="submit" class="btn btn-primary px-4 py-2 fw-bold rounded-pill">
                                        Сохранить настройки
                                    </button>
                                    
                                    <div class="input-group ms-auto" style="max-width: 400px;">
                                        <input type="email" v-model="testRecipient" class="form-control border-primary" placeholder="Email для теста">
                                        <button class="btn btn-primary px-3" type="button" @click="sendTestEmail" :disabled="isSendingTest || !testRecipient">
                                            <span v-if="isSendingTest" class="spinner-border spinner-border-sm me-1"></span>
                                            <i v-else class="bi bi-send me-1"></i>
                                            Тест
                                        </button>
                                    </div>
                                </div>
                                <div v-if="testResult" class="mt-3 alert" :class="testResult.success ? 'alert-success' : 'alert-danger'">
                                    <i class="bi" :class="testResult.success ? 'bi-check-circle' : 'bi-exclamation-triangle'"></i> {{ testResult.message }}
                                </div>
                            </form>
                        </div>
                    </div>

                    <!-- Notification Toggles -->
                    <div class="card border-0 shadow-sm mb-4 overflow-hidden" style="border-radius: 1rem;">
                        <div class="card-header bg-white p-4 border-0">
                            <h5 class="fw-bold mb-0"><i class="bi bi-toggle-on me-2 text-primary"></i>Управление уведомлениями</h5>
                        </div>
                        <div class="card-body p-4 pt-0">
                            <div class="row g-4">
                                <div class="col-md-6">
                                    <div class="p-3 bg-light rounded-3 d-flex justify-content-between align-items-center">
                                        <div>
                                            <div class="fw-bold">Новая заявка</div>
                                            <div class="small text-muted">Уведомление хелпдеску</div>
                                        </div>
                                        <div class="form-check form-switch">
                                            <input class="form-check-input" type="checkbox" v-model="settings.notify_on_create" @change="saveSettings">
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="p-3 bg-light rounded-3 d-flex justify-content-between align-items-center">
                                        <div>
                                            <div class="fw-bold">Комментарий хелпера</div>
                                            <div class="small text-muted">Уведомление автору</div>
                                        </div>
                                        <div class="form-check form-switch">
                                            <input class="form-check-input" type="checkbox" v-model="settings.notify_on_comment" @change="saveSettings">
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="p-3 bg-light rounded-3 d-flex justify-content-between align-items-center">
                                        <div>
                                            <div class="fw-bold">Заявка выполнена</div>
                                            <div class="small text-muted">Уведомление автору</div>
                                        </div>
                                        <div class="form-check form-switch">
                                            <input class="form-check-input" type="checkbox" v-model="settings.notify_on_complete" @change="saveSettings">
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="p-4 bg-primary bg-opacity-10 rounded-3 border border-primary-subtle">
                                        <div class="d-flex justify-content-between align-items-center mb-3">
                                            <div>
                                                <div class="fw-bold">Просроченная заявка</div>
                                                <div class="small text-muted">Email мониторинга:</div>
                                            </div>
                                            <div class="form-check form-switch">
                                                <input class="form-check-input" type="checkbox" v-model="settings.notify_on_overdue" @change="saveSettings">
                                            </div>
                                        </div>
                                        <input type="email" v-model="settings.overdue_notification_email" class="form-control form-control-sm" placeholder="admin@korkyt.kz" @blur="saveSettings">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Email Templates -->
                    <div class="card border-0 shadow-sm mb-4 overflow-hidden" style="border-radius: 1rem;">
                        <div class="card-header bg-white p-4 border-0">
                            <h5 class="fw-bold mb-0"><i class="bi bi-file-earmark-code me-2 text-primary"></i>Шаблоны писем</h5>
                        </div>
                        <div class="card-body p-4 pt-0">
                            <div class="row">
                                <div class="col-md-4 border-end">
                                    <div class="list-group list-group-flush mb-4">
                                        <button 
                                            v-for="template in templates" :key="template.id"
                                            class="list-group-item list-group-item-action border-0 mb-1 rounded-3 py-3"
                                            :class="{ 'bg-primary text-white': selectedTemplateType === template.type }"
                                            @click="selectedTemplateType = template.type"
                                        >
                                            <div class="fw-bold">{{ template.type_display }}</div>
                                            <small :class="selectedTemplateType === template.type ? 'text-white-50' : 'text-muted'">{{ template.type }}</small>
                                        </button>
                                    </div>
                                </div>
                                <div class="col-md-8">
                                    <div v-if="activeTemplate.id">
                                        <div class="mb-3">
                                            <label class="form-label small fw-bold text-muted">Тема письма</label>
                                            <input type="text" v-model="activeTemplate.subject" class="form-control shadow-none">
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label small fw-bold text-muted">Текст письма (HTML)</label>
                                            <textarea v-model="activeTemplate.body" class="form-control shadow-none" rows="10"></textarea>
                                        </div>
                                        
                                        <div class="p-3 bg-light rounded-3 mb-4 small">
                                            <div class="fw-bold mb-2">Доступные переменные:</div>
                                            <div class="d-flex flex-wrap gap-2">
                                                <span class="badge bg-white text-primary border">\{\{ ticket_id \}\}</span>
                                                <span class="badge bg-white text-primary border">\{\{ title \}\}</span>
                                                <span class="badge bg-white text-primary border">\{\{ description \}\}</span>
                                                <span class="badge bg-white text-primary border">\{\{ building \}\}</span>
                                                <span class="badge bg-white text-primary border">\{\{ room \}\}</span>
                                                <span class="badge bg-white text-primary border">\{\{ user_name \}\}</span>
                                                <span class="badge bg-white text-primary border">\{\{ dashboard_link \}\}</span>
                                            </div>
                                        </div>

                                        <div class="d-flex justify-content-between align-items-center">
                                            <div class="form-check form-switch">
                                                <input class="form-check-input" type="checkbox" id="tplActive" v-model="activeTemplate.is_active">
                                                <label class="form-check-label" for="tplActive">Шаблон активен</label>
                                            </div>
                                            <button @click="saveTemplate" class="btn btn-primary px-4 py-2 rounded-pill shadow-sm">
                                                Сохранить шаблон
                                            </button>
                                        </div>
                                    </div>
                                    <div v-else class="text-center py-5 text-muted">
                                        Загрузка шаблонов...
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Email Logs -->
                    <div class="card border-0 shadow-sm overflow-hidden" style="border-radius: 1rem;">
                        <div class="card-header bg-white p-4 border-0 d-flex justify-content-between align-items-center">
                            <h5 class="fw-bold mb-0"><i class="bi bi-journal-text me-2 text-primary"></i>История уведомлений</h5>
                            <div class="d-flex gap-2">
                                <select v-model="logStatus" class="form-select form-select-sm rounded-pill px-3" @change="fetchLogs">
                                    <option value="">Все статусы</option>
                                    <option value="success">Успешно</option>
                                    <option value="failed">Ошибка</option>
                                </select>
                                <input type="text" v-model="logSearch" class="form-control form-control-sm rounded-pill px-3" placeholder="Поиск по Email..." @input="fetchLogs">
                            </div>
                        </div>
                        <div class="card-body p-0">
                            <div v-if="isLoadingLogs" class="text-center py-5">
                                <div class="spinner-border text-primary" role="status"></div>
                            </div>
                            <div v-else class="table-responsive">
                                <table class="table table-hover align-middle mb-0 small">
                                    <thead class="bg-light">
                                        <tr>
                                            <th class="ps-4">Дата</th>
                                            <th>Кому</th>
                                            <th>Тип</th>
                                            <th>Статус</th>
                                            <th class="pe-4">Результат</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="log in logs" :key="log.id">
                                            <td class="ps-4 text-nowrap text-muted">
                                                {{ new Date(log.created_at).toLocaleString() }}
                                            </td>
                                            <td class="fw-bold">{{ log.to_email }}</td>
                                            <td>{{ log.template_type }}</td>
                                            <td>
                                                <span :class="log.status === 'success' ? 'text-success' : 'text-danger'">
                                                    <i class="bi" :class="log.status === 'success' ? 'bi-check-circle-fill' : 'bi-x-circle-fill'"></i>
                                                    {{ log.status === 'success' ? ' Успешно' : ' Ошибка' }}
                                                </span>
                                            </td>
                                            <td class="pe-4">
                                                <div v-if="log.error_message" class="text-danger small" :title="log.error_message">
                                                    {{ log.error_message.substring(0, 40) }}...
                                                </div>
                                                <span v-else class="text-muted">–</span>
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

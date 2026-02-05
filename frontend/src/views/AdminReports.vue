<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import axios from '../axios'
import Clock from '../components/Clock.vue'
import AdminSubNav from '../components/AdminSubNav.vue'

const tickets = ref([])
const corpuses = ref([])
const helpdesks = ref([])
const isLoading = ref(false)

const notifications = ref({
    new_requests: 0,
    new_feedbacks: 0
})

const filters = ref({
    date_from: '',
    date_to: '',
    statuses: ['NEW', 'IN_PROGRESS', 'WAITING_FOR_PARTS', 'CLOSED', 'CANCELED'],
    building: '',
    helper_id: ''
})

const availableStatuses = [
    { value: 'NEW', label: 'Новая' },
    { value: 'IN_PROGRESS', label: 'В работе' },
    { value: 'WAITING_FOR_PARTS', label: 'Ожидается запчасть' },
    { value: 'CLOSED', label: 'Завершена' },
    { value: 'CANCELED', label: 'Отменена' }
]

const fetchCorpuses = async () => {
    try {
        const response = await axios.get('corpuses/')
        corpuses.value = response.data
    } catch (e) { console.error(e) }
}

const fetchHelpdesks = async () => {
    try {
        const response = await axios.get('users/')
        helpdesks.value = response.data.filter(u => u.role === 'helpdesk')
    } catch (e) { console.error(e) }
}

const fetchNotifications = async () => {
    try {
        const response = await axios.get('admin/notifications/summary/')
        notifications.value = response.data
    } catch (error) {
        console.error('Error fetching notifications:', error)
    }
}

const fetchReport = async () => {
    isLoading.value = true
    try {
        const params = new URLSearchParams()
        if (filters.value.date_from) params.append('date_from', filters.value.date_from)
        if (filters.value.date_to) params.append('date_to', filters.value.date_to)
        if (filters.value.building) params.append('building', filters.value.building)
        if (filters.value.helper_id) params.append('helper_id', filters.value.helper_id)
        
        filters.value.statuses.forEach(s => params.append('statuses[]', s))

        const response = await axios.get(`tickets/report/?${params.toString()}`)
        tickets.value = response.data
    } catch (e) {
        console.error(e)
        alert('Ошибка при загрузке отчета')
    } finally {
        isLoading.value = false
    }
}

const exportToExcel = async () => {
    try {
        const params = new URLSearchParams()
        if (filters.value.date_from) params.append('date_from', filters.value.date_from)
        if (filters.value.date_to) params.append('date_to', filters.value.date_to)
        if (filters.value.building) params.append('building', filters.value.building)
        if (filters.value.helper_id) params.append('helper_id', filters.value.helper_id)
        filters.value.statuses.forEach(s => params.append('statuses[]', s))

        const response = await axios.get(`tickets/export_report/?${params.toString()}`, {
            responseType: 'blob'
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `tickets_report_${new Date().toISOString().split('T')[0]}.xlsx`)
        document.body.appendChild(link)
        link.click()
        link.remove()
    } catch (e) {
        console.error(e)
        alert('Ошибка при выгрузке Excel')
    }
}

const exportToPDF = async () => {
    try {
        const params = new URLSearchParams()
        if (filters.value.date_from) params.append('date_from', filters.value.date_from)
        if (filters.value.date_to) params.append('date_to', filters.value.date_to)
        if (filters.value.building) params.append('building', filters.value.building)
        if (filters.value.helper_id) params.append('helper_id', filters.value.helper_id)
        filters.value.statuses.forEach(s => params.append('statuses[]', s))

        const response = await axios.get(`tickets/export_pdf_stats/?${params.toString()}`, {
            responseType: 'blob'
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `stats_report_${new Date().toISOString().split('T')[0]}.pdf`)
        document.body.appendChild(link)
        link.click()
        link.remove()
    } catch (e) {
        console.error(e)
        alert('Ошибка при выгрузке PDF')
    }
}

const getStatusLabel = (status) => {
    const map = {
        'NEW': 'Новая',
        'IN_PROGRESS': 'В работе',
        'WAITING_FOR_PARTS': 'Ожидается запчасть',
        'CLOSED': 'Завершена',
        'CANCELED': 'Отменена'
    }
    return map[status] || status
}

const getStatusColor = (status) => {
    switch(status) {
        case 'NEW': return 'bg-success';
        case 'IN_PROGRESS': return 'bg-warning text-dark';
        case 'WAITING_FOR_PARTS': return 'bg-info text-dark';
        case 'CLOSED': return 'bg-secondary';
        case 'CANCELED': return 'bg-dark';
        default: return 'bg-light text-dark';
    }
}

const formatDate = (dateString) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleString('ru-RU', { 
        timeZone: 'Asia/Almaty', 
        day: '2-digit', month: '2-digit', year: 'numeric', 
        hour: '2-digit', minute: '2-digit' 
    })
}

onMounted(() => {
    fetchCorpuses()
    fetchHelpdesks()
    fetchNotifications()
    fetchReport()
})

// Deep watch filters to update table automatically
watch(() => filters.value, () => {
    fetchReport()
}, { deep: true })

</script>

<template>
    <div class="container-fluid pb-5">
        <AdminSubNav 
            :newRequests="notifications.new_requests" 
            :newFeedbacks="notifications.new_feedbacks"
        />

        <div class="card shadow-sm mb-4">
            <div class="card-header bg-white border-bottom fw-bold text-muted">
                <i class="bi bi-funnel me-2"></i>Параметры фильтрации
            </div>
            <div class="card-body bg-light">
                <div class="row g-3">
                    <div class="col-md-3">
                        <label class="form-label small fw-bold">Период (С)</label>
                        <input type="date" v-model="filters.date_from" class="form-control form-control-sm">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label small fw-bold">Период (По)</label>
                        <input type="date" v-model="filters.date_to" class="form-control form-control-sm">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label small fw-bold">Здание</label>
                        <select v-model="filters.building" class="form-select form-select-sm">
                            <option value="">Все здания</option>
                            <option v-for="c in corpuses" :key="c.id" :value="c.name">{{ c.name }}</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label small fw-bold">Хелпдеск</label>
                        <select v-model="filters.helper_id" class="form-select form-select-sm">
                            <option value="">Все специалисты</option>
                            <option v-for="h in helpdesks" :key="h.id" :value="h.id">{{ h.first_name }} {{ h.last_name }} ({{ h.username }})</option>
                        </select>
                    </div>
                    <div class="col-12">
                        <label class="form-label small fw-bold d-block mb-2">Статусы заявки</label>
                        <div class="d-flex flex-wrap gap-3 p-2 bg-white rounded border">
                            <div v-for="s in availableStatuses" :key="s.value" class="form-check">
                                <input class="form-check-input" type="checkbox" :value="s.value" v-model="filters.statuses" :id="'status-'+s.value">
                                <label class="form-check-label small" :for="'status-'+s.value">
                                    {{ s.label }}
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="card-footer bg-white border-top d-flex justify-content-between align-items-center">
                <div class="text-muted small">
                    Найдено записей: <strong>{{ tickets.length }}</strong>
                </div>
                <div class="d-flex gap-2">
                    <button @click="exportToPDF" class="btn btn-danger" :disabled="tickets.length === 0">
                        <i class="bi bi-file-earmark-pdf me-2"></i>Выгрузить отчет (PDF)
                    </button>
                    <button @click="exportToExcel" class="btn btn-success" :disabled="tickets.length === 0">
                        <i class="bi bi-file-earmark-excel me-2"></i>Выгрузить в Excel
                    </button>
                </div>
            </div>
        </div>

        <div class="card shadow-sm overflow-hidden">
            <div class="table-responsive" style="max-height: 500px;">
                <table class="table table-hover table-sm mb-0 align-middle">
                    <thead class="table-dark sticky-top">
                        <tr>
                            <th>ID</th>
                            <th>Дата создания</th>
                            <th>Статус</th>
                            <th>Пользователь</th>
                            <th>Здание / Каб.</th>
                            <th style="max-width: 300px;">Описание</th>
                            <th>Хелпдеск</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-if="isLoading">
                            <td colspan="8" class="text-center py-5">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Загрузка...</span>
                                </div>
                            </td>
                        </tr>
                        <tr v-else-if="tickets.length === 0">
                            <td colspan="8" class="text-center py-5 text-muted">Заявки не найдены</td>
                        </tr>
                        <tr v-for="t in tickets" :key="t.id">
                            <td class="fw-bold">#{{ t.id }}</td>
                            <td class="small">{{ formatDate(t.created_at) }}</td>
                            <td>
                                <span class="badge rounded-pill" :class="getStatusColor(t.status)">
                                    {{ getStatusLabel(t.status) }}
                                </span>
                            </td>
                            <td class="small">
                                <div>{{ t.author_username }}</div>
                            </td>
                            <td class="small">{{ t.building }}, каб. {{ t.room }}</td>
                            <td class="small text-truncate" style="max-width: 300px;" :title="t.description">
                                {{ t.description }}
                            </td>
                            <td class="small">{{ t.assigned_to_username || '-' }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</template>

<style scoped>
.form-check-input:checked {
    background-color: #0d6efd;
    border-color: #0d6efd;
}
.table-responsive::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
.table-responsive::-webkit-scrollbar-thumb {
    background: #ccc;
    border-radius: 4px;
}
.table-responsive::-webkit-scrollbar-track {
    background: #f1f1f1;
}
</style>

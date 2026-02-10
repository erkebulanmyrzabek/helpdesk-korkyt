<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from '../axios'
import Clock from '../components/Clock.vue'
import AdminSubNav from '../components/AdminSubNav.vue'
import { useRoute } from 'vue-router'
import { watch } from 'vue'

const route = useRoute()

const stats = ref({
    total: 0,
    by_status: [],
    helpdesk_stats: [],
    teacher_stats: [],
    category_stats: {},
    avg_completion_time_minutes: null,

    total_helpers: 0,
    overdue_count: 0
})
const tickets = ref([])
const users = ref([])
const registrationRequests = ref([])
const newUser = ref({
    username: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'teacher',
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

const selectedTicket = ref(null)

const visiblePasswords = ref(new Set())
const isCreatingUser = ref(false)

const notifications = ref({
    new_requests: 0,
    new_feedbacks: 0
})

const filters = ref({
    id: '',
    date_from: '',
    date_to: '',
    statuses: [],
    author: '',
    helper_id: '',
    building: ''
})

const helpdesks = ref([])

const fetchHelpdesks = async () => {
    try {
        const response = await axios.get('users/')
        helpdesks.value = response.data.filter(u => u.role === 'helpdesk')
    } catch (e) { console.error(e) }
}

const availableStatuses = [
    { value: 'NEW', label: 'Новая' },
    { value: 'IN_PROGRESS', label: 'В работе' },
    { value: 'WAITING_FOR_PARTS', label: 'Ожидается запчасть' },
    { value: 'WAITING_APPROVE', label: 'Ожидает' },
    { value: 'CLOSED', label: 'Закрыта' },
    { value: 'CANCELED', label: 'Отменена' }
]

const corpuses = ref([])

const filteredTickets = computed(() => {
    return tickets.value.filter(ticket => {
        if (filters.value.id && !String(ticket.id).includes(filters.value.id)) return false
        if (filters.value.author && !ticket.author_username.toLowerCase().includes(filters.value.author.toLowerCase())) return false
        return true
    })
})

const togglePassword = (userId) => {
    if (visiblePasswords.value.has(userId)) {
        visiblePasswords.value.delete(userId)
    } else {
        visiblePasswords.value.add(userId)
    }
}

const activeTab = ref(route.query.tab || 'stats') // 'stats', 'users', 'requests'

watch(() => route.query.tab, (newTab) => {
    if (newTab) activeTab.value = newTab
    else activeTab.value = 'stats'
    
    if (activeTab.value === 'requests') {
        fetchRegistrationRequests()
    }
})

const fetchStats = async () => {
    try {
        const response = await axios.get('tickets/stats/')
        stats.value = response.data
    } catch (error) {
        console.error(error)
    }
}

const fetchNotifications = async () => {
    try {
        const response = await axios.get('admin/notifications/summary/')
        notifications.value = response.data
    } catch (error) {
        console.error('Error fetching notifications:', error)
    }
}

const fetchTickets = async () => {
    try {
        const params = new URLSearchParams()
        if (filters.value.date_from) params.append('date_from', filters.value.date_from)
        if (filters.value.date_to) params.append('date_to', filters.value.date_to)
        if (filters.value.statuses.length > 0) {
            filters.value.statuses.forEach(s => params.append('statuses[]', s))
        }
        if (filters.value.building) params.append('building', filters.value.building)
        if (filters.value.helper_id) params.append('helper_id', filters.value.helper_id)
        
        const response = await axios.get(`tickets/?${params.toString()}`)
        tickets.value = response.data
    } catch (error) {
        console.error(error)
    }
}

watch(() => [filters.value.date_from, filters.value.date_to, filters.value.statuses, filters.value.building, filters.value.helper_id], () => {
    fetchTickets()
}, { deep: true })

const fetchUsers = async () => {
    try {
        const response = await axios.get('users/')
        users.value = response.data
    } catch (error) {
        console.error(error)
    }
}

const fetchRegistrationRequests = async () => {
    try {
        const response = await axios.get('registration-requests/')
        registrationRequests.value = response.data
        // Mark as viewed when admin opens this tab
        if (activeTab.value === 'requests') {
            await markRequestsViewed()
        }
    } catch (error) {
        console.error(error)
    }
}

const markRequestsViewed = async () => {
    try {
        await axios.post('admin/notifications/mark-requests-viewed/')
        notifications.value.new_requests = 0
    } catch (error) {
        console.error('Error marking requests as viewed:', error)
    }
}

const approveRegistration = async (id) => {
    if (!confirm('Одобрить регистрацию и создать пользователя?')) return
    try {
        await axios.post(`registration-requests/${id}/approve/`)
        fetchRegistrationRequests()
        fetchUsers() // Refresh user list too
        alert('Пользователь создан')
    } catch (error) {
        alert(error.response?.data?.error || 'Ошибка при одобрении')
    }
}

const rejectRegistration = async (id) => {
    if (!confirm('Отклонить этот запрос?')) return
    try {
        await axios.post(`registration-requests/${id}/reject/`)
        fetchRegistrationRequests()
    } catch (error) {
        alert('Ошибка при отклонении')
    }
}

const fetchCorpuses = async () => {
    try {
        const response = await axios.get('corpuses/')
        corpuses.value = response.data
    } catch (error) {
        console.error(error)
    }
}

const showTicketDetail = (ticket) => {
    selectedTicket.value = ticket
}

const closeTicketDetail = () => {
    selectedTicket.value = null
}



const createUser = async () => {
    if (isCreatingUser.value) return;
    isCreatingUser.value = true;
    try {
        if (newUser.value.role === 'teacher' && (!newUser.value.institute || !newUser.value.position)) {
            alert('Для роли Учитель необходимо заполнить институт и должность');
            return;
        }
        await axios.post('users/', newUser.value)
        newUser.value = { username: '', password: '', first_name: '', last_name: '', role: 'teacher', institute: '', position: '' }
        fetchUsers()
        alert('Пользователь создан')
    } catch (error) {
        console.error(error)
        const errorMsg = error.response?.data ? Object.values(error.response.data).flat().join('\n') : 'Ошибка при создании пользователя';
        alert(errorMsg)
    } finally {
        isCreatingUser.value = false;
    }
}

const deleteUser = async (id, username) => {
    if (confirm(`Вы уверены, что хотите удалить пользователя "${username}"? Все его персональные данные будут удалены, но созданные им заявки сохранятся в системе.`)) {
        try {
            await axios.delete(`users/${id}/`)
            fetchUsers()
            alert('Пользователь успешно удален')
        } catch (error) {
            console.error(error)
            alert('Ошибка при удалении: возможно у пользователя есть активные привязки, которые нельзя удалить.')
        }
    }
}



const getStatusLabel = (status) => {
    const map = {
        'NEW': 'Новая',
        'IN_PROGRESS': 'В работе',
        'WAITING_FOR_PARTS': 'Ожидается запчасть',
        'WAITING_APPROVE': 'Ожидает подтверждения',
        'CLOSED': 'Закрыта',
        'CANCELED': 'Отменена'
    }
    return map[status] || status
}

const getStatusColor = (status) => {
    switch(status) {
        case 'NEW': return 'bg-success';
        case 'IN_PROGRESS': return 'bg-warning text-dark';
        case 'WAITING_FOR_PARTS': return 'bg-info text-dark';
        case 'WAITING_APPROVE': return 'bg-primary';
        case 'CLOSED': return 'bg-secondary';
        case 'CANCELED': return 'bg-dark';
        default: return 'bg-light text-dark';
    }
}

const getRoleLabel = (role) => {
    switch(role) {
        case 'teacher': return 'Учитель';
        case 'helpdesk': return 'Хелпдеск';
        case 'admin': return 'Администратор';
        default: return role;
    }
}

const formatTime = (minutes) => {
    if (!minutes) return '-'
    if (minutes < 60) return `${Math.round(minutes)} мин`
    const hours = Math.floor(minutes / 60)
    const mins = Math.round(minutes % 60)
    return `${hours}ч ${mins}мин`
}



onMounted(() => {
    fetchStats()
    fetchTickets()
    fetchUsers()
    fetchCorpuses()
    fetchHelpdesks()
    fetchNotifications()
    if (activeTab.value === 'requests') fetchRegistrationRequests()
})

watch(activeTab, (newTab) => {
    if (newTab === 'requests') {
        fetchRegistrationRequests()
    }
})
</script>

<template>
    <div class="container-fluid">
        <AdminSubNav 
            :newRequests="notifications.new_requests" 
            :newFeedbacks="notifications.new_feedbacks"
        />
        
        <!-- STATS & TICKETS TAB -->
        <div v-if="activeTab === 'stats'">
            <!-- Main Stats Cards -->
            <div class="row g-4 mb-4">
                <div class="col-md-6">
                    <div class="card bg-gradient-primary text-white h-100 shadow-sm" style="background: linear-gradient(45deg, #002855, #00509d);">
                        <div class="card-body d-flex flex-column justify-content-center align-items-center text-center py-4">
                            <h1 class="display-4 fw-bold mb-0">{{ stats.total }}</h1>
                            <p class="mb-0 opacity-75">Всего заявок</p>
                        </div>
                    </div>
                </div>

                <div class="col-md-6">
                    <div class="card bg-danger text-white h-100 shadow-sm">
                        <div class="card-body d-flex flex-column justify-content-center align-items-center text-center py-4">
                            <h1 class="display-4 fw-bold mb-0">{{ stats.overdue_count }}</h1>
                            <p class="mb-0 opacity-75">Просрочено</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Status Distribution -->
            <div class="row g-4 mb-4">
                <div class="col-md-6">
                    <div class="card shadow-sm h-100">
                        <div class="card-header bg-white border-bottom">
                             <h5 class="mb-0 text-muted"><i class="bi bi-pie-chart me-2"></i>По статусам</h5>
                        </div>
                        <div class="card-body">
                             <div v-if="stats.by_status.length === 0" class="text-center py-4 text-muted">
                                Нет данных
                            </div>
                            <div v-else class="list-group list-group-flush">
                                <div v-for="status in stats.by_status" :key="status.status" class="list-group-item d-flex justify-content-between align-items-center py-3 border-bottom-0">
                                    <span class="d-flex align-items-center">
                                        <span class="d-inline-block rounded-circle me-3" :class="getStatusColor(status.status)" style="width: 12px; height: 12px;"></span>
                                        <span class="fs-5">{{ getStatusLabel(status.status) }}</span>
                                    </span>
                                    <span class="badge rounded-pill px-3 py-2 fs-6" :class="getStatusColor(status.status)">{{ status.count }}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Helpdesk Stats -->
                <div class="col-md-6">
                    <div class="card shadow-sm h-100">
                        <div class="card-header bg-white border-bottom">
                            <h5 class="mb-0 text-muted"><i class="bi bi-tools me-2"></i>Статистика хелпдесков</h5>
                        </div>
                        <div class="card-body">
                            <div v-if="stats.helpdesk_stats?.length === 0" class="text-center py-4 text-muted">
                                Нет данных
                            </div>
                            <div v-else class="table-responsive">
                                <table class="table table-sm mb-0">
                                    <thead>
                                        <tr>
                                            <th>Специалист</th>
                                            <th class="text-end">Выполнено</th>
                                            <th class="text-end">Рейтинг</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="hd in stats.helpdesk_stats" :key="hd.id">
                                            <td>{{ hd.first_name || hd.username }}</td>
                                            <td class="text-end">
                                                <span class="badge bg-success">{{ hd.total_tickets || 0 }}</span>
                                            </td>
                                            <td class="text-end">
                                                <span class="badge bg-warning text-dark">{{ hd.avg_rating ? hd.avg_rating.toFixed(1) : '-' }}</span>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- All Tickets Table -->
            <div class="card shadow-sm">
                <div class="card-header bg-white border-bottom">
                    <h5 class="mb-0"><i class="bi bi-list-ul me-2"></i>Все заявки</h5>
                </div>
                
                <!-- Filters -->
                <div class="card-body border-bottom bg-light">
                    <div class="row g-3">
                        <div class="col-md-2">
                            <label class="form-label small fw-bold">ID / Поиск</label>
                            <input type="text" v-model="filters.id" class="form-control form-control-sm" placeholder="ID...">
                        </div>
                        <div class="col-md-5">
                            <label class="form-label small fw-bold">Статусы (мультивыбор)</label>
                            <div class="d-flex flex-wrap gap-2 p-1 bg-white rounded border">
                                <div v-for="s in availableStatuses" :key="s.value" class="form-check form-check-inline mb-0 me-2 ms-1">
                                    <input class="form-check-input" type="checkbox" :value="s.value" v-model="filters.statuses" :id="'status-main-'+s.value">
                                    <label class="form-check-label small" :for="'status-main-'+s.value">
                                        {{ s.label }}
                                    </label>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-5">
                            <label class="form-label small fw-bold">Период создания</label>
                            <div class="input-group input-group-sm">
                                <input type="date" v-model="filters.date_from" class="form-control" title="С">
                                <span class="input-group-text">по</span>
                                <input type="date" v-model="filters.date_to" class="form-control" title="По">
                            </div>
                        </div>
                        
                        <div class="col-md-3">
                            <label class="form-label small fw-bold">Здание</label>
                            <select v-model="filters.building" class="form-select form-select-sm">
                                <option value="">Все здания</option>
                                <option v-for="corpus in corpuses" :key="corpus.id" :value="corpus.name">{{ corpus.name }}</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label small fw-bold">Хелпдеск</label>
                            <select v-model="filters.helper_id" class="form-select form-select-sm">
                                <option value="">Все специалисты</option>
                                <option v-for="h in helpdesks" :key="h.id" :value="h.id">{{ h.first_name }} {{ h.last_name }} ({{ h.username }})</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label small fw-bold">Автор</label>
                            <input type="text" v-model="filters.author" class="form-control form-control-sm" placeholder="Имя автора...">
                        </div>
                        <div class="col-md-3 d-flex align-items-end">
                            <button class="btn btn-sm btn-outline-secondary w-100" @click="filters = { id: '', date_from: '', date_to: '', statuses: [], author: '', helper_id: '', building: '' }">
                                <i class="bi bi-x-circle me-1"></i>Сбросить всё
                            </button>
                        </div>
                    </div>
                </div>

                <div class="table-responsive" style="max-height: 600px; overflow-y: auto;">
                    <table class="table table-hover mb-0">
                        <thead class="table-light sticky-top" style="z-index: 1;">
                            <tr>
                                <th>ID</th>
                                <th>Заголовок</th>
                                <th>Статус</th>
                                <th>Автор</th>
                                <th>Исполнитель</th>
                                <th>Место</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-if="filteredTickets.length === 0">
                                <td colspan="8" class="text-center py-4 text-muted">Заявки не найдены</td>
                            </tr>
                            <tr v-for="ticket in filteredTickets" 
                                :key="ticket.id" 
                                :class="{'table-danger': ticket.is_overdue}"
                                @click="showTicketDetail(ticket)"
                                style="cursor: pointer;"
                                title="Нажмите для просмотра деталей"
                            >
                                <td><strong>#{{ ticket.id }}</strong></td>
                                <td>
                                    <div class="fw-bold">{{ ticket.title }}</div>
                                    <small class="text-muted text-truncate d-block" style="max-width: 200px;">{{ ticket.description }}</small>
                                </td>
                                <td>
                                    <span class="badge rounded-pill" :class="getStatusColor(ticket.status)">
                                        {{ getStatusLabel(ticket.status) }}
                                    </span>
                                    <div v-if="ticket.is_overdue" class="badge bg-danger mt-1">ПРОСРОЧЕНО</div>
                                </td>
                                <td>{{ ticket.author_full_name || ticket.author_username }}</td>
                                <td>{{ ticket.assigned_to_username || '-' }}</td>
                                <td>{{ ticket.building }}, {{ ticket.room }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- USERS TAB -->
        <div v-if="activeTab === 'users'">
            <div class="row">
                <div class="col-md-4">
                    <div class="card shadow-sm mb-4">
                        <div class="card-header bg-white text-primary border-bottom">
                            <h5 class="mb-0"><i class="bi bi-person-plus me-2"></i>Добавить пользователя</h5>
                        </div>
                        <div class="card-body">
                            <form @submit.prevent="createUser">
                                <div class="mb-3">
                                    <label class="form-label small text-muted">Логин</label>
                                    <input v-model="newUser.username" class="form-control" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label small text-muted">Пароль</label>
                                    <input v-model="newUser.password" type="password" class="form-control" required>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-6">
                                        <label class="form-label small text-muted">Имя</label>
                                        <input v-model="newUser.first_name" class="form-control">
                                    </div>
                                    <div class="col-6">
                                        <label class="form-label small text-muted">Фамилия</label>
                                        <input v-model="newUser.last_name" class="form-control">
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label small text-muted">Роль</label>
                                    <select v-model="newUser.role" class="form-select">
                                        <option value="teacher">Учитель</option>
                                        <option value="helpdesk">Хелпдеск</option>
                                        <option value="admin">Администратор</option>
                                    </select>
                                </div>

                                <div v-if="newUser.role === 'teacher'" class="teacher-fields animate-fade-in">
                                    <div class="mb-3">
                                        <label class="form-label small fw-bold text-primary">Институт / подразделение (Обязательно)</label>
                                        <select v-model="newUser.institute" class="form-select border-primary" required>
                                            <option value="">Выберите институт...</option>
                                            <option v-for="inst in institutes" :key="inst" :value="inst">{{ inst }}</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label small fw-bold text-primary">Должность (Обязательно)</label>
                                        <input v-model="newUser.position" class="form-control border-primary" placeholder="Старший преподаватель" required>
                                    </div>
                                </div>

                                <button type="submit" class="btn btn-primary w-100" :disabled="isCreatingUser">
                                    <span v-if="isCreatingUser">
                                        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                        Создание...
                                    </span>
                                    <span v-else>Создать</span>
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
                <div class="col-md-8">
                    <div class="card shadow-sm">
                        <div class="card-header bg-white border-bottom">
                            <h5 class="mb-0"><i class="bi bi-people me-2"></i>Список пользователей</h5>
                        </div>
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead class="table-light">
                                    <tr>
                                        <th>Логин</th>
                                        <th>Имя</th>
                                        <th>Роль</th>
                                        <th>Пароль</th>
                                        <th class="text-end">Действия</th>
                                    </tr>
</thead>
                                <tbody>
                                    <tr v-for="user in users" :key="user.id">
                                        <td>{{ user.username }}</td>
                                        <td>{{ user.first_name }} {{ user.last_name }}</td>
                                        <td>
                                            <span class="badge bg-light text-dark border">
                                                {{ getRoleLabel(user.role) }}
                                            </span>
                                        </td>
                                        <td>
                                            <div v-if="user.plain_password" class="d-flex align-items-center">
                                                <code v-if="visiblePasswords.has(user.id)">{{ user.plain_password }}</code>
                                                <span v-else>••••••</span>
                                                <button class="btn btn-sm btn-link text-muted ms-2 p-0" @click="togglePassword(user.id)">
                                                    <i class="bi" :class="visiblePasswords.has(user.id) ? 'bi-eye-slash' : 'bi-eye'"></i>
                                                </button>
                                            </div>
                                            <span v-else class="text-muted small">Не сохранен</span>
                                        </td>
                                        <td class="text-end">
                                            <button 
                                                class="btn btn-sm btn-outline-danger" 
                                                @click="deleteUser(user.id, user.username)"
                                                title="Удалить пользователя"
                                                :disabled="user.role === 'admin'"
                                            >
                                                <i class="bi bi-trash"></i>
                                            </button>
                                        </td>
                                    </tr>
</tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- REGISTRATION REQUESTS TAB -->
        <div v-if="activeTab === 'requests'">
            <div class="card shadow-sm">
                <div class="card-header bg-white border-bottom d-flex justify-content-between align-items-center">
                    <h5 class="mb-0"><i class="bi bi-person-check me-2"></i>Запросы на регистрацию</h5>
                    <button class="btn btn-sm btn-outline-primary" @click="fetchRegistrationRequests">
                        <i class="bi bi-arrow-clockwise"></i> Обновить
                    </button>
                </div>
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Дата</th>
                                <th>Фамилия и имя</th>
                                <th>Login</th>
                                <th>Институт</th>
                                <th>Должность</th>
                                <th>Статус</th>
                                <th>Действия</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-if="registrationRequests.length === 0">
                                <td colspan="7" class="text-center py-4 text-muted">Запросов пока нет</td>
                            </tr>
                            <tr v-for="req in registrationRequests" :key="req.id">
                                <td class="small">{{ new Date(req.created_at).toLocaleDateString() }}</td>
                                <td>{{ req.full_name }}</td>
                                <td><code>{{ req.username }}</code></td>
                                <td class="small" style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" :title="req.institute">{{ req.institute }}</td>
                                <td class="small">{{ req.position }}</td>
                                <td>
                                    <span class="badge" :class="{
                                        'bg-warning text-dark': req.status === 'PENDING',
                                        'bg-success': req.status === 'APPROVED',
                                        'bg-danger': req.status === 'REJECTED'
                                    }">
                                        {{ req.status === 'PENDING' ? 'Ожидает' : (req.status === 'APPROVED' ? 'Одобрен' : 'Отклонен') }}
                                    </span>
                                </td>
                                <td>
                                    <div v-if="req.status === 'PENDING'" class="btn-group btn-group-sm">
                                        <button class="btn btn-success" @click="approveRegistration(req.id)" title="Одобрить">
                                            <i class="bi bi-check-lg"></i>
                                        </button>
                                        <button class="btn btn-danger" @click="rejectRegistration(req.id)" title="Отклонить">
                                            <i class="bi bi-x-lg"></i>
                                        </button>
                                    </div>
                                    <span v-else class="text-muted small">-</span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TICKET DETAIL MODAL -->
        <div v-if="selectedTicket" class="modal-backdrop fade show"></div>
        <div v-if="selectedTicket" class="modal fade show d-block" tabindex="-1" @click.self="closeTicketDetail">
            <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="bi bi-ticket-detailed me-2"></i>Детали заявки #{{ selectedTicket.id }}
                        </h5>
                        <button type="button" class="btn-close btn-close-white" @click="closeTicketDetail"></button>
                    </div>
                    <div class="modal-body p-4">
                        <div class="row g-4">
                            <!-- Left: Main Info -->
                            <div class="col-md-7">
                                <div class="section mb-4">
                                    <h6 class="text-muted text-uppercase small fw-bold mb-3">Информация о проблеме</h6>
                                    <h4 class="fw-bold mb-2">{{ selectedTicket.title }}</h4>
                                    <p class="text-dark bg-light p-3 rounded" style="white-space: pre-wrap;">{{ selectedTicket.description }}</p>
                                    
                                    <div class="d-flex gap-3 mt-3">
                                        <div class="p-2 border rounded bg-white flex-fill">
                                            <small class="text-muted d-block">Здание</small>
                                            <span class="fw-bold">{{ selectedTicket.building }}</span>
                                        </div>
                                        <div class="p-2 border rounded bg-white flex-fill">
                                            <small class="text-muted d-block">Кабинет</small>
                                            <span class="fw-bold">{{ selectedTicket.room }}</span>
                                        </div>
                                    </div>
                                </div>

                                <div class="section mb-4">
                                    <h6 class="text-muted text-uppercase small fw-bold mb-3">Хронология и комментарии</h6>
                                    <div class="timeline ps-3 border-start">
                                        <div class="mb-3 position-relative">
                                            <small class="text-muted d-block">Создана</small>
                                            <span class="fw-bold">{{ new Date(selectedTicket.created_at).toLocaleString() }}</span>
                                        </div>
                                        <div v-if="selectedTicket.taken_at" class="mb-3">
                                            <small class="text-muted d-block">Взята в работу</small>
                                            <span class="fw-bold text-warning">{{ new Date(selectedTicket.taken_at).toLocaleString() }}</span>
                                            <div class="small text-muted" v-if="selectedTicket.assigned_to_username">
                                                Исполнитель: {{ selectedTicket.assigned_to_username }}
                                            </div>
                                        </div>
                                        <div v-if="selectedTicket.completed_at" class="mb-3">
                                            <small class="text-muted d-block">Завершена</small>
                                            <span class="fw-bold text-success">{{ new Date(selectedTicket.completed_at).toLocaleString() }}</span>
                                        </div>
                                    </div>

                                    <div v-if="selectedTicket.parts_wait_reason" class="alert alert-info py-2 px-3 mt-3">
                                        <small class="fw-bold d-block">Причина ожидания запчастей:</small>
                                        {{ selectedTicket.parts_wait_reason }}
                                    </div>

                                    <div v-if="selectedTicket.report_comment" class="bg-light p-3 rounded mt-3 border-start border-4 border-success">
                                        <small class="text-success fw-bold d-block mb-1">Финальный комментарий хелпдеска:</small>
                                        {{ selectedTicket.report_comment }}
                                    </div>
                                </div>
                            </div>

                            <!-- Right: Author Info -->
                            <div class="col-md-5">
                                <div class="card border-0 bg-light">
                                    <div class="card-body">
                                        <h6 class="text-muted text-uppercase small fw-bold mb-3">
                                            <i class="bi bi-person-badge me-1"></i>Автор заявки
                                        </h6>
                                        <div v-if="selectedTicket.author_details" class="author-block">
                                            <div class="d-flex align-items-center mb-3">
                                                <div class="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 48px; height: 48px; font-size: 1.2rem;">
                                                    {{ selectedTicket.author_details.full_name ? selectedTicket.author_details.full_name[0] : 'U' }}
                                                </div>
                                                <div class="ms-3">
                                                    <div class="fw-bold">{{ selectedTicket.author_details.full_name || 'Не указано' }}</div>
                                                    <code class="small text-primary">@{{ selectedTicket.author_details.username }}</code>
                                                </div>
                                            </div>
                                            
                                            <div class="mb-2">
                                                <small class="text-muted d-block">Институт / Подразделение</small>
                                                <div class="small fw-bold">{{ selectedTicket.author_details.institute || '-' }}</div>
                                            </div>
                                            <div class="mb-2">
                                                <small class="text-muted d-block">Должность</small>
                                                <div class="small fw-bold">{{ selectedTicket.author_details.position || '-' }}</div>
                                            </div>
                                            <hr class="my-2">
                                            <div class="d-flex justify-content-between align-items-center">
                                                <span class="badge bg-secondary opacity-75">{{ getRoleLabel(selectedTicket.author_details.role) }}</span>
                                                <small class="text-muted" v-if="selectedTicket.author_details.date_joined">с {{ new Date(selectedTicket.author_details.date_joined).toLocaleDateString() }}</small>
                                            </div>
                                        </div>
                                        <div v-else class="text-center py-3 text-muted">
                                            Данные автора недоступны
                                        </div>
                                    </div>
                                </div>

                                <div class="mt-4 text-center">
                                    <h6 class="text-muted text-uppercase small fw-bold mb-2">Статус заявки</h6>
                                    <span class="badge p-2 fs-6 w-100 rounded-pill" :class="getStatusColor(selectedTicket.status)">
                                        {{ getStatusLabel(selectedTicket.status) }}
                                    </span>
                                    <div v-if="selectedTicket.is_overdue" class="badge bg-danger mt-2 w-100">ПРОСРОЧЕНА</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

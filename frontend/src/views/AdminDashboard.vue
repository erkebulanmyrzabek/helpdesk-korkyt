<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from '../axios'
import Clock from '../components/Clock.vue'

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
const corpuses = ref([])
const newUser = ref({
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'teacher',
    corpus_id: null
})
const extendDeadlineData = ref({
    ticketId: null,
    days: 3
})
const visiblePasswords = ref(new Set())
const isCreatingUser = ref(false)

const filters = ref({
    id: '',
    date: '',
    status: '',
    author: '',
    helper: ''
})

const filteredTickets = computed(() => {
    return tickets.value.filter(ticket => {
        // Filter by ID
        if (filters.value.id && !String(ticket.id).includes(filters.value.id)) return false
        
        // Filter by Date (created_at)
        if (filters.value.date) {
            const ticketDate = new Date(ticket.created_at).toISOString().split('T')[0]
            if (ticketDate !== filters.value.date) return false
        }

        // Filter by Status
        if (filters.value.status && ticket.status !== filters.value.status) return false

        // Filter by Author
        if (filters.value.author && !ticket.author_username.toLowerCase().includes(filters.value.author.toLowerCase())) return false

        // Filter by Helper
        if (filters.value.helper) {
            const helper = ticket.assigned_to_username || ''
            if (!helper.toLowerCase().includes(filters.value.helper.toLowerCase())) return false
        }

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

const activeTab = ref('stats') // 'stats' or 'users'

const fetchStats = async () => {
    try {
        const response = await axios.get('tickets/stats/')
        stats.value = response.data
    } catch (error) {
        console.error(error)
    }
}

const fetchTickets = async () => {
    try {
        const response = await axios.get('tickets/')
        tickets.value = response.data
    } catch (error) {
        console.error(error)
    }
}

const fetchUsers = async () => {
    try {
        const response = await axios.get('users/')
        users.value = response.data
    } catch (error) {
        console.error(error)
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

const createUser = async () => {
    if (isCreatingUser.value) return;
    isCreatingUser.value = true;
    try {
        const userData = { ...newUser.value }
        if (userData.role !== 'helpdesk') {
            delete userData.corpus_id
        }
        await axios.post('users/', userData)
        newUser.value = { username: '', email: '', password: '', first_name: '', last_name: '', role: 'teacher', corpus_id: null }
        fetchUsers()
        alert('Пользователь создан')
    } catch (error) {
        console.error(error)
        alert('Ошибка при создании пользователя')
    } finally {
        isCreatingUser.value = false;
    }
}

const deleteUser = async (id) => {
    if (!confirm('Вы уверены, что хотите удалить этого пользователя?')) return
    try {
        await axios.delete(`users/${id}/`)
        fetchUsers()
    } catch (error) {
        alert('Ошибка при удалении')
    }
}

const markUnfixable = async (id) => {
    if (!confirm('Пометить как неисправимую?')) return
    try {
        await axios.post(`tickets/${id}/mark_unfixable/`)
        fetchTickets()
        fetchStats()
    } catch (error) {
        alert('Ошибка')
    }
}

const extendDeadline = async () => {
    try {
        await axios.post(`tickets/${extendDeadlineData.value.ticketId}/extend_deadline/`, {
            days: extendDeadlineData.value.days
        })
        extendDeadlineData.value.ticketId = null
        fetchTickets()
    } catch (error) {
        alert('Ошибка')
    }
}

const getStatusLabel = (status) => {
    const map = {
        'NEW': 'Новая',
        'TRANSIT': 'В пути',
        'IN_PROGRESS': 'В работе',
        'WAITING_APPROVE': 'Ожидает подтверждения',
        'CLOSED': 'Закрыта',
        'UNFIXABLE': 'Неисправима'
    }
    return map[status] || status
}

const getStatusColor = (status) => {
    switch(status) {
        case 'NEW': return 'bg-success';
        case 'TRANSIT': return 'bg-info text-dark';
        case 'IN_PROGRESS': return 'bg-warning text-dark';
        case 'WAITING_APPROVE': return 'bg-primary';
        case 'CLOSED': return 'bg-secondary';
        case 'UNFIXABLE': return 'bg-danger';
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
})
</script>

<template>
    <div class="container-fluid">
        <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
            <div class="d-flex align-items-center gap-3">
                <h2 class="text-primary mb-0"><i class="bi bi-speedometer2 me-2"></i>Панель администратора</h2>
                <Clock />
            </div>
            <div class="btn-group">
                <button class="btn" :class="activeTab === 'stats' ? 'btn-primary' : 'btn-outline-primary'" @click="activeTab = 'stats'">
                    <i class="bi bi-graph-up me-1"></i>Статистика
                </button>
                <button class="btn" :class="activeTab === 'users' ? 'btn-primary' : 'btn-outline-primary'" @click="activeTab = 'users'">
                    <i class="bi bi-people me-1"></i>Пользователи
                </button>
                <router-link to="/admin/reviews" class="btn btn-outline-primary">
                    <i class="bi bi-star me-1"></i>Отзывы
                </router-link>
            </div>
        </div>
        
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
                    <div class="row g-2">
                        <div class="col-md-2">
                            <input type="text" v-model="filters.id" class="form-control form-control-sm" placeholder="Поиск по ID...">
                        </div>
                        <div class="col-md-2">
                            <input type="date" v-model="filters.date" class="form-control form-control-sm">
                        </div>
                        <div class="col-md-2">
                            <select v-model="filters.status" class="form-select form-select-sm">
                                <option value="">Все статусы</option>
                                <option value="NEW">Новая</option>
                                <option value="TRANSIT">В пути</option>
                                <option value="IN_PROGRESS">В работе</option>
                                <option value="WAITING_APPROVE">Ожидает</option>
                                <option value="CLOSED">Закрыта</option>
                                <option value="UNFIXABLE">Неисправима</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <input type="text" v-model="filters.author" class="form-control form-control-sm" placeholder="Автор...">
                        </div>
                        <div class="col-md-3">
                            <input type="text" v-model="filters.helper" class="form-control form-control-sm" placeholder="Исполнитель...">
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
                                <th>Дедлайн</th>
                                <th>Действия</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-if="filteredTickets.length === 0">
                                <td colspan="8" class="text-center py-4 text-muted">Заявки не найдены</td>
                            </tr>
                            <tr v-for="ticket in filteredTickets" :key="ticket.id" :class="{'table-danger': ticket.is_overdue}">
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
                                <td>{{ ticket.author_username }}</td>
                                <td>{{ ticket.assigned_to_username || '-' }}</td>
                                <td>{{ ticket.building }}, {{ ticket.room }}</td>
                                <td>
                                    {{ ticket.deadline ? new Date(ticket.deadline).toLocaleString('ru-RU', { timeZone: 'Asia/Almaty', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '-' }}
                                </td>
                                <td>
                                    <div class="btn-group btn-group-sm">
                                        <button v-if="ticket.status !== 'CLOSED' && ticket.status !== 'UNFIXABLE'" class="btn btn-outline-danger" title="Неисправимо" @click="markUnfixable(ticket.id)">
                                            <i class="bi bi-x-circle"></i>
                                        </button>
                                        <button class="btn btn-outline-warning" title="Продлить дедлайн" @click="extendDeadlineData.ticketId = ticket.id">
                                            <i class="bi bi-clock-history"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Extend Deadline Modal (Simple implementation) -->
            <div v-if="extendDeadlineData.ticketId" class="position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center" style="background: rgba(0,0,0,0.5); z-index: 1000;">
                <div class="card p-4" style="width: 300px;">
                    <h5>Продлить дедлайн</h5>
                    <div class="mb-3">
                        <label>Дней:</label>
                        <input type="number" v-model="extendDeadlineData.days" class="form-control">
                    </div>
                    <div class="d-flex justify-content-end gap-2">
                        <button class="btn btn-secondary" @click="extendDeadlineData.ticketId = null">Отмена</button>
                        <button class="btn btn-primary" @click="extendDeadline">Продлить</button>
                    </div>
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
                                    <label class="form-label small text-muted">Email</label>
                                    <input v-model="newUser.email" type="email" class="form-control" required>
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
                                <div class="mb-3" v-if="newUser.role === 'helpdesk'">
                                    <label class="form-label small text-muted">Корпус</label>
                                    <select v-model="newUser.corpus_id" class="form-select">
                                        <option :value="null">Выберите корпус</option>
                                        <option v-for="corpus in corpuses" :key="corpus.id" :value="corpus.id">{{ corpus.name }}</option>
                                    </select>
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
                                        <th>Корпус</th>
                                        <th>Пароль</th>
                                        <th>Действия</th>
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
                                            <span v-if="user.corpus_name" class="badge bg-info text-white">{{ user.corpus_name }}</span>
                                            <span v-else class="text-muted">-</span>
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
                                        <td>
                                            <button class="btn btn-sm btn-outline-danger" @click="deleteUser(user.id)" v-if="user.username !== 'admin'">
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
    </div>
</template>

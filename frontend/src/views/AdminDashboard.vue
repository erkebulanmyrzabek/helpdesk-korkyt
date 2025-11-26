<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from '../axios'

const stats = ref({
    total: 0,
    by_status: [],
    helpdesk_stats: [],
    teacher_stats: [],
    category_stats: {},
    avg_completion_time_minutes: null
})
const tickets = ref([])
const users = ref([])
const corpuses = ref([])
const newUser = ref({
    username: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'teacher',
    corpus_id: null
})

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
    try {
        const userData = { ...newUser.value }
        if (userData.role !== 'helpdesk') {
            delete userData.corpus_id
        }
        await axios.post('users/', userData)
        newUser.value = { username: '', password: '', first_name: '', last_name: '', role: 'teacher', corpus_id: null }
        fetchUsers()
        alert('Пользователь создан')
    } catch (error) {
        console.error(error)
        alert('Ошибка при создании пользователя')
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

const getStatusLabel = (status) => {
     switch(status) {
        case 'open': return 'Открыто';
        case 'in_progress': return 'В работе';
        case 'done': return 'Выполнено';
        default: return status;
    }
}

const getStatusColor = (status) => {
     switch(status) {
        case 'open': return 'bg-success';
        case 'in_progress': return 'bg-warning text-dark';
        case 'done': return 'bg-secondary';
        default: return 'bg-primary';
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
    <div>
        <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
            <h2 class="text-primary mb-0"><i class="bi bi-speedometer2 me-2"></i>Панель администратора</h2>
            <div class="btn-group">
                <button class="btn" :class="activeTab === 'stats' ? 'btn-primary' : 'btn-outline-primary'" @click="activeTab = 'stats'">
                    <i class="bi bi-graph-up me-1"></i>Статистика
                </button>
                <button class="btn" :class="activeTab === 'users' ? 'btn-primary' : 'btn-outline-primary'" @click="activeTab = 'users'">
                    <i class="bi bi-people me-1"></i>Пользователи
                </button>
            </div>
        </div>
        
        <!-- STATS & TICKETS TAB -->
        <div v-if="activeTab === 'stats'">
            <!-- Main Stats Cards -->
            <div class="row g-4 mb-4">
                <div class="col-md-3">
                    <div class="card bg-gradient-primary text-white h-100 shadow-sm" style="background: linear-gradient(45deg, #002855, #00509d);">
                        <div class="card-body d-flex flex-column justify-content-center align-items-center text-center py-4">
                            <h1 class="display-4 fw-bold mb-0">{{ stats.total }}</h1>
                            <p class="mb-0 opacity-75">Всего заявок</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-success text-white h-100 shadow-sm">
                        <div class="card-body d-flex flex-column justify-content-center align-items-center text-center py-4">
                            <h1 class="display-4 fw-bold mb-0">{{ stats.category_stats?.computers || 0 }}</h1>
                            <p class="mb-0 opacity-75">Компьютеров</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-info text-white h-100 shadow-sm">
                        <div class="card-body d-flex flex-column justify-content-center align-items-center text-center py-4">
                            <h1 class="display-4 fw-bold mb-0">{{ stats.category_stats?.internet || 0 }}</h1>
                            <p class="mb-0 opacity-75">Интернет</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-warning text-dark h-100 shadow-sm">
                        <div class="card-body d-flex flex-column justify-content-center align-items-center text-center py-4">
                            <h1 class="display-4 fw-bold mb-0">{{ formatTime(stats.avg_completion_time_minutes) }}</h1>
                            <p class="mb-0 opacity-75">Среднее время</p>
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
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="hd in stats.helpdesk_stats" :key="hd.id">
                                            <td>{{ hd.first_name || hd.username }}</td>
                                            <td class="text-end">
                                                <span class="badge bg-success">{{ hd.total_tickets || 0 }}</span>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Teacher Stats -->
            <div class="row g-4 mb-4">
                <div class="col-md-12">
                    <div class="card shadow-sm">
                        <div class="card-header bg-white border-bottom">
                            <h5 class="mb-0 text-muted"><i class="bi bi-person-check me-2"></i>Статистика учителей</h5>
                        </div>
                        <div class="card-body">
                            <div v-if="stats.teacher_stats?.length === 0" class="text-center py-4 text-muted">
                                Нет данных
                            </div>
                            <div v-else class="table-responsive">
                                <table class="table table-hover mb-0">
                                    <thead class="table-light">
                                        <tr>
                                            <th>Учитель</th>
                                            <th class="text-center">Всего заявок</th>
                                            <th class="text-center">Выполнено</th>
                                            <th class="text-center">В работе</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="teacher in stats.teacher_stats" :key="teacher.id">
                                            <td>{{ teacher.first_name || teacher.username }}</td>
                                            <td class="text-center">
                                                <span class="badge bg-primary">{{ teacher.total_created || 0 }}</span>
                                            </td>
                                            <td class="text-center">
                                                <span class="badge bg-success">{{ teacher.completed || 0 }}</span>
                                            </td>
                                            <td class="text-center">
                                                <span class="badge bg-warning text-dark">{{ (teacher.total_created || 0) - (teacher.completed || 0) }}</span>
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
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>ID</th>
                                <th>Заголовок</th>
                                <th>Статус</th>
                                <th>Автор</th>
                                <th>Исполнитель</th>
                                <th>Место</th>
                                <th>Время выполнения</th>
                                <th>Дата</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="ticket in tickets" :key="ticket.id">
                                <td>#{{ ticket.id }}</td>
                                <td>
                                    <div class="fw-bold">{{ ticket.title }}</div>
                                    <small class="text-muted text-truncate d-block" style="max-width: 200px;">{{ ticket.description }}</small>
                                </td>
                                <td>
                                    <span class="badge rounded-pill" :class="getStatusColor(ticket.status)">
                                        {{ getStatusLabel(ticket.status) }}
                                    </span>
                                </td>
                                <td>{{ ticket.author_username }}</td>
                                <td>{{ ticket.assigned_to_username || '-' }}</td>
                                <td>{{ ticket.corpus_name || ticket.corpus }}, {{ ticket.cabinet }}</td>
                                <td>
                                    <small v-if="ticket.duration_minutes" class="text-muted">
                                        {{ formatTime(ticket.duration_minutes) }}
                                    </small>
                                    <small v-else class="text-muted">-</small>
                                </td>
                                <td>{{ new Date(ticket.created_at).toLocaleDateString() }}</td>
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
                                <div class="mb-3" v-if="newUser.role === 'helpdesk'">
                                    <label class="form-label small text-muted">Корпус</label>
                                    <select v-model="newUser.corpus_id" class="form-select">
                                        <option :value="null">Выберите корпус</option>
                                        <option v-for="corpus in corpuses" :key="corpus.id" :value="corpus.id">{{ corpus.name }}</option>
                                    </select>
                                </div>
                                <button type="submit" class="btn btn-primary w-100">Создать</button>
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

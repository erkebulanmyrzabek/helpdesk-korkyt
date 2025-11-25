<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from '../axios'

const stats = ref({
    total: 0,
    by_status: []
})
const tickets = ref([])
const users = ref([])
const newUser = ref({
    username: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'teacher'
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

const createUser = async () => {
    try {
        await axios.post('users/', newUser.value)
        newUser.value = { username: '', password: '', first_name: '', last_name: '', role: 'teacher' }
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

onMounted(() => {
    fetchStats()
    fetchTickets()
    fetchUsers()
})
</script>

<template>
    <div>
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="text-primary mb-0"><i class="bi bi-speedometer2 me-2"></i>Панель администратора</h2>
            <div class="btn-group">
                <button class="btn" :class="activeTab === 'stats' ? 'btn-primary' : 'btn-outline-primary'" @click="activeTab = 'stats'">
                    <i class="bi bi-graph-up me-1"></i>Статистика и Заявки
                </button>
                <button class="btn" :class="activeTab === 'users' ? 'btn-primary' : 'btn-outline-primary'" @click="activeTab = 'users'">
                    <i class="bi bi-people me-1"></i>Пользователи
                </button>
            </div>
        </div>
        
        <!-- STATS & TICKETS TAB -->
        <div v-if="activeTab === 'stats'">
            <div class="row g-4 mb-4">
                <div class="col-md-4">
                    <div class="card bg-gradient-primary text-white h-100 shadow-sm" style="background: linear-gradient(45deg, #002855, #00509d);">
                        <div class="card-body d-flex flex-column justify-content-center align-items-center text-center py-5">
                            <h1 class="display-1 fw-bold mb-0">{{ stats.total }}</h1>
                            <p class="lead opacity-75">Всего заявок</p>
                        </div>
                    </div>
                </div>
                 <div class="col-md-8">
                    <div class="card shadow-sm h-100">
                        <div class="card-header bg-white border-bottom">
                             <h5 class="mb-0 text-muted">Распределение по статусам</h5>
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
            </div>

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
                                <td>{{ ticket.corpus }}, {{ ticket.cabinet }}</td>
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

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import axios from '../axios'
import { useAuthStore } from '../stores/auth'

const tickets = ref([])
const authStore = useAuthStore()
const reportData = ref({
    id: null,
    comment: '',
    media_after: null
})
const commentData = ref({
    id: null,
    text: ''
})
const currentTime = ref(new Date())
let timerInterval = null

const fetchTickets = async () => {
    try {
        const response = await axios.get('tickets/')
        tickets.value = response.data
    } catch (e) {
        console.error(e)
    }
}

const checkIn = async () => {
    try {
        const response = await axios.post('users/check_in/')
        authStore.user.is_checked_in = response.data.is_checked_in
        fetchTickets() // Refresh tickets based on new status
    } catch (e) {
        console.error(e)
    }
}

const openTickets = computed(() => tickets.value.filter(t => t.status === 'NEW'))
const myTickets = computed(() => tickets.value.filter(t => t.assigned_to === authStore.user.id && ['TRANSIT', 'IN_PROGRESS'].includes(t.status)))
const waitingTickets = computed(() => tickets.value.filter(t => t.assigned_to === authStore.user.id && t.status === 'WAITING_APPROVE'))
const completedTickets = computed(() => tickets.value.filter(t => t.assigned_to === authStore.user.id && t.status === 'CLOSED'))

const getTransitTime = (ticket) => {
    if (!ticket.taken_at) return '00:00'
    // Deadline for transit is taken_at + 10 mins? Requirement said "Calculate remaining time: (taken_at + 10 minutes) - now"
    const taken = new Date(ticket.taken_at)
    const deadline = new Date(taken.getTime() + 10 * 60000)
    const now = currentTime.value
    const diff = Math.floor((deadline - now) / 1000)
    
    if (diff <= 0) return 'Прибытие'
    
    const mins = Math.floor(diff / 60)
    const secs = diff % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
}

const takeTicket = async (id) => {
    try {
        await axios.post(`tickets/${id}/take/`)
        fetchTickets()
    } catch (error) {
        alert(error.response?.data?.error || 'Ошибка')
    }
}

const arrive = async (id) => {
    try {
        await axios.post(`tickets/${id}/arrive/`)
        fetchTickets()
    } catch (error) {
        alert(error.response?.data?.error || 'Ошибка')
    }
}

const addComment = async () => {
    try {
        await axios.post(`tickets/${commentData.value.id}/add_comment/`, {
            comment: commentData.value.text
        })
        commentData.value.id = null
        commentData.value.text = ''
        fetchTickets()
    } catch (error) {
        alert(error.response?.data?.error || 'Ошибка')
    }
}

const handleReportImage = (event) => {
    reportData.value.media_after = event.target.files[0]
}

const submitReport = async () => {
    const formData = new FormData()
    if (reportData.value.comment) formData.append('report_comment', reportData.value.comment) // Optional now? Requirement said comment for feedback, but here maybe optional.
    if (reportData.value.media_after) formData.append('media_after', reportData.value.media_after)

    try {
        await axios.post(`tickets/${reportData.value.id}/complete/`, formData, {
             headers: { 'Content-Type': 'multipart/form-data' }
        })
        reportData.value.id = null
        fetchTickets()
    } catch (error) {
        alert(error.response?.data?.error || 'Ошибка')
    }
}

onMounted(() => {
    fetchTickets()
    timerInterval = setInterval(() => {
        currentTime.value = new Date()
    }, 1000)
})

onUnmounted(() => {
    if (timerInterval) clearInterval(timerInterval)
})
</script>

<template>
    <div class="container-fluid">
        <!-- Check-in Status -->
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h3>Панель Хелпдеска</h3>
            <button 
                class="btn" 
                :class="authStore.user.is_checked_in ? 'btn-success' : 'btn-secondary'"
                @click="checkIn"
            >
                <i class="bi" :class="authStore.user.is_checked_in ? 'bi-toggle-on' : 'bi-toggle-off'"></i>
                {{ authStore.user.is_checked_in ? 'На смене' : 'Не на смене' }}
            </button>
        </div>

        <div v-if="!authStore.user.is_checked_in" class="alert alert-warning text-center">
            Вы не на смене. Нажмите кнопку выше, чтобы видеть заявки.
        </div>

        <div v-else class="row">
            <!-- New Tickets -->
            <div class="col-md-4">
                <div class="card shadow-sm h-100">
                    <div class="card-header bg-white text-primary border-bottom d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">Новые заявки</h5>
                        <span class="badge bg-primary rounded-pill">{{ openTickets.length }}</span>
                    </div>
                    <div class="card-body p-0">
                        <div v-if="openTickets.length === 0" class="text-center py-5 text-muted">
                            Нет новых заявок
                        </div>
                        <div v-else class="list-group list-group-flush">
                            <div v-for="ticket in openTickets" :key="ticket.id" class="list-group-item p-3" :class="{'bg-danger bg-opacity-10': ticket.is_overdue}">
                                <div class="d-flex w-100 justify-content-between mb-2">
                                    <h6 class="mb-1 fw-bold">{{ ticket.title }}</h6>
                                    <span v-if="ticket.is_overdue" class="badge bg-danger">ПРОСРОЧЕНО</span>
                                </div>
                                <p class="mb-2 text-secondary small">{{ ticket.description }}</p>
                                <div class="small text-muted mb-2">
                                    <i class="bi bi-building"></i> {{ ticket.building }} | 
                                    <i class="bi bi-door-closed"></i> {{ ticket.room }} <!-- Should be masked by API -->
                                </div>
                                <div v-if="ticket.media_before">
                                    <a :href="ticket.media_before" target="_blank" class="btn btn-sm btn-outline-info">Медиа</a>
                                </div>
                                <button class="btn btn-sm btn-primary w-100 mt-2" @click="takeTicket(ticket.id)">
                                    Взять в работу
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- My Active Tickets -->
            <div class="col-md-4">
                <div class="card shadow-sm h-100">
                    <div class="card-header bg-warning text-dark border-bottom d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">В работе</h5>
                        <span class="badge bg-dark text-white rounded-pill">{{ myTickets.length }}</span>
                    </div>
                    <div class="card-body p-0">
                        <div v-for="ticket in myTickets" :key="ticket.id" class="list-group-item p-3">
                            <h6 class="fw-bold">{{ ticket.title }}</h6>
                            <div class="small text-muted mb-2">
                                {{ ticket.building }}, {{ ticket.room }} ({{ ticket.status }})
                            </div>
                            
                            <!-- Transit Timer -->
                            <div v-if="ticket.status === 'TRANSIT'" class="alert alert-info py-1 mb-2">
                                <i class="bi bi-stopwatch"></i> Прибытие через: <strong>{{ getTransitTime(ticket) }}</strong>
                            </div>

                            <!-- Actions -->
                            <div class="d-flex gap-2 mt-2">
                                <button v-if="ticket.status === 'TRANSIT'" class="btn btn-sm btn-primary" @click="arrive(ticket.id)">
                                    Прибыл на место
                                </button>
                                <button v-else class="btn btn-sm btn-outline-secondary" @click="commentData.id = ticket.id">
                                    Комментарий
                                </button>
                                <button class="btn btn-sm btn-success" @click="reportData.id = ticket.id">
                                    Завершить
                                </button>
                            </div>

                            <!-- Comment Form -->
                            <div v-if="commentData.id === ticket.id && ticket.status !== 'TRANSIT'" class="mt-2">
                                <textarea v-model="commentData.text" class="form-control form-control-sm mb-1" placeholder="Комментарий (продлит дедлайн)"></textarea>
                                <button class="btn btn-sm btn-primary" @click="addComment">Отправить</button>
                            </div>

                            <!-- Finish Form -->
                            <div v-if="reportData.id === ticket.id" class="mt-2">
                                <input type="file" @change="handleReportImage" class="form-control form-control-sm mb-1" accept="image/*">
                                <textarea v-model="reportData.comment" class="form-control form-control-sm mb-1" placeholder="Комментарий (опционально)"></textarea>
                                <button class="btn btn-sm btn-success w-100" @click="submitReport">Отправить отчет</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Waiting Approval / Closed -->
            <div class="col-md-4">
                <div class="card shadow-sm h-100">
                    <div class="card-header bg-success text-white border-bottom">
                        <h5 class="mb-0">История / Ожидание</h5>
                    </div>
                    <div class="card-body p-0">
                        <div v-for="ticket in waitingTickets" :key="ticket.id" class="list-group-item p-3 bg-light">
                            <h6 class="text-muted">{{ ticket.title }}</h6>
                            <span class="badge bg-warning text-dark">Ожидает подтверждения</span>
                        </div>
                        <div v-for="ticket in completedTickets" :key="ticket.id" class="list-group-item p-3">
                            <h6 class="text-muted text-decoration-line-through">{{ ticket.title }}</h6>
                            <span class="badge bg-success">Закрыто</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

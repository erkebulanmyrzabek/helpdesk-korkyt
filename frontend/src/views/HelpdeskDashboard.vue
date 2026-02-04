<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import axios from '../axios'
import { useAuthStore } from '../stores/auth'
import Clock from '../components/Clock.vue'

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

const fetchTickets = async () => {
    try {
        const response = await axios.get('tickets/')
        tickets.value = response.data
    } catch (e) {
        console.error(e)
    }
}



const openTickets = computed(() => tickets.value.filter(t => t.status === 'NEW'))
const myTickets = computed(() => {
    if (!authStore.user) return []
    return tickets.value.filter(t => t.assigned_to === authStore.user.id && t.status === 'IN_PROGRESS')
})
const completedTickets = computed(() => {
    if (!authStore.user) return []
    return tickets.value.filter(t => t.assigned_to === authStore.user.id && t.status === 'CLOSED')
})

const takeTicket = async (id) => {
    try {
        await axios.post(`tickets/${id}/take/`)
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
    if (!reportData.value.comment) {
        alert('Отчет о выполнении (комментарий) обязателен.')
        return
    }
    const formData = new FormData()
    formData.append('report_comment', reportData.value.comment)
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
})


</script>

<template>
    <div class="container-fluid">
        <div class="d-flex justify-content-between align-items-center mb-4">
             <div class="d-flex align-items-center gap-3">
                <h3>Панель Хелпдеска</h3>
                <Clock />
            </div>
        </div>

        <div class="row">
            <!-- New Tickets -->
            <div class="col-md-4">
                <div class="card shadow-sm h-100">
                    <div class="card-header bg-white text-primary border-bottom d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">Новые заявки</h5>
                        <span class="badge bg-primary rounded-pill">{{ openTickets.length }}</span>
                    </div>
                    <div class="card-body p-0" style="max-height: 70vh; overflow-y: auto;">
                        <div v-if="openTickets.length === 0" class="text-center py-5 text-muted">
                            Нет новых заявок
                        </div>
                        <div v-else class="list-group list-group-flush">
                            <div v-for="ticket in openTickets" :key="ticket.id" class="list-group-item p-3" :class="{'bg-danger bg-opacity-10': ticket.is_overdue}">
                                <div class="d-flex w-100 justify-content-between mb-2">
                                    <h6 class="mb-1 fw-bold">#{{ ticket.id }} {{ ticket.title }}</h6>
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
                    <div class="card-body p-0" style="max-height: 70vh; overflow-y: auto;">
                        <div v-for="ticket in myTickets" :key="ticket.id" class="list-group-item p-3">
                            <h6 class="fw-bold">#{{ ticket.id }} {{ ticket.title }}</h6>
                            <div class="small text-muted mb-2">
                                {{ ticket.building }}, {{ ticket.room }} ({{ ticket.status }})
                            </div>
                            


                            <!-- Actions -->
                            <div class="d-flex gap-2 mt-2">
                                <button class="btn btn-sm btn-outline-secondary" @click="commentData.id = ticket.id">
                                    Комментарий
                                </button>
                                <button class="btn btn-sm btn-success" @click="reportData.id = ticket.id">
                                    Завершить
                                </button>
                            </div>

                            <!-- Comment Form -->
                            <div v-if="commentData.id === ticket.id" class="mt-2">
                                <textarea v-model="commentData.text" class="form-control form-control-sm mb-1" placeholder="Комментарий (продлит дедлайн)"></textarea>
                                <button class="btn btn-sm btn-primary" @click="addComment">Отправить</button>
                            </div>

                            <!-- Finish Form -->
                            <div v-if="reportData.id === ticket.id" class="mt-2">
                                <div class="form-text small mb-1">Фото (по желанию):</div>
                                <input type="file" @change="handleReportImage" class="form-control form-control-sm mb-1" accept="image/*">
                                <textarea v-model="reportData.comment" class="form-control form-control-sm mb-1" placeholder="Комментарий к выполнению" required></textarea>
                                <button class="btn btn-sm btn-success w-100" @click="submitReport">Отправить отчет</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Closed -->
            <div class="col-md-4">
                <div class="card shadow-sm h-100">
                    <div class="card-header bg-success text-white border-bottom">
                        <h5 class="mb-0">История</h5>
                    </div>
                    <div class="card-body p-0" style="max-height: 70vh; overflow-y: auto;">
                        <div v-for="ticket in completedTickets" :key="ticket.id" class="list-group-item p-3">
                            <h6 class="text-muted text-decoration-line-through">#{{ ticket.id }} {{ ticket.title }}</h6>
                            <span class="badge bg-success mb-2">Закрыто</span>
                            
                            <div v-if="ticket.feedback" class="p-2 rounded" style="background-color: #e9ecef;">
                                <div class="d-flex justify-content-between align-items-center mb-1">
                                    <small class="fw-bold text-primary">Отзыв пользователя</small>
                                    <span class="text-warning small">
                                        <i v-for="n in 5" :key="n" class="bi" :class="n <= ticket.feedback.rating ? 'bi-star-fill' : 'bi-star'"></i>
                                    </span>
                                </div>
                                <p class="mb-0 small text-dark fst-italic">"{{ ticket.feedback.comment || 'Без комментария' }}"</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

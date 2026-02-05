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
    return tickets.value.filter(t => t.assigned_to === authStore.user.id && (t.status === 'IN_PROGRESS' || t.status === 'WAITING_FOR_PARTS'))
})
const completedTickets = computed(() => {
    if (!authStore.user) return []
    return tickets.value.filter(t => t.assigned_to === authStore.user.id && (t.status === 'CLOSED' || t.status === 'UNFIXABLE' || t.status === 'CANCELED'))
})

const getStatusText = (status) => {
    const map = {
        'NEW': 'Новая',
        'IN_PROGRESS': 'В работе',
        'WAITING_FOR_PARTS': 'Ожидается запчасть',
        'WAITING_APPROVE': 'Ожидает подтверждения',
        'CLOSED': 'Закрыта',
        'UNFIXABLE': 'Неисправима',
        'CANCELED': 'Отменена'
    }
    return map[status] || status
}

const getStatusBadgeClass = (status) => {
    switch(status) {
        case 'NEW': return 'badge bg-success';
        case 'IN_PROGRESS': return 'badge bg-warning text-dark';
        case 'WAITING_FOR_PARTS': return 'badge bg-info text-dark';
        case 'WAITING_APPROVE': return 'badge bg-primary';
        case 'CLOSED': return 'badge bg-secondary';
        case 'UNFIXABLE': return 'badge bg-danger';
        case 'CANCELED': return 'badge bg-dark';
        default: return 'badge bg-light text-dark';
    }
}

const needPartsData = ref({
    id: null,
    comment: ''
})

const takeTicket = async (id) => {
    try {
        await axios.post(`tickets/${id}/take/`)
        fetchTickets()
    } catch (error) {
        alert(error.response?.data?.error || 'Ошибка')
    }
}





const submitNeedParts = async () => {
    if (!needPartsData.value.comment) {
        alert('Комментарий обязателен')
        return
    }
    try {
        await axios.post(`tickets/${needPartsData.value.id}/need-parts/`, {
            comment: needPartsData.value.comment
        })
        needPartsData.value.id = null
        needPartsData.value.comment = ''
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
                                {{ ticket.building }}, {{ ticket.room }} 
                                <span :class="getStatusBadgeClass(ticket.status)">{{ getStatusText(ticket.status) }}</span>
                            </div>
                            

                            <!-- Actions -->
                            <div class="d-flex gap-2 mt-2 flex-wrap">

                                <button v-if="ticket.status !== 'WAITING_FOR_PARTS'" class="btn btn-sm btn-dark" @click="needPartsData.id = ticket.id">
                                    ⏳ Требуется запчасть
                                </button>
                                <button class="btn btn-sm btn-success" @click="reportData.id = ticket.id">
                                    Завершить
                                </button>
                            </div>


                            
                            <!-- Need Parts Form -->
                            <div v-if="needPartsData.id === ticket.id" class="mt-2 text-start p-2 bg-light rounded border border-warning">
                                <small class="fw-bold text-dark d-block mb-1">Запрос запчастей:</small>
                                <textarea v-model="needPartsData.comment" class="form-control form-control-sm mb-1" placeholder="Какая запчасть требуется? (Обязательно)" required></textarea>
                                <button class="btn btn-sm btn-secondary me-1" @click="needPartsData.id = null">Отмена</button>
                                <button class="btn btn-sm btn-warning" @click="submitNeedParts">Отправить запрос</button>
                            </div>

                            <!-- Finish Form -->
                            <div v-if="reportData.id === ticket.id" class="mt-2 text-start p-2 bg-light rounded border border-success">
                                <div class="form-text small mb-1">Фото (по желанию):</div>
                                <input type="file" @change="handleReportImage" class="form-control form-control-sm mb-1" accept="image/*">
                                <textarea v-model="reportData.comment" class="form-control form-control-sm mb-1" placeholder="Комментарий к выполнению (необязательно)"></textarea>
                                <button class="btn btn-sm btn-secondary me-1" @click="reportData.id = null">Отмена</button>
                                <button class="btn btn-sm btn-success" @click="submitReport">Отправить отчет</button>
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
                            <span :class="getStatusBadgeClass(ticket.status) + ' mb-2'">{{ getStatusText(ticket.status) }}</span>
                            
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

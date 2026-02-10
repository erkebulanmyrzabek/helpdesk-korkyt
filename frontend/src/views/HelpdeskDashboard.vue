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

const assistOffers = ref([])
const helpdeskUsers = ref([])
const assistantModal = ref({
    show: false,
    ticketId: null,
    search: '',
    isLoading: false
})

const currentTime = ref(new Date())

const selectedAuthor = ref(null)
const isLoadingAuthor = ref(false)

const fetchTickets = async () => {
    try {
        const response = await axios.get('tickets/')
        tickets.value = response.data
    } catch (e) {
        console.error(e)
    }
}

const fetchOffers = async () => {
    try {
        const response = await axios.get('assist-offers/?status=PENDING')
        assistOffers.value = response.data
    } catch (e) {
        console.error(e)
    }
}

const fetchHelpdeskUsers = async () => {
    try {
        const response = await axios.get('users/?role=helpdesk')
        helpdeskUsers.value = response.data.filter(u => u.role === 'helpdesk')
    } catch (e) {
        console.error(e)
    }
}



const openTickets = computed(() => tickets.value.filter(t => t.status === 'NEW'))
const myTickets = computed(() => {
    if (!authStore.user) return []
    return tickets.value.filter(t => 
        (t.assigned_to === authStore.user.id || (t.assistants && t.assistants.includes(authStore.user.id))) && 
        (t.status === 'IN_PROGRESS' || t.status === 'WAITING_FOR_PARTS')
    )
})
const completedTickets = computed(() => {
    if (!authStore.user) return []
    return tickets.value.filter(t => t.assigned_to === authStore.user.id && (t.status === 'CLOSED' || t.status === 'CANCELED'))
})

const getStatusText = (status) => {
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

const getStatusBadgeClass = (status) => {
    switch(status) {
        case 'NEW': return 'badge bg-success';
        case 'IN_PROGRESS': return 'badge bg-warning text-dark';
        case 'WAITING_FOR_PARTS': return 'badge bg-info text-dark';
        case 'WAITING_APPROVE': return 'badge bg-primary';
        case 'CLOSED': return 'badge bg-secondary';
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

const getRoleLabel = (role) => {
    switch(role) {
        case 'teacher': return 'Учитель';
        case 'helpdesk': return 'Хелпдеск';
        case 'admin': return 'Администратор';
        default: return role;
    }
}

const viewAuthorDetails = async (userId) => {
    if (!userId) return
    isLoadingAuthor.value = true
    try {
        const response = await axios.get(`users/${userId}/details/`)
        selectedAuthor.value = response.data
    } catch (error) {
        alert('Ошибка при загрузке данных автора')
        console.error(error)
    } finally {
        isLoadingAuthor.value = false
    }
}

const openAssistantModal = (ticketId) => {
    assistantModal.value.ticketId = ticketId
    assistantModal.value.show = true
    assistantModal.value.search = ''
    fetchHelpdeskUsers()
}

const closeAssistantModal = () => {
    assistantModal.value.show = false
    assistantModal.value.ticketId = null
}

const filteredHelpdeskUsers = computed(() => {
    const search = assistantModal.value.search.toLowerCase()
    const ticket = tickets.value.find(t => t.id === assistantModal.value.ticketId)
    if (!ticket) return []

    const currentAssistants = (ticket.assistants || [])
    const pendingOfferIds = (ticket.pending_offers || [])

    return helpdeskUsers.value.filter(u => {
        const fullName = (u.full_name || '').toLowerCase()
        const username = (u.username || '').toLowerCase()
        const isSelf = u.id === authStore.user.id
        const isAlreadyAssistant = currentAssistants.includes(u.id)
        const hasPendingOffer = pendingOfferIds.includes(u.id)

        return (fullName.includes(search) || username.includes(search)) && !isSelf && !isAlreadyAssistant && !hasPendingOffer
    })
})

const sendAssistOffer = async (toHelpdeskId) => {
    try {
        await axios.post(`tickets/${assistantModal.value.ticketId}/assist-offers/`, {
            to_helpdesk_id: toHelpdeskId
        })
        alert('Предложение отправлено')
        closeAssistantModal()
    } catch (error) {
        alert(error.response?.data?.error || 'Ошибка при отправке предложения')
    }
}

const acceptOffer = async (offerId) => {
    try {
        await axios.post(`assist-offers/${offerId}/accept/`)
        fetchOffers()
        fetchTickets()
    } catch (error) {
        alert(error.response?.data?.error || 'Ошибка')
    }
}

const declineOffer = async (offerId) => {
    try {
        await axios.post(`assist-offers/${offerId}/decline/`)
        fetchOffers()
    } catch (error) {
        alert(error.response?.data?.error || 'Ошибка')
    }
}

const closeAuthorModal = () => {
    selectedAuthor.value = null
}

onMounted(() => {
    fetchTickets()
    fetchOffers()
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

        <div class="row g-3">
            <!-- New Tickets -->
            <div class="col-xl-3 col-md-6">
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
                                <div class="small fw-bold text-primary mb-1 author-link" @click="viewAuthorDetails(ticket.author)" style="cursor: pointer;">
                                    <i class="bi bi-person"></i> {{ ticket.author_full_name || ticket.author_username }}
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
            <div class="col-xl-3 col-md-6">
                <div class="card shadow-sm h-100">
                    <div class="card-header bg-warning text-dark border-bottom d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">В работе</h5>
                        <span class="badge bg-dark text-white rounded-pill">{{ myTickets.length }}</span>
                    </div>
                    <div class="card-body p-0" style="max-height: 70vh; overflow-y: auto;">
                        <div v-for="ticket in myTickets" :key="ticket.id" class="list-group-item p-3">
                            <h6 class="fw-bold">#{{ ticket.id }} {{ ticket.title }}</h6>
                            <div class="small text-primary fw-bold mb-1 author-link" @click="viewAuthorDetails(ticket.author)" style="cursor: pointer;">
                                <i class="bi bi-person"></i> {{ ticket.author_full_name || ticket.author_username }}
                            </div>
                            <div class="small text-muted mb-2">
                                {{ ticket.building }}, {{ ticket.room }} 
                                <span :class="getStatusBadgeClass(ticket.status)">{{ getStatusText(ticket.status) }}</span>
                            </div>
                            

                            <!-- Actions -->
                            <div class="d-flex gap-2 mt-2 flex-wrap">

                                <button v-if="ticket.status !== 'WAITING_FOR_PARTS' && ticket.assigned_to === authStore.user.id" class="btn btn-sm btn-dark" @click="needPartsData.id = ticket.id">
                                    ⏳ Требуется запчасть
                                </button>
                                <button v-if="ticket.assigned_to === authStore.user.id && (!ticket.assistants_details || ticket.assistants_details.length === 0) && (!ticket.pending_offers || ticket.pending_offers.length === 0)" class="btn btn-sm btn-outline-primary" @click="openAssistantModal(ticket.id)">
                                    ➕ Добавить помощника
                                </button>
                                <button class="btn btn-sm btn-success" @click="reportData.id = ticket.id">
                                    Завершить
                                </button>
                            </div>

                            <!-- Assistants list -->
                            <div v-if="ticket.assistants_details && ticket.assistants_details.length > 0" class="mt-2">
                                <small class="text-muted d-block mb-1">Помощники:</small>
                                <div class="d-flex flex-wrap gap-1">
                                    <span v-for="asst in ticket.assistants_details" :key="asst.id" class="badge bg-light text-dark border">
                                        {{ asst.full_name || asst.username }}
                                    </span>
                                </div>
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

            <!-- Offers -->
            <div class="col-xl-3 col-md-6">
                <div class="card shadow-sm h-100">
                    <div class="card-header bg-info text-dark border-bottom d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">Предложения</h5>
                        <span class="badge bg-dark text-white rounded-pill">{{ assistOffers.length }}</span>
                    </div>
                    <div class="card-body p-0" style="max-height: 70vh; overflow-y: auto;">
                        <div v-if="assistOffers.length === 0" class="text-center py-5 text-muted">
                            Нет предложений
                        </div>
                        <div v-else class="list-group list-group-flush">
                            <div v-for="offer in assistOffers" :key="offer.id" class="list-group-item p-3">
                                <div class="d-flex justify-content-between mb-1">
                                    <h6 class="fw-bold mb-0">#{{ offer.ticket_details.id }} {{ offer.ticket_details.title }}</h6>
                                </div>
                                <div class="small text-muted mb-2">
                                    От: <span class="fw-bold text-primary">{{ offer.from_helpdesk_details.full_name || offer.from_helpdesk_details.username }}</span>
                                </div>
                                <div class="small text-muted mb-2">
                                    {{ offer.ticket_details.building }}, {{ offer.ticket_details.room }}
                                </div>
                                <div class="d-flex gap-2">
                                    <button class="btn btn-sm btn-success flex-grow-1" @click="acceptOffer(offer.id)">Принять</button>
                                    <button class="btn btn-sm btn-outline-danger flex-grow-1" @click="declineOffer(offer.id)">Отклонить</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Closed -->
            <div class="col-xl-3 col-md-6">
                <div class="card shadow-sm h-100">
                    <div class="card-header bg-success text-white border-bottom">
                        <h5 class="mb-0">История</h5>
                    </div>
                    <div class="card-body p-0" style="max-height: 70vh; overflow-y: auto;">
                        <div v-for="ticket in completedTickets" :key="ticket.id" class="list-group-item p-3">
                            <h6 class="text-muted text-decoration-line-through">#{{ ticket.id }} {{ ticket.title }}</h6>
                            <div class="small text-muted mb-1 author-link" @click="viewAuthorDetails(ticket.author)" style="cursor: pointer;">
                                <i class="bi bi-person"></i> {{ ticket.author_full_name || ticket.author_username }}
                            </div>
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

        <!-- ASSISTANT SELECTION MODAL -->
        <div v-if="assistantModal.show" class="modal-backdrop fade show"></div>
        <div v-if="assistantModal.show" class="modal fade show d-block" tabindex="-1" @click.self="closeAssistantModal">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header">
                        <h5 class="modal-title">Выберите помощника</h5>
                        <button type="button" class="btn-close" @click="closeAssistantModal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <input v-model="assistantModal.search" type="text" class="form-control" placeholder="Поиск по имени или логину...">
                        </div>
                        <div class="list-group list-group-flush" style="max-height: 300px; overflow-y: auto;">
                            <div v-for="user in filteredHelpdeskUsers" :key="user.id" class="list-group-item d-flex justify-content-between align-items-center">
                                <div>
                                    <div class="fw-bold">{{ user.full_name }}</div>
                                    <small class="text-muted">@{{ user.username }}</small>
                                </div>
                                <button class="btn btn-sm btn-primary" @click="sendAssistOffer(user.id)">Пригласить</button>
                            </div>
                            <div v-if="filteredHelpdeskUsers.length === 0" class="text-center py-3 text-muted">
                                Помощники не найдены
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" @click="closeAssistantModal">Закрыть</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- AUTHOR INFO MODAL -->
        <div v-if="selectedAuthor" class="modal-backdrop fade show"></div>
        <div v-if="selectedAuthor" class="modal fade show d-block" tabindex="-1" @click.self="closeAuthorModal">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-light border-bottom-0 pb-0">
                        <button type="button" class="btn-close" @click="closeAuthorModal"></button>
                    </div>
                    <div class="modal-body pt-0 text-center">
                        <div class="author-avatar mb-3 d-inline-block">
                            <div class="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center mx-auto" style="width: 80px; height: 80px; font-size: 2rem;">
                                {{ selectedAuthor.full_name ? selectedAuthor.full_name[0] : selectedAuthor.username[0].toUpperCase() }}
                            </div>
                        </div>
                        <h4 class="fw-bold mb-1">{{ selectedAuthor.full_name || 'Не указано' }}</h4>
                        <code class="text-primary mb-4 d-block fs-5">@{{ selectedAuthor.username }}</code>

                        <div class="row g-3 text-start">
                            <div class="col-12 p-3 bg-light rounded-3 mb-2">
                                <div class="row">
                                    <div class="col-6 mb-3">
                                        <small class="text-muted d-block text-uppercase fw-bold" style="font-size: 0.7rem;">Институт</small>
                                        <div class="fw-bold">{{ selectedAuthor.institute || '-' }}</div>
                                    </div>
                                    <div class="col-6 mb-3">
                                        <small class="text-muted d-block text-uppercase fw-bold" style="font-size: 0.7rem;">Должность</small>
                                        <div class="fw-bold">{{ selectedAuthor.position || '-' }}</div>
                                    </div>
                                    <div class="col-6">
                                        <small class="text-muted d-block text-uppercase fw-bold" style="font-size: 0.7rem;">Роль</small>
                                        <span class="badge bg-secondary">{{ getRoleLabel(selectedAuthor.role) }}</span>
                                    </div>
                                    <div class="col-6">
                                        <small class="text-muted d-block text-uppercase fw-bold" style="font-size: 0.7rem;">Регистрация</small>
                                        <div class="fw-bold small">{{ selectedAuthor.date_joined ? new Date(selectedAuthor.date_joined).toLocaleDateString() : '-' }}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <button class="btn btn-outline-secondary w-100 mt-3" @click="closeAuthorModal">Закрыть</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Loading Overlay -->
        <div v-if="isLoadingAuthor" class="modal-backdrop fade show d-flex align-items-center justify-content-center" style="z-index: 2000;">
            <div class="spinner-border text-light" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    </div>
</template>

<style scoped>
.author-link:hover {
    text-decoration: underline !important;
    opacity: 0.8;
}
</style>

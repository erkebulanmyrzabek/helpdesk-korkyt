<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from '../axios'
import { useAuthStore } from '../stores/auth'

const tickets = ref([])
const authStore = useAuthStore()
const reportData = ref({
    id: null,
    comment: '',
    image: null
})
const fileInputReport = ref(null)

const fetchTickets = async () => {
    const response = await axios.get('tickets/')
    tickets.value = response.data
}

const openTickets = computed(() => tickets.value.filter(t => t.status === 'open'))
const myTickets = computed(() => tickets.value.filter(t => t.assigned_to === authStore.user.id && t.status !== 'done'))
const completedTickets = computed(() => tickets.value.filter(t => t.assigned_to === authStore.user.id && t.status === 'done'))

const takeTicket = async (id) => {
    try {
        await axios.post(`tickets/${id}/take/`)
        fetchTickets()
    } catch (error) {
        alert('Ошибка')
    }
}

const prepareReport = (ticket) => {
    reportData.value.id = ticket.id
    reportData.value.comment = ''
    reportData.value.image = null
}

const handleReportImage = (event) => {
    reportData.value.image = event.target.files[0]
}

const submitReport = async () => {
    const formData = new FormData()
    formData.append('report_comment', reportData.value.comment)
    if (reportData.value.image) formData.append('report_image', reportData.value.image)

    try {
        await axios.post(`tickets/${reportData.value.id}/complete/`, formData, {
             headers: { 'Content-Type': 'multipart/form-data' }
        })
        reportData.value.id = null
        fetchTickets()
    } catch (error) {
        alert('Ошибка')
    }
}

onMounted(fetchTickets)
</script>

<template>
    <div>
        <div class="row mb-4">
            <!-- Свободные заявки -->
            <div class="col-md-4">
                <div class="card shadow-sm h-100">
                    <div class="card-header bg-white text-primary border-bottom d-flex justify-content-between align-items-center">
                        <h5 class="mb-0"><i class="bi bi-inbox me-2"></i>Свободные заявки</h5>
                        <span class="badge bg-primary rounded-pill">{{ openTickets.length }}</span>
                    </div>
                    <div class="card-body p-0">
                        <div v-if="openTickets.length === 0" class="text-center py-5 text-muted">
                            <i class="bi bi-check2-all display-4 d-block mb-2"></i>
                            Нет новых заявок
                        </div>
                        <div v-else class="list-group list-group-flush">
                            <div v-for="ticket in openTickets" :key="ticket.id" class="list-group-item p-3">
                                <div class="d-flex w-100 justify-content-between mb-2">
                                    <h6 class="mb-1 fw-bold text-dark">{{ ticket.title }}</h6>
                                    <small class="text-muted"><i class="bi bi-person me-1"></i>{{ ticket.author_username }}</small>
                                </div>
                                <p class="mb-2 text-secondary small">{{ ticket.description }}</p>
                                
                                <div class="d-flex flex-wrap gap-3 mb-2 text-muted small">
                                    <span><i class="bi bi-geo-alt me-1"></i>{{ ticket.corpus }}, {{ ticket.cabinet }}</span>
                                    <span><i class="bi bi-clock me-1"></i>{{ new Date(ticket.created_at).toLocaleString() }}</span>
                                </div>

                                <div v-if="ticket.image" class="mb-3">
                                     <small class="text-muted d-block mb-1 fw-bold"><i class="bi bi-image me-1"></i>Фото от учителя:</small>
                                    <a :href="ticket.image" target="_blank">
                                        <img :src="ticket.image" class="img-thumbnail" style="max-height: 150px; object-fit: cover;">
                                    </a>
                                </div>

                                <div class="d-flex justify-content-end align-items-center mt-2">
                                    <button class="btn btn-sm btn-primary px-3" @click="takeTicket(ticket.id)">
                                        Взять в работу
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Мои активные задачи -->
            <div class="col-md-4">
                <div class="card shadow-sm h-100 border-primary border-opacity-25">
                    <div class="card-header bg-primary text-white border-bottom d-flex justify-content-between align-items-center">
                        <h5 class="mb-0"><i class="bi bi-list-check me-2"></i>В работе</h5>
                        <span class="badge bg-white text-primary rounded-pill">{{ myTickets.length }}</span>
                    </div>
                    <div class="card-body p-0">
                        <div v-if="myTickets.length === 0" class="text-center py-5 text-muted">
                             <i class="bi bi-cup-hot display-4 d-block mb-2"></i>
                            Нет активных задач
                        </div>
                        <div v-else class="list-group list-group-flush">
                            <div v-for="ticket in myTickets" :key="ticket.id" class="list-group-item p-3 bg-light">
                                <div class="d-flex w-100 justify-content-between mb-1">
                                    <h6 class="mb-1 fw-bold">{{ ticket.title }}</h6>
                                    <span class="badge bg-warning text-dark">В работе</span>
                                </div>
                                <p class="mb-2 small text-secondary">{{ ticket.description }}</p>
                                
                                <div class="d-flex flex-wrap gap-3 mb-2 text-muted small">
                                    <span><i class="bi bi-geo-alt me-1"></i>{{ ticket.corpus }}, {{ ticket.cabinet }}</span>
                                    <span><i class="bi bi-person me-1"></i>{{ ticket.author_username }}</span>
                                </div>

                                <div v-if="ticket.image" class="mb-3">
                                     <small class="text-muted d-block mb-1 fw-bold"><i class="bi bi-image me-1"></i>Фото от учителя:</small>
                                    <a :href="ticket.image" target="_blank">
                                        <img :src="ticket.image" class="img-thumbnail" style="max-height: 150px; object-fit: cover;">
                                    </a>
                                </div>
                                
                                <div v-if="reportData.id === ticket.id" class="mt-3 card card-body border-success shadow-sm">
                                    <h6 class="card-title text-success"><i class="bi bi-flag me-2"></i>Завершение работы</h6>
                                    <div class="mb-2">
                                        <label class="form-label small text-muted">Фотоотчет</label>
                                        <input type="file" @change="handleReportImage" class="form-control form-control-sm">
                                    </div>
                                    <div class="mb-2">
                                        <label class="form-label small text-muted">Комментарий</label>
                                        <textarea v-model="reportData.comment" class="form-control form-control-sm" rows="2" placeholder="Что было сделано?"></textarea>
                                    </div>
                                    <div class="d-flex justify-content-end gap-2">
                                        <button class="btn btn-secondary btn-sm" @click="reportData.id = null">Отмена</button>
                                        <button class="btn btn-success btn-sm" @click="submitReport">Отправить отчет</button>
                                    </div>
                                </div>
                                <button v-else class="btn btn-sm btn-outline-success w-100 mt-2" @click="prepareReport(ticket)">
                                    <i class="bi bi-check-lg me-1"></i>Завершить задачу
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- История выполненных -->
            <div class="col-md-4">
                <div class="card shadow-sm h-100">
                    <div class="card-header bg-white text-success border-bottom d-flex justify-content-between align-items-center">
                        <h5 class="mb-0"><i class="bi bi-clock-history me-2"></i>История</h5>
                        <span class="badge bg-success rounded-pill">{{ completedTickets.length }}</span>
                    </div>
                    <div class="card-body p-0">
                        <div v-if="completedTickets.length === 0" class="text-center py-5 text-muted">
                            <i class="bi bi-journal-check display-4 d-block mb-2"></i>
                            История пуста
                        </div>
                        <div v-else class="list-group list-group-flush">
                            <div v-for="ticket in completedTickets" :key="ticket.id" class="list-group-item p-3">
                                <div class="d-flex w-100 justify-content-between mb-1">
                                    <h6 class="mb-1 fw-bold text-muted text-decoration-line-through">{{ ticket.title }}</h6>
                                    <span class="badge bg-secondary">Выполнено</span>
                                </div>
                                <p class="mb-2 small text-muted">{{ ticket.description }}</p>
                                <div class="d-flex flex-wrap gap-2 mb-2 text-muted small">
                                    <span><i class="bi bi-geo-alt me-1"></i>{{ ticket.corpus }}, {{ ticket.cabinet }}</span>
                                    <span><i class="bi bi-calendar-check me-1"></i>{{ new Date(ticket.updated_at).toLocaleDateString() }}</span>
                                </div>
                                
                                <div v-if="ticket.report_comment || ticket.report_image" class="mt-2 p-2 bg-light rounded small">
                                    <div v-if="ticket.report_comment" class="mb-1">
                                        <i class="bi bi-chat-left-text me-1 text-success"></i> {{ ticket.report_comment }}
                                    </div>
                                    <div v-if="ticket.report_image">
                                        <a :href="ticket.report_image" target="_blank" class="text-decoration-none">
                                            <i class="bi bi-image me-1"></i>Смотреть отчет
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

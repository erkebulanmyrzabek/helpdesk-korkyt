<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from '../axios'

const tickets = ref([])
const corpuses = ref([])
const newTicket = ref({
    title: '',
    description: '',
    building: '',
    room: '',
    media_before: null
})
const fileInputMedia = ref(null)
const mediaPreview = ref(null)
const isDragging = ref(false)

const fetchTickets = async () => {
    const response = await axios.get('tickets/')
    tickets.value = response.data
}

const fetchCorpuses = async () => {
    const response = await axios.get('corpuses/')
    corpuses.value = response.data
}

const setFile = (file) => {
    newTicket.value.media_before = file
    if (file) {
        mediaPreview.value = URL.createObjectURL(file)
    } else {
        mediaPreview.value = null
    }
}

const handleMediaUpload = (event) => {
    const file = event.target.files[0]
    setFile(file)
}

const handlePaste = (event) => {
    const items = (event.clipboardData || event.originalEvent.clipboardData).items;
    for (const item of items) {
        if (item.type.indexOf('image') === 0) {
            const blob = item.getAsFile();
            setFile(blob)
            
            // Sync with file input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(blob);
            fileInputMedia.value.files = dataTransfer.files;
            
            event.preventDefault();
            break;
        }
    }
}

const handleDrop = (event) => {
    isDragging.value = false;
    const file = event.dataTransfer.files[0];
    if (file) { // Allow any file type for now, backend validates
        setFile(file);
        
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInputMedia.value.files = dataTransfer.files;
    }
}

const removeMedia = () => {
    newTicket.value.media_before = null;
    mediaPreview.value = null;
    fileInputMedia.value.value = '';
}

const createTicket = async () => {
    const formData = new FormData()
    formData.append('title', newTicket.value.title)
    formData.append('description', newTicket.value.description)
    formData.append('building', newTicket.value.building)
    formData.append('room', newTicket.value.room)
    if (newTicket.value.media_before) formData.append('media_before', newTicket.value.media_before)

    try {
        await axios.post('tickets/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
        newTicket.value = { title: '', description: '', building: '', room: '', media_before: null }
        mediaPreview.value = null
        fileInputMedia.value.value = ''
        fetchTickets()
    } catch (error) {
        console.error(error)
        alert(error.response?.data?.detail || 'Ошибка при создании заявки')
    }
}

const showRatingModal = ref(false)
const ratingData = ref({
    ticketId: null,
    rating: 0,
    feedback: ''
})

const confirmTicket = (id) => {
    ratingData.value = { ticketId: id, rating: 0, feedback: '' }
    showRatingModal.value = true
}

const closeRatingModal = () => {
    showRatingModal.value = false
    ratingData.value = { ticketId: null, rating: 0, feedback: '' }
}

const submitRating = async () => {
    try {
        await axios.post(`tickets/${ratingData.value.ticketId}/approve/`, {
            rating: ratingData.value.rating,
            feedback: ratingData.value.feedback
        })
        closeRatingModal()
        fetchTickets()
    } catch (error) {
        alert(error.response?.data?.error || 'Ошибка')
    }
}

const getStatusBadgeClass = (status) => {
    switch(status) {
        case 'NEW': return 'badge bg-success';
        case 'TRANSIT': return 'badge bg-info text-dark';
        case 'IN_PROGRESS': return 'badge bg-warning text-dark';
        case 'WAITING_APPROVE': return 'badge bg-primary';
        case 'CLOSED': return 'badge bg-secondary';
        case 'UNFIXABLE': return 'badge bg-danger';
        default: return 'badge bg-light text-dark';
    }
}

const getStatusText = (status) => {
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

const formatDate = (dateString) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleString('ru-RU', {
        timeZone: 'Asia/Almaty',
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    })
}

const cleanComment = (comment) => {
    if (!comment) return ''
    // Remove [Timestamp] Username: pattern
    return comment.replace(/\[.*?\] .*?: /g, '').trim()
}

onMounted(() => {
    fetchTickets()
    fetchCorpuses()
})

onUnmounted(() => {
    if (mediaPreview.value) URL.revokeObjectURL(mediaPreview.value)
})
</script>

<template>
    <div class="row" @paste="handlePaste">
        <div class="col-md-4">
            <div class="card shadow-sm">
                <div class="card-header bg-white text-primary border-bottom">
                    <h5 class="mb-0"><i class="bi bi-plus-circle me-2"></i>Новая заявка</h5>
                </div>
                <div class="card-body">
                    <form @submit.prevent="createTicket">
                        <div class="mb-3">
                            <label class="form-label text-muted">Заголовок</label>
                            <input v-model="newTicket.title" class="form-control" placeholder="Кратко о проблеме" required>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label text-muted">Корпус</label>
                                <select v-model="newTicket.building" class="form-select" required>
                                    <option value="" disabled>Выберите...</option>
                                    <option v-for="corpus in corpuses" :key="corpus.id" :value="corpus.name">{{ corpus.name }}</option>
                                </select>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label text-muted">Кабинет</label>
                                <input v-model="newTicket.room" class="form-control" placeholder="№" required>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label text-muted">Описание</label>
                            <textarea v-model="newTicket.description" class="form-control" rows="4" placeholder="Подробное описание... (Ctrl+V для вставки фото)" required></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label text-muted"><i class="bi bi-paperclip me-1"></i>Медиа (Фото/Видео)</label>
                            
                            <div 
                                class="upload-zone mb-2"
                                :class="{ 'is-dragging': isDragging }"
                                @dragover.prevent="isDragging = true"
                                @dragleave.prevent="isDragging = false"
                                @drop.prevent="handleDrop"
                                @click="$refs.fileInputMedia.click()"
                            >
                                <div v-if="!mediaPreview" class="text-center py-4 text-muted">
                                    <i class="bi bi-cloud-upload display-6 mb-2 d-block"></i>
                                    <span class="small">Нажмите или перетащите файл сюда</span>
                                </div>
                                <div v-else class="position-relative h-100 d-flex justify-content-center align-items-center bg-light rounded">
                                    <span class="text-success fw-bold">Файл выбран</span>
                                    <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0 m-2" @click.stop="removeMedia">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                </div>
                            </div>
                            
                            <input type="file" @change="handleMediaUpload" ref="fileInputMedia" class="d-none">
                        </div>
                        
                        <button type="submit" class="btn btn-primary w-100 fw-bold py-2">
                            <i class="bi bi-send me-2"></i>Отправить заявку
                        </button>
                    </form>
                </div>
            </div>
        </div>
        <div class="col-md-8">
            <h3 class="mb-4 text-primary"><i class="bi bi-list-task me-2"></i>Мои заявки</h3>
            <div class="list-group shadow-sm rounded-3 overflow-hidden">
                <div v-if="tickets.length === 0" class="list-group-item text-center py-5 text-muted">
                    <i class="bi bi-inbox display-4 mb-3 d-block"></i>
                    У вас пока нет заявок
                </div>
                <div v-for="ticket in tickets" :key="ticket.id" class="list-group-item p-4 border-start-0 border-end-0">
                    <div class="d-flex w-100 justify-content-between align-items-start mb-2">
                        <h5 class="mb-1 fw-bold text-dark">{{ ticket.title }}</h5>
                        <span :class="getStatusBadgeClass(ticket.status)">{{ getStatusText(ticket.status) }}</span>
                    </div>
                    <p class="mb-2 text-secondary">{{ ticket.description }}</p>
                    <div class="d-flex align-items-center text-muted small mb-3">
                        <span class="me-3"><i class="bi bi-building me-1"></i>{{ ticket.building }}</span>
                        <span class="me-3"><i class="bi bi-door-open me-1"></i>{{ ticket.room }}</span>
                        <span><i class="bi bi-calendar me-1"></i>{{ new Date(ticket.created_at).toLocaleString('ru-RU', { timeZone: 'Asia/Almaty', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) }}</span>
                    </div>
                    
                    <div v-if="ticket.media_before" class="mb-3">
                         <a :href="ticket.media_before" target="_blank" class="btn btn-sm btn-outline-info">
                            <i class="bi bi-paperclip me-1"></i>Смотреть медиа
                         </a>
                    </div>
                    
                    <div v-if="ticket.assigned_to_username" class="alert alert-light border-0 bg-light p-2 d-inline-block mb-2">
                        <small class="text-muted"><i class="bi bi-person-badge me-1"></i>Исполнитель: <strong>{{ ticket.assigned_to_username }}</strong></small>
                    </div>

                     <div v-if="ticket.status === 'WAITING_APPROVE'" class="mt-3 card border-warning mb-3">
                        <div class="card-header bg-warning text-dark fw-bold">
                            <i class="bi bi-flag-fill me-2"></i>🏁 Работа выполнена
                        </div>
                        <div class="card-body bg-warning bg-opacity-10">
                            <div class="mb-2">
                                <strong>Исполнитель:</strong> {{ ticket.assigned_to_username }}
                            </div>
                            <div class="mb-2">
                                <strong>Время завершения:</strong> {{ formatDate(ticket.completed_at) }}
                            </div>
                            
                            <div v-if="ticket.report_comment" class="mb-3 p-2 bg-white rounded border">
                                <small class="text-muted d-block mb-1">Комментарий исполнителя:</small>
                                {{ cleanComment(ticket.report_comment) }}
                            </div>

                            <div v-if="ticket.media_after" class="mb-3">
                                <small class="text-muted d-block mb-1">Фото результата:</small>
                                <a :href="ticket.media_after" target="_blank" class="d-inline-block border rounded overflow-hidden">
                                    <img :src="ticket.media_after" alt="Результат" style="height: 100px; object-fit: cover;">
                                </a>
                            </div>

                            <button class="btn btn-success w-100 btn-lg shadow-sm" @click="confirmTicket(ticket.id)">
                                <i class="bi bi-check-circle-fill me-2"></i>Подтвердить выполнение
                            </button>
                        </div>
                    </div>

                     <div v-if="ticket.status === 'CLOSED'" class="mt-3 p-3 bg-success bg-opacity-10 rounded border border-success border-opacity-10">
                        <h6 class="text-success fw-bold"><i class="bi bi-check-circle-fill me-2"></i>Заявка закрыта</h6>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Rating Modal -->
    <div v-if="showRatingModal" class="modal-overlay">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Оцените работу специалиста</h5>
                    <button type="button" class="btn-close" @click="closeRatingModal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3 text-center">
                        <label class="form-label d-block">Рейтинг</label>
                        <div class="rating-stars">
                            <span 
                                v-for="star in 5" 
                                :key="star" 
                                class="star" 
                                :class="{ 'active': ratingData.rating >= star }"
                                @click="ratingData.rating = star"
                            >
                                ★
                            </span>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Комментарий</label>
                        <textarea v-model="ratingData.feedback" class="form-control" rows="3" placeholder="Ваш отзыв..."></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" @click="closeRatingModal">Отмена</button>
                    <button type="button" class="btn btn-primary" @click="submitRating" :disabled="!ratingData.rating">Подтвердить</button>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.upload-zone {
    border: 2px dashed #dee2e6;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    background-color: #f8f9fa;
    min-height: 150px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.upload-zone:hover, .upload-zone.is-dragging {
    border-color: var(--primary-color, #0d6efd);
    background-color: #e9ecef;
}

.upload-zone img {
    object-fit: contain;
}

.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1050;
}

.rating-stars {
    font-size: 2rem;
    color: #ddd;
    cursor: pointer;
}

.rating-stars .star {
    margin: 0 5px;
    transition: color 0.2s;
}

.rating-stars .star.active {
    color: #ffc107;
}
</style>

<style scoped>
.upload-zone {
    border: 2px dashed #dee2e6;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    background-color: #f8f9fa;
    min-height: 150px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.upload-zone:hover, .upload-zone.is-dragging {
    border-color: var(--primary-color, #0d6efd);
    background-color: #e9ecef;
}

.upload-zone img {
    object-fit: contain;
}
</style>

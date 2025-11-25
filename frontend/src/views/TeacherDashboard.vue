<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from '../axios'

const tickets = ref([])
const newTicket = ref({
    title: '',
    description: '',
    corpus: '',
    cabinet: '',
    image: null,
    video: null
})
const fileInputImage = ref(null)
const fileInputVideo = ref(null)
const imagePreview = ref(null)
const isDragging = ref(false)

const fetchTickets = async () => {
    const response = await axios.get('tickets/')
    tickets.value = response.data
}

const setFile = (file) => {
    newTicket.value.image = file
    if (file) {
        imagePreview.value = URL.createObjectURL(file)
    } else {
        imagePreview.value = null
    }
}

const handleImageUpload = (event) => {
    const file = event.target.files[0]
    setFile(file)
}

const handleVideoUpload = (event) => {
    newTicket.value.video = event.target.files[0]
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
            fileInputImage.value.files = dataTransfer.files;
            
            event.preventDefault();
            break;
        }
    }
}

const handleDrop = (event) => {
    isDragging.value = false;
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        setFile(file);
        
        // Sync with file input
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInputImage.value.files = dataTransfer.files;
    }
}

const removeImage = () => {
    newTicket.value.image = null;
    imagePreview.value = null;
    fileInputImage.value.value = '';
}

const createTicket = async () => {
    const formData = new FormData()
    formData.append('title', newTicket.value.title)
    formData.append('description', newTicket.value.description)
    formData.append('corpus', newTicket.value.corpus)
    formData.append('cabinet', newTicket.value.cabinet)
    if (newTicket.value.image) formData.append('image', newTicket.value.image)
    if (newTicket.value.video) formData.append('video', newTicket.value.video)

    try {
        await axios.post('tickets/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
        newTicket.value = { title: '', description: '', corpus: '', cabinet: '', image: null, video: null }
        imagePreview.value = null
        fileInputImage.value.value = ''
        fileInputVideo.value.value = ''
        fetchTickets()
    } catch (error) {
        console.error(error)
        alert('Ошибка при создании заявки')
    }
}

const getStatusBadgeClass = (status) => {
    switch(status) {
        case 'open': return 'badge bg-success';
        case 'in_progress': return 'badge bg-warning text-dark';
        case 'done': return 'badge bg-secondary';
        default: return 'badge bg-light text-dark';
    }
}

const getStatusText = (status) => {
    switch(status) {
        case 'open': return 'Открыта';
        case 'in_progress': return 'В работе';
        case 'done': return 'Выполнена';
        default: return status;
    }
}

onMounted(fetchTickets)

// Clean up object URL to avoid memory leaks
onUnmounted(() => {
    if (imagePreview.value) URL.revokeObjectURL(imagePreview.value)
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
                                <select v-model="newTicket.corpus" class="form-select" required>
                                    <option value="" disabled>Выберите...</option>
                                    <option value="Главный корпус">Главный корпус</option>
                                    <option v-for="i in 9" :key="i" :value="`Корпус ${i}`">Корпус {{ i }}</option>
                                </select>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label text-muted">Кабинет</label>
                                <input v-model="newTicket.cabinet" class="form-control" placeholder="№" required>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label text-muted">Описание</label>
                            <textarea v-model="newTicket.description" class="form-control" rows="4" placeholder="Подробное описание... (Ctrl+V для вставки фото)" required></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label text-muted"><i class="bi bi-camera me-1"></i>Фото</label>
                            
                            <!-- Drag and Drop Zone -->
                            <div 
                                class="upload-zone mb-2"
                                :class="{ 'is-dragging': isDragging }"
                                @dragover.prevent="isDragging = true"
                                @dragleave.prevent="isDragging = false"
                                @drop.prevent="handleDrop"
                                @click="$refs.fileInputImage.click()"
                            >
                                <div v-if="!imagePreview" class="text-center py-4 text-muted">
                                    <i class="bi bi-cloud-upload display-6 mb-2 d-block"></i>
                                    <span class="small">Нажмите или перетащите фото сюда</span>
                                    <br>
                                    <span class="small opacity-75">(или вставьте из буфера Ctrl+V)</span>
                                </div>
                                <div v-else class="position-relative h-100 d-flex justify-content-center align-items-center bg-light rounded">
                                    <img :src="imagePreview" class="img-fluid rounded" style="max-height: 200px;">
                                    <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0 m-2" @click.stop="removeImage">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                </div>
                            </div>
                            
                            <input type="file" @change="handleImageUpload" ref="fileInputImage" class="d-none" accept="image/*">
                        </div>
                        
                         <div class="mb-4">
                            <label class="form-label text-muted"><i class="bi bi-camera-reels me-1"></i>Видео</label>
                            <input type="file" @change="handleVideoUpload" ref="fileInputVideo" class="form-control" accept="video/*">
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
                        <span class="me-3"><i class="bi bi-building me-1"></i>{{ ticket.corpus }}</span>
                        <span class="me-3"><i class="bi bi-door-open me-1"></i>{{ ticket.cabinet }}</span>
                        <span><i class="bi bi-calendar me-1"></i>{{ new Date(ticket.created_at).toLocaleDateString() }}</span>
                    </div>
                    
                    <div v-if="ticket.image" class="mb-3">
                         <small class="text-muted d-block mb-1"><i class="bi bi-paperclip me-1"></i>Прикрепленное фото:</small>
                        <img :src="ticket.image" class="img-thumbnail" style="max-height: 150px;">
                    </div>
                    
                    <div v-if="ticket.assigned_to_username" class="alert alert-light border-0 bg-light p-2 d-inline-block mb-2">
                        <small class="text-muted"><i class="bi bi-person-badge me-1"></i>Исполнитель: <strong>{{ ticket.assigned_to_username }}</strong></small>
                    </div>

                     <div v-if="ticket.status === 'done'" class="mt-3 p-3 bg-success bg-opacity-10 rounded border border-success border-opacity-10">
                        <h6 class="text-success fw-bold"><i class="bi bi-check-circle-fill me-2"></i>Отчет о выполнении</h6>
                        <p v-if="ticket.report_comment" class="mb-2">{{ ticket.report_comment }}</p>
                        <img v-if="ticket.report_image" :src="ticket.report_image" class="img-thumbnail rounded shadow-sm" style="max-width: 200px">
                    </div>
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
</style>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from '../axios'
import AdminSubNav from '../components/AdminSubNav.vue'

const feedbacks = ref([])
const helperFilter = ref('')

const notifications = ref({
    new_requests: 0,
    new_feedbacks: 0
})

const fetchFeedbacks = async () => {
    try {
        const response = await axios.get('feedbacks/')
        feedbacks.value = response.data
        // Mark as viewed when admin opens this page
        await markFeedbacksViewed()
    } catch (error) {
        console.error(error)
    }
}

const fetchNotifications = async () => {
    try {
        const response = await axios.get('admin/notifications/summary/')
        notifications.value = response.data
    } catch (error) {
        console.error('Error fetching notifications:', error)
    }
}

const markFeedbacksViewed = async () => {
    try {
        await axios.post('admin/notifications/mark-feedbacks-viewed/')
        notifications.value.new_feedbacks = 0
    } catch (error) {
        console.error('Error marking feedbacks as viewed:', error)
    }
}

const uniqueHelpers = computed(() => {
    const helpers = new Set(feedbacks.value.map(f => f.helper_username).filter(Boolean))
    return Array.from(helpers).sort()
})

const sortedFeedbacks = computed(() => {
    let result = [...feedbacks.value]
    
    // Filter
    if (helperFilter.value) {
        result = result.filter(f => f.helper_username === helperFilter.value)
    }

    // Sort (Newest first)
    result.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    
    return result
})

const formatDate = (dateString) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    })
}

onMounted(() => {
    fetchNotifications()
    fetchFeedbacks()
})
</script>

<template>
    <div class="container-fluid pb-5">
        <AdminSubNav 
            :newRequests="notifications.new_requests" 
            :newFeedbacks="notifications.new_feedbacks"
        />

        <div class="d-flex justify-content-between align-items-center mb-4">
            <h4 class="text-muted mb-0"><i class="bi bi-star me-2"></i>Отзывы пользователей</h4>
            <div class="d-flex gap-3 align-items-center">
                <select v-model="helperFilter" class="form-select form-select-sm" style="width: 200px;">
                    <option value="">Все хелперы</option>
                    <option v-for="helper in uniqueHelpers" :key="helper" :value="helper">{{ helper }}</option>
                </select>
            </div>
        </div>

        <div class="card shadow-sm">
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Хелпдеск</th>
                                <th>Пользователь</th>
                                <th>Оценка</th>
                                <th>Комментарий</th>
                                <th>Заявка</th>
                                <th>Дата</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-if="sortedFeedbacks.length === 0">
                                <td colspan="6" class="text-center py-4 text-muted">Нет отзывов</td>
                            </tr>
                            <tr v-for="feedback in sortedFeedbacks" :key="feedback.id">
                                <td>
                                    <span class="badge bg-info text-dark">{{ feedback.helper_username }}</span>
                                </td>
                                <td>{{ feedback.author_username }}</td>
                                <td>
                                    <span class="text-warning">
                                        <i v-for="n in 5" :key="n" class="bi" :class="n <= feedback.rating ? 'bi-star-fill' : 'bi-star'"></i>
                                    </span>
                                </td>
                                <td>
                                    <span v-if="feedback.comment" class="fst-italic">"{{ feedback.comment }}"</span>
                                    <span v-else class="text-muted small">-</span>
                                </td>
                                <td>
                                    <small class="text-muted">#{{ feedback.ticket }}</small>
                                    <div class="small fw-bold">{{ feedback.ticket_title }}</div>
                                </td>
                                <td class="small text-muted">{{ formatDate(feedback.created_at) }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</template>

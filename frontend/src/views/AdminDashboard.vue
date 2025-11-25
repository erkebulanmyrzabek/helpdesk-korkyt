<script setup>
import { ref, onMounted } from 'vue'
import axios from '../axios'

const stats = ref({
    total: 0,
    by_status: []
})

const fetchStats = async () => {
    try {
        const response = await axios.get('tickets/stats/')
        stats.value = response.data
    } catch (error) {
        console.error(error)
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

onMounted(fetchStats)
</script>

<template>
    <div>
        <h2 class="mb-4 text-primary"><i class="bi bi-bar-chart-line me-2"></i>Статистика системы</h2>
        
        <div class="row g-4 mb-4">
            <div class="col-md-4">
                <div class="card bg-gradient-primary text-white h-100 shadow-sm" style="background: linear-gradient(45deg, #002855, #00509d);">
                    <div class="card-body d-flex flex-column justify-content-center align-items-center text-center py-5">
                        <h1 class="display-1 fw-bold mb-0">{{ stats.total }}</h1>
                        <p class="lead opacity-75">Всего заявок за все время</p>
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
    </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Clock from './Clock.vue'

const props = defineProps({
    newRequests: {
        type: Number,
        default: 0
    },
    newFeedbacks: {
        type: Number,
        default: 0
    }
})

const route = useRoute()

const activeTab = computed(() => {
    if (route.name === 'admin') {
        return route.query.tab || 'stats'
    }
    return ''
})
</script>

<template>
    <div class="admin-subnav mb-4">
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div class="d-flex align-items-center gap-3">
                <h2 class="text-primary mb-0">
                    <i class="bi bi-speedometer2 me-2"></i>Панель администратора
                </h2>
                <Clock />
            </div>
            <div class="btn-group shadow-sm">
                <router-link 
                    to="/admin?tab=stats" 
                    class="btn d-flex align-items-center px-3" 
                    :class="activeTab === 'stats' ? 'btn-primary' : 'btn-outline-primary'"
                >
                    <i class="bi bi-graph-up me-1"></i>Статистика
                </router-link>
                <router-link 
                    to="/admin?tab=users" 
                    class="btn d-flex align-items-center px-3" 
                    :class="activeTab === 'users' ? 'btn-primary' : 'btn-outline-primary'"
                >
                    <i class="bi bi-people me-1"></i>Пользователи
                </router-link>
                <router-link 
                    to="/admin?tab=requests" 
                    class="btn d-flex align-items-center px-3 position-relative" 
                    :class="activeTab === 'requests' ? 'btn-primary' : 'btn-outline-primary'"
                >
                    <i class="bi bi-person-check me-1"></i>Запросы
                    <span v-if="newRequests > 0" class="notification-badge">
                        {{ newRequests }}
                    </span>
                </router-link>
                <router-link 
                    to="/admin/reports" 
                    class="btn d-flex align-items-center px-3" 
                    :class="route.name === 'admin-reports' ? 'btn-primary' : 'btn-outline-primary'"
                >
                    <i class="bi bi-file-earmark-bar-graph me-1"></i>Получение отчета
                </router-link>
                <router-link 
                    to="/admin/reviews" 
                    class="btn d-flex align-items-center px-3 position-relative" 
                    :class="route.name === 'admin-reviews' ? 'btn-primary' : 'btn-outline-primary'"
                >
                    <i class="bi bi-star me-1"></i>Отзывы
                    <span v-if="newFeedbacks > 0" class="notification-badge">
                        {{ newFeedbacks }}
                    </span>
                </router-link>
                <router-link 
                    to="/admin/settings" 
                    class="btn d-flex align-items-center px-3" 
                    :class="route.name === 'admin-settings' ? 'btn-primary' : 'btn-outline-primary'"
                >
                    <i class="bi bi-gear me-1"></i>Настройки
                </router-link>
            </div>
        </div>
        <hr class="mt-3 opacity-10">
    </div>
</template>

<style scoped>
.notification-badge {
    position: absolute;
    top: -8px;
    right: -8px;
    min-width: 22px;
    height: 22px;
    padding: 0 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    color: white;
    background: linear-gradient(135deg, #ff4757, #ff6348);
    border-radius: 11px;
    box-shadow: 0 2px 8px rgba(255, 71, 87, 0.4), 0 0 0 3px rgba(255, 255, 255, 0.8);
    animation: pulse-badge 2s ease-in-out infinite;
    z-index: 10;
}

@keyframes pulse-badge {
    0%, 100% {
        transform: scale(1);
        box-shadow: 0 2px 8px rgba(255, 71, 87, 0.4), 0 0 0 3px rgba(255, 255, 255, 0.8);
    }
    50% {
        transform: scale(1.1);
        box-shadow: 0 4px 12px rgba(255, 71, 87, 0.6), 0 0 0 4px rgba(255, 255, 255, 0.9);
    }
}

.btn-group .btn {
    font-weight: 500;
    transition: all 0.2s ease;
}
.btn-primary {
    box-shadow: 0 4px 10px rgba(13, 110, 253, 0.2);
}
@media (max-width: 768px) {
    .btn-group {
        width: 100%;
        flex-direction: column;
    }
    .btn-group .btn {
        border-radius: 0.5rem !important;
        margin-bottom: 5px;
        border: 1px solid #0d6efd !important;
    }
    .notification-badge {
        top: 8px;
        right: 8px;
    }
}
</style>

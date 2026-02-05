<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Clock from './Clock.vue'

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
                    to="/admin/reports" 
                    class="btn d-flex align-items-center px-3" 
                    :class="route.name === 'admin-reports' ? 'btn-primary' : 'btn-outline-primary'"
                >
                    <i class="bi bi-file-earmark-bar-graph me-1"></i>Получение отчета
                </router-link>
                <router-link 
                    to="/admin/reviews" 
                    class="btn d-flex align-items-center px-3" 
                    :class="route.name === 'admin-reviews' ? 'btn-primary' : 'btn-outline-primary'"
                >
                    <i class="bi bi-star me-1"></i>Отзывы
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
}
</style>

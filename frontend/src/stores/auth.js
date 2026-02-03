import { defineStore } from 'pinia'
import axios from '../axios'
import router from '../router'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: JSON.parse(localStorage.getItem('user')) || null,
        token: localStorage.getItem('token') || null,
    }),
    getters: {
        isAuthenticated: (state) => !!state.token,
        isTeacher: (state) => state.user?.role === 'teacher',
        isHelpdesk: (state) => state.user?.role === 'helpdesk',
        isAdmin: (state) => state.user?.role === 'admin',
    },
    actions: {
        async login(username, password) {
            try {
                const response = await axios.post('api-token-auth/', { username, password })
                this.token = response.data.token;
                localStorage.setItem('token', this.token);

                const userResponse = await axios.get('users/me/');
                this.user = userResponse.data;
                localStorage.setItem('user', JSON.stringify(this.user));

                // Redirect based on role
                if (this.isTeacher) router.push('/teacher');
                else if (this.isHelpdesk) router.push('/helpdesk');
                else if (this.isAdmin) router.push('/admin');

            } catch (error) {
                console.error("Login failed", error);
                throw error;
            }
        },
        async logout() {
            await router.push('/login');
            this.user = null;
            this.token = null;
            localStorage.removeItem('user');
            localStorage.removeItem('token');
        }
    }
})

import { api } from "./client";

// Admin only: everyone who uses ColdReach, Each returns the response body.
export const adminUsersApi = {
    // Newest first: [{ id, name, email, role, status: 'active' | 'blocked' | 'pending', auth_provider,
    //   created_at, blocked_at, blocked_by_name, emails_sent, last_sent_at }]
    list: () => api.get('/users/').then((res) => res.data),

    // role: 'user' | 'admin' -> the updated user. Not for your own account.
    setRole: (id, role) => api.patch(`/users/${id}/role`, {role}).then((res) => res.data),

    // blocked: true | false -> the updated user. A blocked user is signed out and can't sign in.
    setBlocked: (id, blocked) => api.patch(`/users/${id}/block`, {blocked }).then((res) => res.data),

}
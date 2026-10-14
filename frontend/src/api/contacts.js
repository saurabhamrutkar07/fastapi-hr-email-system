import { api } from "./client";

// HR contacts are one list shared by every user
export const contactsApi = {
    // Every contact: [{id, name, title, company, email, phone, created_at, 
    //  emails: [{ email, is_primary, is_verified}], phones: [{phone, is_primary }] }]
    list: () => api.get('/hr-contacts/v2/list').then((res) => res.data ), 
}


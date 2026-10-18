import { api } from "./client";

// HR contacts are one list shared by every user
export const contactsApi = {
    // Every contact: [{id, name, title, company, email, phone, created_at, 
    //  emails: [{ email, is_primary, is_verified}], phones: [{phone, is_primary }] }]
    list: () => api.get('/hr-contacts/v2/list').then((res) => res.data ), 

    // { status, message, contact_id, email, merged}. `merged` is true when the email or phone already
    // belonged to a saved contact, so the new details were added to that contact instead 
    add : (contact) => api.post('/hr-contacts/v2/add', contact).then((res) => res.data),

    // Admin only. Replaces the contact's details and its email / phone lists. 409 when an email or
    // phone belongs to another contact
    update: (id, contact) => api.put(`/hr-contacts/v2/${id}`, contact).then((res)=> res.data),

    // Admin only. Deletes the contact with its emails and phones
    remove: (id) => api.delete(`/hr-contacts/v2/${id}`).then((res) => res.data),

    // Admin only. Excel / CSV upload: { status, total_rows, created_contacts, existing_contacts,
    //   emails_added, phones_added, skipped_contacts, errors: [{ row?, name?, error }] }
    importFile: (file) => {
        const body = new FormData()
        body.append('file', file)
        return api.post('/hr-contacts/v2/upload-file', body).then((res) => res.data)
    },
}


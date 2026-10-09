// Sidebar / drawer manu. `to` must match a route path in App.jsx.
export const NAV_GROUPS = [
    {
        label : 'Workspace',
        items : [
            {to: '/', label: 'Dashboard', icon: 'home'},
            {to: '/contacts', label: 'HR Contacts', icon: 'users'},
            {to: '/send', label:'Send Email', icon: 'send'},
            {to: '/history', label: 'History', icon: 'clock'},
        ],
    },
    {
        label: "Setup",
        items : [
            {to: '/templates', label: 'Templates', icon: 'file'},
            {to: '/resumes', label: 'Resumes', icon: 'resume'},
            {to: '/settings', label: 'Settings', icon: 'sliders'},
        ],
    },
    {
        // Shown to everyone for now; Step 3 (auth) hides it for non-admins
        label: 'Admin',
        items: [{to: '/admin/users', label:'Users',icon:'shield'}],
    }
]

// Mobile bottom bar: the four most used pages. Everyhing else is under "More".
export const BOTTOM_NAV = [
    
    {to: '/', label: 'Dashboard', icon: 'home'},
    {to: '/contacts', label: 'HR Contacts', icon: 'users'},
    {to: '/send', label:'Send Email', icon: 'send'},
    {to: '/history', label: 'History', icon: 'clock'},
]

// Pages reached through "More" - used to highlight the More button
export const MORE_PATHS = ['/templates','/resumes','/settings','/admin']

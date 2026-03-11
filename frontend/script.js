// ========== LOCALSTORAGE HELPERS ==========
function getUsers() {
    const users = localStorage.getItem('users');
    if (users) {
        return JSON.parse(users);
    } else {
        // No users yet – create a default admin
        const defaultAdmin = [
            { username: 'admin', password: 'admin', role: 'admin', registered: new Date().toLocaleString() }
        ];
        localStorage.setItem('users', JSON.stringify(defaultAdmin));
        return defaultAdmin;
    }
}

function saveUsers(users) {
    localStorage.setItem('users', JSON.stringify(users));
}

function getCurrentUser() {
    const user = sessionStorage.getItem('currentUser');
    return user ? JSON.parse(user) : null;
}

function setCurrentUser(user) {
    sessionStorage.setItem('currentUser', JSON.stringify({ username: user.username, role: user.role }));
}

function logout() {
    sessionStorage.removeItem('currentUser');
}

// ========== ADMIN FUNCTIONS ==========
function deleteUser(username) {
    let users = getUsers();
    users = users.filter(u => u.username !== username);
    saveUsers(users);
}

function toggleUserRole(username) {
    let users = getUsers();
    const user = users.find(u => u.username === username);
    if (user) {
        user.role = user.role === 'admin' ? 'user' : 'admin';
        saveUsers(users);
    }
}

// ========== INIT: ensure allowRegistration flag exists ==========
if (localStorage.getItem('allowRegistration') === null) {
    localStorage.setItem('allowRegistration', 'true');
}
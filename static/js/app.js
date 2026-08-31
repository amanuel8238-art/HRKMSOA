// HRKMSO - Komishinii Manneen Sirreessaa Oromiyaa JavaScript Application

document.addEventListener('DOMContentLoaded', () => {
    // Initialize application data
    initApp();
    setupEventListeners();
});

// Mock Data for Employees, Branches, and Transfers
let appData = {
    employees: [
        { id: "HR-001", name: "Abraaham Kebede", gender: "Dhiira", branch: "Biiroo Appii (Headquarters)", position: "Daayireektara Qajeelchaa", rank: "Komishinara" },
        { id: "HR-002", name: "Tirunesh Gabayyoo", gender: "Dubartii", branch: "Aanaa Dadar", position: "Ogeessa Bulchiinsa Humna Namaa", rank: "Inspeekterii" },
        { id: "HR-003", name: "Gamachuu Tolasaa", gender: "Dhiira", branch: "Mana Sirreessaa Finfinnee", position: "Hoggansa Eegumsaa", rank: "Kommanderii" },
        { id: "HR-004", name: "Sifan Tasfaayee", gender: "Dubartii", branch: "Aanaa Dadar", position: "Fandii fi Faayinaansi", rank: "Sajjootti" }
    ],
    branches: [
        "Biiroo Appii (Headquarters)", 
        "Aanaa Dadar", 
        "Mana Sirreessaa Finfinnee", 
        "Mana Sirreessaa Adaamaa", 
        "Mana Sirreessaa Jimmaa", 
        "Mana Sirreessaa Naqamtee", 
        "Mana Sirreessaa Shaashamannee",
        "Dameewwan Hafe (32)"
    ],
    transfers: [
        { employee: "Tirunesh Gabayyoo", from: "Mana Sirreessaa Finfinnee", to: "Aanaa Dadar", reason: "Gaaffii Dhuunfaa", status: "Mirkanaa'e" },
        { employee: "Gamachuu Tolasaa", from: "Mana Sirreessaa Adaamaa", to: "Biiroo Appii (Headquarters)", position: "Guddina Sadarkaa", status: "Adeemsarra Jira" }
    ],
    ranks: [
        { name: "Komishinara", description: "Hooggansa Olaanoo Komishinichaa" },
        { name: "Kommanderii", description: "I/Aanaa ykn Hogganaa Damee Gurguddoo" },
        { name: "Inspeekterii Olaanoo", description: "Ogeessa Olaanaa / Garee Hogganaa" },
        { name: "Inspeekterii", description: "Ogeessa Damee Hojii Addaddaa" },
        { name: "Sajjootti", description: "Hojjetaa Deeskii fi Tajaajila Kennituu" },
        { name: "Hojjetaa Idilee", description: "Hojjetoota Waliigalaa" }
    ]
};

function initApp() {
    updateDashboardStats();
    renderRecentEmployees();
    renderBranchSummaries();
    renderEmployeesTable();
    renderBranchesGrid();
    renderTransfersTable();
    renderRanksList();
    populateBranchDropdown();
}

function setupEventListeners() {
    // Sidebar Navigation Switching
    const navItems = document.querySelectorAll('.sidebar-nav li');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            const target = item.getAttribute('data-target');
            document.querySelectorAll('.view-section').forEach(section => {
                section.classList.remove('active');
            });
            document.getElementById(target).classList.add('active');

            // Update Page Title
            const titles = {
                dashboard: 'Daashboordii Waliigalaa',
                employees: 'Galmee Hojjetootaa',
                branches: 'Dameewwan Komishinichaa (39)',
                transfers: 'Qajeelcha Jijjiirraa Hojjetootaa',
                ranks: 'Caasaa Raankii fi Sadarkaa',
                reports: 'Gabaasa Waliigalaa',
                settings: 'Qindaa\'ina Sirnaa'
            };
            document.getElementById('page-title').textContent = titles[target] || 'HRKMSO';
        });
    });

    // Sidebar Toggle for Mobile
    const toggleBtn = document.getElementById('sidebar-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('collapsed');
        });
    }

    // Modal Controls for Adding Employee
    const modal = document.getElementById('employee-modal');
    const addEmpBtn = document.getElementById('btn-add-employee');
    const closeBtn = document.querySelector('.close-modal');

    if (addEmpBtn) {
        addEmpBtn.addEventListener('click', () => modal.style.display = 'flex');
    }
    if (closeBtn) {
        closeBtn.addEventListener('click', () => modal.style.display = 'none');
    }

    // Employee Form Submission
    const empForm = document.getElementById('employee-form');
    if (empForm) {
        empForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const newEmp = {
                id: `HR-00${appData.employees.length + 1}`,
                name: document.getElementById('emp-name').value,
                gender: document.getElementById('emp-gender').value,
                rank: document.getElementById('emp-rank').value,
                branch: document.getElementById('emp-branch').value,
                position: document.getElementById('emp-position').value
            };
            appData.employees.unshift(newEmp);
            initApp();
            modal.style.display = 'none';
            empForm.reset();
            alert('Hojjetaan haaraan milkaa\'inaan galmeeffameera!');
        });
    }

    // Search Filtering
    const searchInput = document.getElementById('employee-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const filtered = appData.employees.filter(emp => 
                emp.name.toLowerCase().includes(query) || 
                emp.branch.toLowerCase().includes(query) || 
                emp.id.toLowerCase().includes(query)
            );
            renderFilteredEmployees(filtered);
        });
    }
}

// Render Functions
function updateDashboardStats() {
    document.getElementById('total-employees').textContent = appData.employees.length + 1240; // Simulated total count
    document.getElementById('total-transfers').textContent = appData.transfers.length;
    document.getElementById('total-leaders').textContent = appData.employees.filter(e => e.rank === 'Komishinara' || e.rank === 'Kommanderii').length + 45;
}

function renderRecentEmployees() {
    const tbody = document.querySelector('#recent-employees-table tbody');
    if (!tbody) return;
    tbody.innerHTML = appData.employees.slice(0, 4).map(emp => `
        <tr>
            <td>${emp.name}</td>
            <td>${emp.branch}</td>
            <td>${emp.position}</td>
            <td><span class="badge">${emp.rank}</span></td>
        </tr>
    `).join('');
}

function renderBranchSummaries() {
    const container = document.getElementById('branch-summary-list');
    if (!container) return;
    container.innerHTML = `
        <div class="summary-item"><span>Biiroo Appii & Qajeelcha</span><strong>35 Hojjetoota</strong></div>
        <div class="summary-item highlight"><span>Aanaa Dadar (Damee Addaa)</span><strong>18 Hojjetoota</strong></div>
        <div class="summary-item"><span>Mana Sirreessaa Finfinnee</span><strong>120 Hojjetoota</strong></div>
        <div class="summary-item"><span>Dameewwan Biqiltuu / Waraanaa (36)</span><strong>1,080 Hojjetoota</strong></div>
    `;
}

function renderEmployeesTable() {
    const tbody = document.querySelector('#employees-table tbody');
    if (!tbody) return;
    tbody.innerHTML = appData.employees.map(emp => `
        <tr>
            <td>${emp.id}</td>
            <td>${emp.name}</td>
            <td>${emp.gender}</td>
            <td>${emp.branch}</td>
            <td>${emp.position}</td>
            <td>${emp.rank}</td>
            <td><button class="btn-sm" onclick="alert('Ilaaluuf / Sirreessuuf: ${emp.name}')">Gulaali</button></td>
        </tr>
    `).join('');
}

function renderFilteredEmployees(list) {
    const tbody = document.querySelector('#employees-table tbody');
    if (!tbody) return;
    tbody.innerHTML = list.map(emp => `
        <tr>
            <td>${emp.id}</td>
            <td>${emp.name}</td>
            <td>${emp.gender}</td>
            <td>${emp.branch}</td>
            <td>${emp.position}</td>
            <td>${emp.rank}</td>
            <td><button class="btn-sm">Gulaali</button></td>
        </tr>
    `).join('');
}

function renderBranchesGrid() {
    const grid = document.getElementById('branches-grid');
    if (!grid) return;
    grid.innerHTML = appData.branches.map(branch => `
        <div class="branch-card ${branch.includes('Dadar') ? 'special-branch' : ''}">
            <h3><i class="fa-solid fa-building-columns"></i> ${branch}</h3>
            <p>Haala Hojii: Guutuu</p>
            <span class="badge">Sirna Qindaa'aa</span>
        </div>
    `).join('');
}

function renderTransfersTable() {
    const tbody = document.querySelector('#transfers-table tbody');
    if (!tbody) return;
    tbody.innerHTML = appData.transfers.map(tr => `
        <tr>
            <td>${tr.employee}</td>
            <td>${tr.from}</td>
            <td>${tr.to}</td>
            <td>${tr.reason}</td>
            <td><span class="status-badge">${tr.status}</span></td>
        </tr>
    `).join('');
}

function renderRanksList() {
    const list = document.getElementById('ranks-list');
    if (!list) return;
    list.innerHTML = appData.ranks.map(r => `
        <div class="rank-item">
            <h4>${r.name}</h4>
            <p>${r.description}</p>
        </div>
    `).join('');
}

function populateBranchDropdown() {
    const select = document.getElementById('emp-branch');
    if (!select) return;
    select.innerHTML = appData.branches.map(b => `<option value="${b}">${b}</option>`).join('');
}
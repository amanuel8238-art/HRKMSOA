// --- OFFICIAL BRANCHES LIST ---
const branchesList = [
    "Head Office (Addis Ababa)", "Iluu Abaabor", "Jimmaa", "Bunoo Beddellee",  
    "Wallaggaa Bahaa", "Wallaggaa Lixaa", "Horo Guduruu Wallaggaa", "Qellem Wallaggaa",
    "Shawaa Bahaa", "Shawaa Lixaa", "Shawaa Kibba Lixaa", "Shawaa Kaabaa",
    "Baalee", "Baalee Bahaa", "Harargee Bahaa", "Harargee Lixaa",
    "Gujii Bahaa", "Gujii Lixaa", "Booranaa", "Booranaa Bahaa",
    "Arsii", "Arsii Lixaa", "GGLTO", "Dadar", "Magaalaa Shagar",
    "Baatuu", "Aggaroo", "Mayyaa", "Dodolaa", "Shanoo",
    "Aanaa Aallee", "Jimmaa Arjoo", "Eejeree", "Gursum", "Girawaa",
    "Habroo", "Dalloo Mannaa", "Martii", "Roobee"
];

// --- OFFICIAL RANKS & PROMOTION REQUIREMENTS ---
const promotionRequirements = {
    "Konstaabilii": 4, "Gargaaraa Saajin": 3, "Itti Aanaa Saajin": 3,
    "Saajin": 3, "Saajin Ol'aanaa": 3, "Gargaaraa Inspeektaraa": 2,
    "Itti Aanaa Inspeektaraa": 3, "Inspeektaraa": 3, "Inspeektaraa Olaanaa": 3,
    "Itti Aanaa Komandaraa": 3, "Komandaraa": "other",
    "Gargaaraa Komishinaraa": "other", "Itti Aanaa Komishinaraa": "other"
};

const ranksList = Object.keys(promotionRequirements);

let membersData = [];
let usersData = [];

window.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    await fetchMembers();
    await fetchUsers();
    populateDropdowns();
    renderDashboard();
    renderFullMembersTable();
    renderBranchesGrid();
    renderUsersTable();
}

// Backend irraa Miseensota fiduuf (GET)
async function fetchMembers() {
    try {
        const response = await fetch('/api/members');
        membersData = await response.json();
        if (!Array.isArray(membersData)) membersData = [];
    } catch (error) {
        console.error("Dogoggora miseensota fiduu:", error);
        membersData = [];
    }
}

// Backend irraa Useroota fiduuf (GET)
async function fetchUsers() {
    try {
        const response = await fetch('/api/users');
        usersData = await response.json();
        if (!Array.isArray(usersData)) usersData = [];
    } catch (error) {
        console.error("Dogoggora useroota fiduu:", error);
        usersData = [];
    }
}

function populateDropdowns() {
    const filterBranch = document.getElementById('filterBranch');
    const regBranch = document.getElementById('regBranch');
    const filterRank = document.getElementById('filterRank');
    const regRank = document.getElementById('regRank');

    if(!filterBranch || !regBranch) return;

    filterBranch.innerHTML = '<option value="">-- Dameewwan Hundaa --</option>';
    regBranch.innerHTML = '<option value="">-- Damee Filadhu --</option>';
    filterRank.innerHTML = '<option value="">-- Gonfoo Hundaa --</option>';
    regRank.innerHTML = '<option value="">-- Gonfoo Filadhu --</option>';

    branchesList.forEach(b => {
        filterBranch.innerHTML += `<option value="${b}">${b}</option>`;
        regBranch.innerHTML += `<option value="${b}">${b}</option>`;
    });

    ranksList.forEach(r => {
        filterRank.innerHTML += `<option value="${r}">${r}</option>`;
        regRank.innerHTML += `<option value="${r}">${r}</option>`;
    });
}

function switchTab(tabName) {
    const tabs = ['dashboard', 'register', 'members', 'branches', 'users'];
    tabs.forEach(t => {
        const el = document.getElementById(`tab${t.charAt(0).toUpperCase() + t.slice(1)}`);
        const btn = document.getElementById(`tabBtn${t.charAt(0).toUpperCase() + t.slice(1)}`);
        if(el) el.classList.add('hidden');
        if(btn) btn.className = "pb-2 text-slate-500 hover:text-indigo-600 transition";
    });

    const activeEl = document.getElementById(`tab${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`);
    const activeBtn = document.getElementById(`tabBtn${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`);
    if(activeEl) activeEl.classList.remove('hidden');
    if(activeBtn) activeBtn.className = "pb-2 border-b-2 border-indigo-600 text-indigo-600 font-semibold transition";

    if(tabName === 'dashboard') renderDashboard();
    if(tabName === 'members') renderFullMembersTable();
    if(tabName === 'branches') renderBranchesGrid();
    if(tabName === 'users') renderUsersTable();
}

// Funksiinii Login (Seensa Sirnichaa)
async function handleLogin(event) {
    if (event) event.preventDefault();
    
    const usernameInput = document.getElementById('username')?.value.trim();
    const passwordInput = document.getElementById('password')?.value.trim();

    if (!usernameInput || !passwordInput) {
        alert("Maaloo Maqaa Fayyadamaa fi Jecha Darbii guuti!");
        return;
    }

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: usernameInput, password: passwordInput })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            localStorage.setItem('user', data.user);
            localStorage.setItem('role', data.role);
            localStorage.setItem('branch', data.branch);
            
            window.location.reload();
        } else {
            alert(data.message || "Maqaa fayyadamaa ykn jecha darbii dogoggoraati!");
        }
    } catch (err) {
        console.error("Login Error:", err);
        alert("Rakkoo network ykn serveriti jira!");
    }
}

async function handleRegistration(e) {
    e.preventDefault();
    const newMember = {
        name: document.getElementById('regName').value,
        id: document.getElementById('regId').value,
        branch: document.getElementById('regBranch').value,
        rank: document.getElementById('regRank').value,
        promotionDate: document.getElementById('regPromotionDate').value,
        gender: document.getElementById('regGender').value,
        hireYear: document.getElementById('regHireYear').value,
        birthYear: document.getElementById('regBirthYear').value,
        rankSalary: parseFloat(document.getElementById('regRankSalary').value) || 0,
        locationAllowance: parseFloat(document.getElementById('regLocationAllowance').value) || 0,
        foodAllowance: parseFloat(document.getElementById('regFoodAllowance').value) || 0,
        eduLevel: document.getElementById('regEduLevel').value,
        fieldOfStudy: document.getElementById('regFieldOfStudy').value,
        jobPosition: document.getElementById('regJobPosition').value,
        status: document.getElementById('regStatus').value,
        disciplinary: document.getElementById('regDisciplinary').value === "true"
    };

    try {
        const response = await fetch('/api/members', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newMember)
        });
        const result = await response.json();
        
        if(response.ok) {
            alert("Miseensi guyyaa guddinaa fi odeeffannoo guutuu waliin Supabase keessatti milkaa'inaan galmaa'e!");
            document.getElementById('memberForm').reset();
            await fetchMembers();
            switchTab('dashboard');
        } else {
            alert("Dogoggora: " + result.message);
        }
    } catch (err) {
        console.error("Dogoggora galchuu:", err);
        alert("Galmeessuu irratti dogoggora uumame.");
    }
}

async function handleUserRegistration(e) {
    e.preventDefault();
    const newUser = {
        username: document.getElementById('newUsername').value,
        role: document.getElementById('newUserRole').value,
        date: new Date().toISOString().split('T')[0]
    };

    try {
        const response = await fetch('/api/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newUser)
        });
        
        if(response.ok) {
            alert("User haaraan milkaa'inaan uumameera!");
            document.getElementById('userForm').reset();
            await fetchUsers();
            renderUsersTable();
        } else {
            alert("Dogoggora uumuuf yaalame irratti argame.");
        }
    } catch(err) {
        console.error("Dogoggora user:", err);
    }
}

function renderDashboard() {
    if (!Array.isArray(membersData)) membersData = [];
    const total = membersData.length;
    const active = membersData.filter(m => m.status === "Active" || m.status === "active").length;
    const terminated = total - active;

    const statTotalMembers = document.getElementById('statTotalMembers');
    const statActiveMembers = document.getElementById('statActiveMembers');
    const statTerminatedMembers = document.getElementById('statTerminatedMembers');

    if(statTotalMembers) statTotalMembers.textContent = total;
    if(statActiveMembers) statActiveMembers.textContent = active;
    if(statTerminatedMembers) statTerminatedMembers.textContent = terminated;

    const activeList = membersData.filter(m => m.status === "Active" || m.status === "active");
    const male = activeList.filter(m => m.gender === "Dhiira" || m.gender === "dhira").length;
    const female = activeList.filter(m => m.gender === "Dhalaa" || m.gender === "dhalaa").length;

    const malePct = active > 0 ? ((male / active) * 100).toFixed(1) : 0;
    const femalePct = active > 0 ? ((female / active) * 100).toFixed(1) : 0;

    const statMaleCount = document.getElementById('statMaleCount');
    const statFemaleCount = document.getElementById('statFemaleCount');
    const barMale = document.getElementById('barMale');
    const barFemale = document.getElementById('barFemale');

    if(statMaleCount) statMaleCount.textContent = `${male} (${malePct}%)`;
    if(statFemaleCount) statFemaleCount.textContent = `${female} (${femalePct}%)`;
    if(barMale) barMale.style.width = `${malePct}%`;
    if(barFemale) barFemale.style.width = `${femalePct}%`;

    renderFilteredTable();
}

function applyFilters() { renderFilteredTable(); }

function resetFilters() {
    const filterBranch = document.getElementById('filterBranch');
    const filterRank = document.getElementById('filterRank');
    const filterSearch = document.getElementById('filterSearch');

    if(filterBranch) filterBranch.value = "";
    if(filterRank) filterRank.value = "";
    if(filterSearch) filterSearch.value = "";
    renderFilteredTable();
}

function renderFilteredTable() {
    const tbody = document.getElementById('filteredTableBody');
    if(!tbody) return;
    tbody.innerHTML = "";

    if (!Array.isArray(membersData)) membersData = [];

    const bFilter = document.getElementById('filterBranch')?.value || "";
    const rFilter = document.getElementById('filterRank')?.value || "";
    const sFilter = document.getElementById('filterSearch')?.value.toLowerCase() || "";

    const filtered = membersData.filter(m => {
        let matchB = !bFilter || m.branch === bFilter;
        let matchR = !rFilter || m.rank === rFilter;
        let matchS = !sFilter || (m.name && m.name.toLowerCase().includes(sFilter)) || (m.id && m.id.toLowerCase().includes(sFilter));
        return matchB && matchR && matchS;
    });

    if(filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-slate-400">Daataan argame hin jiru.</td></tr>`;
        return;
    }

    filtered.forEach((m) => {
        const totalSalary = (parseFloat(m.rankSalary) || 0) + (parseFloat(m.locationAllowance) || 0) + (parseFloat(m.foodAllowance) || 0);
        tbody.innerHTML += `
            <tr class="hover:bg-slate-50">
                <td class="p-2.5">
                    <div class="font-bold text-slate-800">${m.name}</div>
                    <div class="text-[10px] text-slate-500 font-mono">ID: ${m.id} | ${m.gender}</div>
                </td>
                <td class="p-2.5">
                    <div class="font-medium text-slate-700">${m.branch}</div>
                    <div class="text-[10px] text-indigo-600">${m.jobPosition || '-'}</div>
                </td>
                <td class="p-2.5">
                    <div class="font-semibold text-slate-900">${m.rank}</div>
                    <div class="text-[10px] text-emerald-600">ETB ${totalSalary.toLocaleString()}</div>
                </td>
                <td class="p-2.5 text-slate-600">
                    <div>Qac.: ${m.hireYear}</div>
                    <div class="text-[10px] text-slate-400">Guddina: ${m.promotionDate || '-'}</div>
                </td>
                <td class="p-2.5">
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-700">${m.status}</span>
                </td>
                <td class="p-2.5">
                    <span class="text-[10px] text-slate-400">-</span>
                </td>
            </tr>
        `;
    });
}

function renderFullMembersTable() {
    const tbody = document.getElementById('fullMembersTableBody');
    if(!tbody) return;
    tbody.innerHTML = "";
    
    if (!Array.isArray(membersData)) membersData = [];

    const totalBadge = document.getElementById('totalBadge');
    if(totalBadge) totalBadge.textContent = `${membersData.length} Total`;

    membersData.forEach((m) => {
        const totalSalary = (parseFloat(m.rankSalary) || 0) + (parseFloat(m.locationAllowance) || 0) + (parseFloat(m.foodAllowance) || 0);
        tbody.innerHTML += `
            <tr class="hover:bg-slate-50">
                <td class="p-3">
                    <div class="font-bold text-slate-800">${m.name}</div>
                    <div class="text-[10px] text-slate-500 font-mono">ID: ${m.id}</div>
                </td>
                <td class="p-3">
                    <div class="font-medium text-slate-700">${m.branch}</div>
                    <div class="text-[10px] text-indigo-600">${m.jobPosition || '-'}</div>
                </td>
                <td class="p-3">
                    <div class="font-semibold text-slate-900">${m.rank}</div>
                    <div class="text-[10px] text-emerald-600">ETB ${totalSalary.toLocaleString()}</div>
                </td>
                <td class="p-3 text-slate-600">${m.eduLevel || '-'}</td>
                <td class="p-3 text-slate-600">Qac: ${m.hireYear}</td>
                <td class="p-3"><span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-700">${m.status}</span></td>
                <td class="p-3"><span class="text-[10px] text-slate-400">-</span></td>
            </tr>
        `;
    });
}

function renderBranchesGrid() {
    const grid = document.getElementById('branchesGrid');
    const previewList = document.getElementById('branchPreviewList');
    if(!grid) return;

    if (!Array.isArray(membersData)) membersData = [];

    grid.innerHTML = "";
    if(previewList) previewList.innerHTML = "";

    branchesList.forEach(b => {
        const count = membersData.filter(m => m.branch === b && (m.status === "Active" || m.status === "active")).length;
        
        grid.innerHTML += `
            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 flex flex-col justify-between space-y-2">
                <div>
                    <h4 class="font-bold text-indigo-900 text-xs">${b}</h4>
                    <p class="text-[10px] text-slate-500 mt-1">Komishinii Manneen Sirreessaa Oromiyaa</p>
                </div>
                <div class="flex justify-between items-center pt-2 border-t border-slate-200">
                    <span class="text-[10px] text-slate-600 font-medium">Active:</span>
                    <span class="bg-indigo-100 text-indigo-700 font-bold px-2 py-0.5 rounded-full text-xs">${count}</span>
                </div>
            </div>
        `;

        if(previewList) {
            previewList.innerHTML += `
                <div class="flex justify-between items-center py-1 border-b border-slate-100">
                    <span class="truncate pr-2 text-slate-700">${b}</span>
                    <span class="bg-slate-100 text-slate-800 px-2 py-0.5 rounded text-[10px] font-bold">${count}</span>
                </div>
            `;
        }
    });
}

function renderUsersTable() {
    const tbody = document.getElementById('usersTableBody');
    if(!tbody) return;
    tbody.innerHTML = "";
    
    if (!Array.isArray(usersData)) usersData = [];

    const userCountBadge = document.getElementById('userCountBadge');
    if(userCountBadge) userCountBadge.textContent = `${usersData.length} Users`;

    usersData.forEach(u => {
        tbody.innerHTML += `
            <tr class="hover:bg-slate-50">
                <td class="p-3 font-bold text-slate-800">${u.username}</td>
                <td class="p-3 text-indigo-600 font-semibold">${u.role || u.branch || '-'}</td>
                <td class="p-3 text-slate-500">${u.date || '-'}</td>
                <td class="p-3 text-slate-400">-</td>
            </tr>
        `;
    });
}
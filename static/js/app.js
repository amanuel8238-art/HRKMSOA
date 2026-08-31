// --- OFFICIAL BRANCHES LIST ---
const branchesList = [
    "Head Office (Addis Ababa)",
    "Iluu Abaabor", 
    "Jimmaa", 
    "Bunoo Beddellee", 
    "Wallaggaa Bahaa",
    "Wallaggaa Lixaa", 
    "Horo Guduruu Wallaggaa", 
    "Qellem Wallaggaa",
    "Shawaa Bahaa", 
    "Shawaa Lixaa", 
    "Shawaa Kibba Lixaa", 
    "Shawaa Kaabaa",
    "Baalee", 
    "Baalee Bahaa", 
    "Harargee Bahaa", 
    "Harargee Lixaa",
    "Gujii Bahaa", 
    "Gujii Lixaa", 
    "Booranaa", 
    "Booranaa Bahaa",
    "Arsii", 
    "Arsii Lixaa", 
    "GGLTO", 
    "Dadar", 
    "Magaalaa Shagar",
    "Baatuu", 
    "Aggaroo", 
    "Mayyaa", 
    "Dodolaa", 
    "Shanoo",
    "Aanaa Aallee", 
    "Jimmaa Arjoo", 
    "Eejeree", 
    "Gursum", 
    "Girawaa",
    "Habroo", 
    "Dalloo Mannaa", 
    "Martii", 
    "Roobee"
];

// --- OFFICIAL RANKS & PROMOTION REQUIREMENTS ---
const promotionRequirements = {
    "Konstaabilii": 4,
    "Gargaaraa Saajin": 3,
    "Itti Aanaa Saajin": 3,
    "Saajin": 3,
    "Saajin Ol'aanaa": 3,
    "Gargaaraa Inspeektaraa": 2,
    "Itti Aanaa Inspeektaraa": 3,
    "Inspeektaraa": 3,
    "Inspeektaraa Olaanaa": 3,
    "Itti Aanaa Komandaraa": 3,
    "Komandaraa": "other",
    "Gargaaraa Komishinaraa": "other",
    "Itti Aanaa Komishinaraa": "other"
};

const ranksList = Object.keys(promotionRequirements);

let membersData = JSON.parse(localStorage.getItem('hrkmso_members')) || [
    { 
        name: "Amsaaluu Tasfaa", id: "HRK-001", branch: "Head Office (Addis Ababa)", rank: "Konstaabilii", promotionDate: "2019-06-15", gender: "Dhiira", 
        hireYear: 2015, birthYear: 1995, rankSalary: 5500, locationAllowance: 500, foodAllowance: 1000, 
        eduLevel: "Diploma", fieldOfStudy: "Law", jobPosition: "Poolisii Tajaajila", status: "Active", disciplinary: false 
    }
];

let usersData = JSON.parse(localStorage.getItem('hrkmso_users')) || [
    { username: "admin_hrkmso", role: "Admin", date: "2026-07-01" },
    { username: "manager_dadar", role: "Branch Manager", date: "2026-07-05" }
];

function saveData() {
    localStorage.setItem('hrkmso_members', JSON.stringify(membersData));
    localStorage.setItem('hrkmso_users', JSON.stringify(usersData));
}

window.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    populateDropdowns();
    renderDashboard();
    renderFullMembersTable();
    renderBranchesGrid();
    renderUsersTable();
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

function handleRegistration(e) {
    e.preventDefault();
    const name = document.getElementById('regName').value;
    const id = document.getElementById('regId').value;
    const branch = document.getElementById('regBranch').value;
    const rank = document.getElementById('regRank').value;
    const promotionDate = document.getElementById('regPromotionDate').value;
    const gender = document.getElementById('regGender').value;
    const hireYear = document.getElementById('regHireYear').value;
    const birthYear = document.getElementById('regBirthYear').value;
    
    const rankSalary = parseFloat(document.getElementById('regRankSalary').value) || 0;
    const locationAllowance = parseFloat(document.getElementById('regLocationAllowance').value) || 0;
    const foodAllowance = parseFloat(document.getElementById('regFoodAllowance').value) || 0;
    const eduLevel = document.getElementById('regEduLevel').value;
    const fieldOfStudy = document.getElementById('regFieldOfStudy').value;
    const jobPosition = document.getElementById('regJobPosition').value;

    const status = document.getElementById('regStatus').value;
    const disciplinary = document.getElementById('regDisciplinary').value === "true";

    if(membersData.some(m => m.id === id)) {
        alert("ID kana qabu duraanuu galmeeffameera!");
        return;
    }

    membersData.push({ 
        name, id, branch, rank, promotionDate, gender, hireYear, birthYear, 
        rankSalary, locationAllowance, foodAllowance, eduLevel, fieldOfStudy, jobPosition, 
        status, disciplinary 
    });
    saveData();
    alert("Miseensi guyyaa guddinaa fi odeeffannoo guutuu waliin milkaa'inaan galmeeffame!");
    document.getElementById('memberForm').reset();
    switchTab('dashboard');
}

function handleUserRegistration(e) {
    e.preventDefault();
    const username = document.getElementById('newUsername').value;
    const role = document.getElementById('newUserRole').value;
    const date = new Date().toISOString().split('T')[0];

    usersData.push({ username, role, date });
    saveData();
    alert("User haaraan milkaa'inaan uumameera!");
    document.getElementById('userForm').reset();
    renderUsersTable();
}

function renderDashboard() {
    const total = membersData.length;
    const active = membersData.filter(m => m.status === "Active").length;
    const terminated = total - active;

    const statTotalMembers = document.getElementById('statTotalMembers');
    const statActiveMembers = document.getElementById('statActiveMembers');
    const statTerminatedMembers = document.getElementById('statTerminatedMembers');

    if(statTotalMembers) statTotalMembers.textContent = total;
    if(statActiveMembers) statActiveMembers.textContent = active;
    if(statTerminatedMembers) statTerminatedMembers.textContent = terminated;

    const activeList = membersData.filter(m => m.status === "Active");
    const male = activeList.filter(m => m.gender === "Dhiira").length;
    const female = activeList.filter(m => m.gender === "Dhalaa").length;

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

function applyFilters() {
    renderFilteredTable();
}

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

    const bFilterEl = document.getElementById('filterBranch');
    const rFilterEl = document.getElementById('filterRank');
    const sFilterEl = document.getElementById('filterSearch');

    const bFilter = bFilterEl ? bFilterEl.value : "";
    const rFilter = rFilterEl ? rFilterEl.value : "";
    const sFilter = sFilterEl ? sFilterEl.value.toLowerCase() : "";

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
        const originalIndex = membersData.indexOf(m);
        tbody.innerHTML += `
            <tr class="hover:bg-slate-50">
                <td class="p-2.5">
                    <div class="font-bold text-slate-800">${m.name}</div>
                    <div class="text-[10px] text-slate-500 font-mono">ID: ${m.id} | ${m.gender}</div>
                </td>
                <td class="p-2.5">
                    <div class="font-medium text-slate-700">${m.branch}</div>
                    <div class="text-[10px] text-indigo-600">${m.jobPosition}</div>
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
                    <button onclick="deleteMember(${originalIndex})" class="bg-rose-500 hover:bg-rose-600 text-white px-2 py-1 rounded text-[10px]">Haqi</button>
                </td>
            </tr>
        `;
    });
}

function renderFullMembersTable() {
    const tbody = document.getElementById('fullMembersTableBody');
    if(!tbody) return;
    tbody.innerHTML = "";
    
    const totalBadge = document.getElementById('totalBadge');
    if(totalBadge) totalBadge.textContent = `${membersData.length} Total`;

    membersData.forEach((m, idx) => {
        const totalSalary = (parseFloat(m.rankSalary) || 0) + (parseFloat(m.locationAllowance) || 0) + (parseFloat(m.foodAllowance) || 0);
        tbody.innerHTML += `
            <tr class="hover:bg-slate-50">
                <td class="p-3">
                    <div class="font-bold text-slate-800">${m.name}</div>
                    <div class="text-[10px] text-slate-500 font-mono">ID: ${m.id}</div>
                </td>
                <td class="p-3">
                    <div class="font-medium text-slate-700">${m.branch}</div>
                    <div class="text-[10px] text-indigo-600">${m.jobPosition}</div>
                </td>
                <td class="p-3">
                    <div class="font-semibold text-slate-900">${m.rank}</div>
                    <div class="text-[10px] text-emerald-600">ETB ${totalSalary.toLocaleString()}</div>
                </td>
                <td class="p-3 text-slate-600">${m.eduLevel}</td>
                <td class="p-3 text-slate-600">Qac: ${m.hireYear}</td>
                <td class="p-3"><span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-700">${m.status}</span></td>
                <td class="p-3"><button onclick="deleteMember(${idx})" class="bg-rose-500 hover:bg-rose-600 text-white px-2.5 py-1 rounded text-[10px]">Haqi</button></td>
            </tr>
        `;
    });
}

function renderBranchesGrid() {
    const grid = document.getElementById('branchesGrid');
    const previewList = document.getElementById('branchPreviewList');
    if(!grid) return;

    grid.innerHTML = "";
    if(previewList) previewList.innerHTML = "";

    branchesList.forEach(b => {
        const count = membersData.filter(m => m.branch === b && m.status === "Active").length;
        
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
    
    const userCountBadge = document.getElementById('userCountBadge');
    if(userCountBadge) userCountBadge.textContent = `${usersData.length} Users`;

    usersData.forEach(u => {
        tbody.innerHTML += `
            <tr class="hover:bg-slate-50">
                <td class="p-3 font-bold text-slate-800">${u.username}</td>
                <td class="p-3 text-indigo-600 font-semibold">${u.role}</td>
                <td class="p-3 text-slate-500">${u.date}</td>
                <td class="p-3 text-slate-400">-</td>
            </tr>
        `;
    });
}

function deleteMember(idx) {
    if(confirm("Miseensa kana haquu barbaaddaa?")) {
        membersData.splice(idx, 1);
        saveData();
        initApp();
    }
}
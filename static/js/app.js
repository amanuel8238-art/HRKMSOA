// --- GLOBAL APP STATE ---
let membersData = [];
let branchesData = [];
let usersData = [];
let currentUser = null;

// Komishinii Manneen Sirreessaa Oromiyaa - 39 Official Units / Branches
const officialBranches = [
    "Head Office (Finfinnee)",
    "Damee Qajeelcha Waliigalaa",
    "Godina Shawaa Bahaa (Adama)",
    "Godina Shawaa Lixaa (Amboo)",
    "Godina Shawaa Kaabaa (Fichee)",
    "Godina Shawaa Kibba-Lixaa (Waliso)",
    "Godina Arsii (Asalla)",
    "Godina Arsii Lixaa (Shaashamannoo)",
    "Godina Baalee (Robe)",
    "Godina Baalee Bahaa (Gindhir)",
    "Godina Harargee Bahaa (Ciroo)",
    "Godina Harargee Lixaa (Batee)",
    "Godina Gujii (Neeqee)",
    "Godina Gujii Lixaa (Bule Horaa)",
    "Godina Boorana (Yaabelloo)",
    "Godina Horroo Guduruu Wallaggaa (Shaambuu)",
    "Godina Wallagga Bahaa (Naqamte)",
    "Godina Wallagga Lixaa (Giidbiidha)",
    "Godina Qellem Wallaggaa (Dambi Doloo)",
    "Godina Iluu Abaaboor (Mattuu)",
    "Godina Baddaa Roggee (Metuu)",
    "Godina Kelem Bahaa",
    "Aanaa Dadar Sirreessaa (Dadar)",
    "Manni Sirreessaa Magaalaa Finfinnee",
    "Manni Sirreessaa Magaalaa Adama",
    "Manni Sirreessaa Magaalaa Shaashamannoo",
    "Manni Sirreessaa Magaalaa Naqamte",
    "Manni Sirreessaa Magaalaa Jimmaa",
    "Manni Sirreessaa Magaalaa Amboo",
    "Manni Sirreessaa Magaalaa Asalla",
    "Manni Sirreessaa Magaalaa Robe",
    "Manni Sirreessaa Magaalaa Biishoftuu",
    "Manni Sirreessaa Magaalaa Adaamaa Addaa",
    "Manni Sirreessaa Magaalaa Waliso",
    "Manni Sirreessaa Magaalaa Mattuu",
    "Manni Sirreessaa Magaalaa Yaabelloo",
    "Manni Sirreessaa Magaalaa Ciroo",
    "Manni Sirreessaa Magaalaa Bule Horaa",
    "Manni Sirreessaa Magaalaa Dambi Doloo"
];

// Official Ranks (Gonfoo Sirreessaa)
const officialRanks = [
    "Komiishinara Jeneraalaa",
    "Komiishinara Ittaanaa Jeneraalaa",
    "Komiishinara",
    "Komiishinara Dooktar",
    "Komiishinara Ittaanaa",
    "Komiishinara Qopheessaa",
    "Komiishinara Qopheessaa Ittaanaa",
    "Komiishinara Ol'aanaa",
    "Komiishinara I/A",
    "Komiishinara Komaandara",
    "Komaandara Ol'aanaa",
    "Komaandara",
    "Komaandara Ittaanaa",
    "Inspeekitara Ol'aanaa",
    "Inspeekitara",
    "Inspeekitara Ittaanaa",
    "Sajjaani Ol'aanaa",
    "Sajjaani",
    "Sajjaani Ittaanaa",
    "Konstabeli",
    "Miseensa Instituutiichaa"
];

// Initialize on DOM Load
document.addEventListener("DOMContentLoaded", () => {
    initializeStaticDropdowns();
    checkExistingSession();
});

function initializeStaticDropdowns() {
    // Populate Branches
    const branchSelects = ["regBranch", "filterBranch", "newUserBranch"];
    branchSelects.forEach(id => {
        const el = document.getElementById(id);
        if(!el) return;
        // Keep default option if filter
        let defaultHTML = el.innerHTML.includes("Hundaa") ? el.innerHTML.split("</option>")[0] + "</option>" : '<option value="">-- Damee Filadhu --</option>';
        if(id === "filterBranch") defaultHTML = '<option value="">-- Dameewwan Hundaa --</option>';
        
        el.innerHTML = defaultHTML;
        officialBranches.forEach(b => {
            const opt = document.createElement("option");
            opt.value = b;
            opt.textContent = b;
            el.appendChild(opt);
        });
    });

    // Populate Ranks
    const rankSelects = ["regRank", "filterRank"];
    rankSelects.forEach(id => {
        const el = document.getElementById(id);
        if(!el) return;
        let defaultHTML = id === "filterRank" ? '<option value="">-- Gulaataa Gonfoo Hundaa --</option>' : '<option value="">-- Gonfoo Filadhu --</option>';
        el.innerHTML = defaultHTML;
        officialRanks.forEach(r => {
            const opt = document.createElement("option");
            opt.value = r;
            opt.textContent = r;
            el.appendChild(opt);
        });
    });

    renderBranchesGrid();
}

// --- AUTHENTICATION & SESSIONS ---
function handleLogin(e) {
    e.preventDefault();
    const u = document.getElementById("loginUsername").value.trim();
    const p = document.getElementById("loginPassword").value.trim();

    // Default admin fallback
    if(u === "admin_hrkmso" && p === "admin123") {
        currentUser = { username: "admin_hrkmso", branch: "Head Office (Finfinnee)" };
        localStorage.setItem("hrkmso_user", JSON.stringify(currentUser));
        startApp();
        return;
    }

    // Check custom registered users
    const found = usersData.find(usr => usr.username === u && usr.password === p);
    if(found) {
        currentUser = found;
        localStorage.setItem("hrkmso_user", JSON.stringify(currentUser));
        startApp();
    } else {
        alert("Maqaa Fayyadamaa ykn Jecha Darbii dogoggora / Invalid credentials!");
    }
}

function checkExistingSession() {
    const saved = localStorage.getItem("hrkmso_user");
    if(saved) {
        currentUser = JSON.parse(saved);
        startApp();
    }
}

function startApp() {
    document.getElementById("loginScreen").classList.add("hidden");
    document.getElementById("mainApp").classList.remove("hidden");
    document.getElementById("currentAdminUser").textContent = currentUser.username;
    
    // Load local mock data if empty
    loadInitialData();
    updateDashboardStats();
    renderFilteredTable();
    renderMembersTable();
    renderUsersTable();
}

function handleLogout() {
    localStorage.removeItem("hrkmso_user");
    currentUser = null;
    document.getElementById("mainApp").classList.add("hidden");
    document.getElementById("loginScreen").classList.remove("hidden");
}

// --- NAVIGATION TABS ---
function switchTab(tabName) {
    const tabs = ["dashboard", "register", "members", "branches", "users"];
    tabs.forEach(t => {
        const contentEl = document.getElementById(`tab${t.charAt(0).toUpperCase() + t.slice(1)}`);
        const btnEl = document.getElementById(`tabBtn${t.charAt(0).toUpperCase() + t.slice(1)}`);
        if(contentEl) contentEl.classList.add("hidden");
        if(btnEl) {
            btnEl.classList.remove("border-b-2", "border-indigo-600", "text-indigo-600");
            btnEl.classList.add("text-slate-500");
        }
    });

    const activeContent = document.getElementById(`tab${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`);
    const activeBtn = document.getElementById(`tabBtn${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`);
    if(activeContent) activeContent.classList.remove("hidden");
    if(activeBtn) {
        activeBtn.classList.add("border-b-2", "border-indigo-600", "text-indigo-600");
        activeBtn.classList.remove("text-slate-500");
    }
}

// --- DATA MANAGEMENT & INITIAL MOCK DATA ---
function loadInitialData() {
    const localMembers = localStorage.getItem("hrkmso_members");
    const localUsers = localStorage.getItem("hrkmso_users");

    if(localMembers) {
        membersData = JSON.parse(localMembers);
    } else {
        // Sample data for demonstration
        membersData = [
            {
                name: "Abebe Kebede",
                id: "HRK-001",
                branch: "Head Office (Finfinnee)",
                rank: "Inspeekitara Ol'aanaa",
                rankDay: "12", rankMonth: "05", rankYear: "2014",
                gender: "Dhiira",
                hireDay: "10", hireMonth: "02", hireYear: "2010",
                birthDay: "15", birthMonth: "08", birthYear: "1988",
                rankSalary: 7500,
                locationAllowance: 1000,
                foodAllowance: 1200,
                eduLevel: "Degree",
                fieldOfStudy: "Law",
                jobPosition: "Hoogganaa Qorannoo",
                status: "Active"
            },
            {
                name: "Tirunesh Mamo",
                id: "HRK-002",
                branch: "Aanaa Dadar Sirreessaa (Dadar)",
                rank: "Inspeekitara",
                rankDay: "04", rankMonth: "10", rankYear: "2015",
                gender: "Dhalaa",
                hireDay: "20", hireMonth: "11", hireYear: "2012",
                birthDay: "22", birthMonth: "03", birthYear: "1992",
                rankSalary: 6200,
                locationAllowance: 800,
                foodAllowance: 1200,
                eduLevel: "Diploma",
                fieldOfStudy: "Management",
                jobPosition: "Bulchiinsa Humna Namaa",
                status: "Active"
            }
        ];
        localStorage.setItem("hrkmso_members", JSON.stringify(membersData));
    }

    if(localUsers) {
        usersData = JSON.parse(localUsers);
    } else {
        usersData = [
            { username: "dadar_manager", password: "password123", branch: "Aanaa Dadar Sirreessaa (Dadar)" }
        ];
        localStorage.setItem("hrkmso_users", JSON.stringify(usersData));
    }
}

function saveMembers() {
    localStorage.setItem("hrkmso_members", JSON.stringify(membersData));
    updateDashboardStats();
    renderFilteredTable();
    renderMembersTable();
    renderBranchesGrid();
}

function saveUsers() {
    localStorage.setItem("hrkmso_users", JSON.stringify(usersData));
    renderUsersTable();
}

// --- REGISTRATION & EDITING FORM ---
function handleRegistration(e) {
    e.preventDefault();
    const editIndex = document.getElementById("editMemberIndex").value;

    const memberObj = {
        name: document.getElementById("regName").value.trim(),
        id: document.getElementById("regId").value.trim(),
        branch: document.getElementById("regBranch").value,
        rank: document.getElementById("regRank").value,
        rankDay: document.getElementById("regRankDay").value,
        rankMonth: document.getElementById("regRankMonth").value,
        rankYear: document.getElementById("regRankYear").value,
        gender: document.getElementById("regGender").value,
        hireDay: document.getElementById("regHireDay").value,
        hireMonth: document.getElementById("regHireMonth").value,
        hireYearVal: document.getElementById("regHireYearVal").value,
        birthDay: document.getElementById("regBirthDay").value,
        birthMonth: document.getElementById("regBirthMonth").value,
        birthYearVal: document.getElementById("regBirthYearVal").value,
        rankSalary: parseFloat(document.getElementById("regRankSalary").value) || 0,
        locationAllowance: parseFloat(document.getElementById("regLocationAllowance").value) || 0,
        foodAllowance: parseFloat(document.getElementById("regFoodAllowance").value) || 0,
        eduLevel: document.getElementById("regEduLevel").value,
        fieldOfStudy: document.getElementById("regFieldOfStudy").value.trim(),
        jobPosition: document.getElementById("regJobPosition").value.trim(),
        status: document.getElementById("regStatus").value
    };

    if(editIndex === "") {
        membersData.push(memberObj);
        alert("Miseensi haaraan milkaa'inaan galmaa'eera!");
    } else {
        membersData[editIndex] = memberObj;
        alert("Gulaalliin miseensichaa haaromfameera!");
        resetRegistrationForm();
    }

    document.getElementById("memberForm").reset();
    saveMembers();
    switchTab("dashboard");
}

function editMember(index) {
    const m = membersData[index];
    document.getElementById("editMemberIndex").value = index;
    document.getElementById("regName").value = m.name;
    document.getElementById("regId").value = m.id;
    document.getElementById("regBranch").value = m.branch;
    document.getElementById("regRank").value = m.rank;
    document.getElementById("regRankDay").value = m.rankDay || "";
    document.getElementById("regRankMonth").value = m.rankMonth || "";
    document.getElementById("regRankYear").value = m.rankYear || "";
    document.getElementById("regGender").value = m.gender;
    document.getElementById("regHireDay").value = m.hireDay || "";
    document.getElementById("regHireMonth").value = m.hireMonth || "";
    document.getElementById("regHireYearVal").value = m.hireYearVal || "";
    document.getElementById("regBirthDay").value = m.birthDay || "";
    document.getElementById("regBirthMonth").value = m.birthMonth || "";
    document.getElementById("regBirthYearVal").value = m.birthYearVal || "";
    document.getElementById("regRankSalary").value = m.rankSalary;
    document.getElementById("regLocationAllowance").value = m.locationAllowance;
    document.getElementById("regFoodAllowance").value = m.foodAllowance;
    document.getElementById("regEduLevel").value = m.eduLevel;
    document.getElementById("regFieldOfStudy").value = m.fieldOfStudy;
    document.getElementById("regJobPosition").value = m.jobPosition;
    document.getElementById("regStatus").value = m.status;

    document.getElementById("regFormTitle").textContent = "Gulaali / Update Miseensa: " + m.name;
    document.getElementById("submitRegBtn").textContent = "Miseensa Haaromsi (Update)";
    document.getElementById("cancelEditBtn").classList.remove("hidden");

    switchTab("register");
}

function resetRegistrationForm() {
    document.getElementById("memberForm").reset();
    document.getElementById("editMemberIndex").value = "";
    document.getElementById("regFormTitle").textContent = "Galmee Miseensa Haaraa (Ethiopian Calendar: Guyyaa/Ji'a/Bara)";
    document.getElementById("submitRegBtn").textContent = "Miseensa Galmeessi";
    document.getElementById("cancelEditBtn").classList.add("hidden");
}

function deleteMember(index) {
    if(confirm("Miseensa kana haquu keetti mirkanaaftee?")) {
        membersData.splice(index, 1);
        saveMembers();
    }
}

// --- USERS MANAGEMENT FUNCTIONS ---
function handleUserRegistration(e) {
    e.preventDefault();
    const editIdx = document.getElementById("editUserIndex").value;
    const usr = document.getElementById("newUsername").value.trim();
    const pwd = document.getElementById("newPassword").value.trim();
    const brn = document.getElementById("newUserBranch").value;

    const userObj = { username: usr, password: pwd, branch: brn };

    if(editIdx === "") {
        usersData.push(userObj);
        alert("User haaraan milkaa'inaan uumameera!");
    } else {
        usersData[editIdx] = userObj;
        alert("Daataan userichaa haaromfameera!");
        resetUserForm();
    }

    document.getElementById("userForm").reset();
    saveUsers();
}

function editUser(index) {
    const u = usersData[index];
    document.getElementById("editUserIndex").value = index;
    document.getElementById("newUsername").value = u.username;
    document.getElementById("newPassword").value = u.password;
    document.getElementById("newUserBranch").value = u.branch;
    document.getElementById("submitUserBtn").textContent = "User Haaromsi";
    document.getElementById("cancelUserEditBtn").classList.remove("hidden");
}

function resetUserForm() {
    document.getElementById("userForm").reset();
    document.getElementById("editUserIndex").value = "";
    document.getElementById("submitUserBtn").textContent = "User Galmeessi";
    document.getElementById("cancelUserEditBtn").classList.add("hidden");
}

function deleteUser(index) {
    if(confirm("User kana haquu keetti mirkanaaftee?")) {
        usersData.splice(index, 1);
        saveUsers();
    }
}

function renderUsersTable() {
    const tbody = document.getElementById("usersTableBody");
    if(!tbody) return;
    tbody.innerHTML = "";
    document.getElementById("userCountBadge").textContent = `${usersData.length} Users`;

    if(usersData.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-slate-400">Userni tokkollee hin jiru.</td></tr>`;
        return;
    }

    usersData.forEach((u, index) => {
        tbody.innerHTML += `
            <tr class="hover:bg-slate-50">
                <td class="p-3 font-semibold text-slate-800">${u.username}</td>
                <td class="p-3 font-mono text-slate-600">${u.password}</td>
                <td class="p-3 text-slate-600">${u.branch}</td>
                <td class="p-3 flex gap-2">
                    <button onclick="editUser(${index})" class="bg-amber-500 hover:bg-amber-600 text-white px-2 py-1 rounded text-[10px]">Gulaali</button>
                    <button onclick="deleteUser(${index})" class="bg-rose-500 hover:bg-rose-600 text-white px-2 py-1 rounded text-[10px]">Haqi</button>
                </td>
            </tr>
        `;
    });
}

// --- DASHBOARD & TABLES RENDERING ---
function updateDashboardStats() {
    const total = membersData.length;
    const active = membersData.filter(m => m.status === "Active").length;
    const terminated = total - active;

    document.getElementById("statTotalMembers").textContent = total;
    document.getElementById("statActiveMembers").textContent = active;
    document.getElementById("statTerminatedMembers").textContent = terminated;
    document.getElementById("statBranchCountDisplay").textContent = officialBranches.length;

    // Gender stats
    const activeList = membersData.filter(m => m.status === "Active");
    const male = activeList.filter(m => m.gender === "Dhiira").length;
    const female = activeList.filter(m => m.gender === "Dhalaa").length;

    const malePct = active > 0 ? ((male / active) * 100).toFixed(1) : 0;
    const femalePct = active > 0 ? ((female / active) * 100).toFixed(1) : 0;

    document.getElementById("statMaleCount").textContent = `${male} (${malePct}%)`;
    document.getElementById("barMale.style") // safe check
    const barM = document.getElementById("barMale");
    const barF = document.getElementById("barFemale");
    if(barM) barM.style.width = `${malePct}%`;
    if(barF) barF.style.width = `${femalePct}%`;
}

function applyFilters() {
    renderFilteredTable();
}

function resetFilters() {
    document.getElementById("filterBranch").value = "";
    document.getElementById("filterRank").value = "";
    document.getElementById("filterSearch").value = "";
    renderFilteredTable();
}

function getFilteredMembers() {
    const bFilter = document.getElementById("filterBranch").value;
    const rFilter = document.getElementById("filterRank").value;
    const sFilter = document.getElementById("filterSearch").value.toLowerCase();

    return membersData.filter(m => {
        let matchB = !bFilter || m.branch === bFilter;
        let matchR = !rFilter || m.rank === rFilter;
        let matchS = !sFilter || m.name.toLowerCase().includes(sFilter) || m.id.toLowerCase().includes(sFilter) || (m.rankYear && m.rankYear.includes(sFilter));
        return matchB && matchR && matchS;
    });
}

function renderFilteredTable() {
    const tbody = document.getElementById("filteredTableBody");
    if(!tbody) return;
    tbody.innerHTML = "";

    const filtered = getFilteredMembers();

    if(filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-slate-400">Daataan argame hin jiru.</td></tr>`;
        return;
    }

    filtered.forEach((m, idx) => {
        // find original index
        const originalIndex = membersData.indexOf(m);
        const totalSalary = (parseFloat(m.rankSalary) || 0) + (parseFloat(m.locationAllowance) || 0) + (parseFloat(m.foodAllowance) || 0);

        tbody.innerHTML += `
            <tr class="hover:bg-slate-50">
                <td class="p-2.5">
                    <div class="font-bold text-slate-800">${m.name}</div>
                    <div class="text-[10px] text-slate-500 font-mono">ID: ${m.id} | Saala: ${m.gender}</div>
                </td>
                <td class="p-2.5">
                    <div class="font-medium text-slate-700">${m.branch}</div>
                    <div class="text-[10px] text-indigo-600">${m.jobPosition || '-'}</div>
                </td>
                <td class="p-2.5">
                    <div class="font-semibold text-slate-900">${m.rank}</div>
                    <div class="text-[10px] text-emerald-600">Mindaa Waliigalaa: ETB ${totalSalary.toLocaleString()}</div>
                </td>
                <td class="p-2.5 text-slate-600">
                    <div>Qacar.: ${m.hireDay || '-'}/${m.hireMonth || '-'}/${m.hireYearVal || '-'}</div>
                    <div class="text-[10px] text-slate-400">Gonfoo: ${m.rankDay || '-'}/${m.rankMonth || '-'}/${m.rankYear || '-'}</div>
                </td>
                <td class="p-2.5">
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold ${m.status === 'Active' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}">${m.status}</span>
                </td>
                <td class="p-2.5 flex gap-1">
                    <button onclick="editMember(${originalIndex})" class="bg-amber-500 hover:bg-amber-600 text-white px-2 py-1 rounded text-[10px]">Gulaali</button>
                    <button onclick="deleteMember(${originalIndex})" class="bg-rose-500 hover:bg-rose-600 text-white px-2 py-1 rounded text-[10px]">Haqi</button>
                </td>
            </tr>
        `;
    });
}

function renderMembersTable() {
    const tbody = document.getElementById("fullMembersTableBody");
    if(!tbody) return;
    tbody.innerHTML = "";
    document.getElementById("totalBadge").textContent = `${membersData.length} Total`;

    if(membersData.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="p-4 text-center text-slate-400">Miseensi galmaa'e hin jiru.</td></tr>`;
        return;
    }

    membersData.forEach((m, index) => {
        const totalSalary = (parseFloat(m.rankSalary) || 0) + (parseFloat(m.locationAllowance) || 0) + (parseFloat(m.foodAllowance) || 0);
        tbody.innerHTML += `
            <tr class="hover:bg-slate-50">
                <td class="p-3">
                    <div class="font-bold text-slate-800">${m.name}</div>
                    <div class="text-[10px] text-slate-500 font-mono">ID: ${m.id} | Saala: ${m.gender}</div>
                </td>
                <td class="p-3">
                    <div class="font-medium text-slate-700">${m.branch}</div>
                    <div class="text-[10px] text-indigo-600">${m.jobPosition || '-'}</div>
                </td>
                <td class="p-3">
                    <div class="font-semibold text-slate-900">${m.rank}</div>
                    <div class="text-[10px] text-emerald-600">ETB ${totalSalary.toLocaleString()} (Gonfoo: ${m.rankSalary})</div>
                    <div class="text-[10px] text-slate-400">Idoo: ${m.locationAllowance} | Nyaata: ${m.foodAllowance}</div>
                </td>
                <td class="p-3 text-slate-600">
                    <div>${m.eduLevel || '-'}</div>
                    <div class="text-[10px] text-slate-400">${m.fieldOfStudy || ''}</div>
                </td>
                <td class="p-3 text-slate-600 text-[11px]">
                    <div>Qac.: ${m.hireDay || '-'}/${m.hireMonth || '-'}/${m.hireYearVal || '-'}</div>
                    <div>Gon.: ${m.rankDay || '-'}/${m.rankMonth || '-'}/${m.rankYear || '-'}</div>
                </td>
                <td class="p-3">
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold ${m.status === 'Active' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}">${m.status}</span>
                </td>
                <td class="p-3 flex gap-1">
                    <button onclick="editMember(${index})" class="bg-amber-500 hover:bg-amber-600 text-white px-2.5 py-1 rounded text-[10px]">Gulaali</button>
                    <button onclick="deleteMember(${index})" class="bg-rose-500 hover:bg-rose-600 text-white px-2.5 py-1 rounded text-[10px]">Haqi</button>
                </td>
            </tr>
        `;
    });
}

function renderBranchesGrid() {
    const grid = document.getElementById("branchesGrid");
    const previewList = document.getElementById("branchPreviewList");
    if(!grid) return;

    grid.innerHTML = "";
    if(previewList) previewList.innerHTML = "";

    officialBranches.forEach(b => {
        const count = membersData.filter(m => m.branch === b && m.status === "Active").length;
        
        // Grid card for Branches tab
        grid.innerHTML += `
            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 flex flex-col justify-between space-y-2">
                <div>
                    <h4 class="font-bold text-indigo-900 text-xs">${b}</h4>
                    <p class="text-[10px] text-slate-500 mt-1">Komishinii Manneen Sirreessaa Oromiyaa</p>
                </div>
                <div class="flex justify-between items-center pt-2 border-t border-slate-200">
                    <span class="text-[10px] text-slate-600 font-medium">Miseensa Active:</span>
                    <span class="bg-indigo-100 text-indigo-700 font-bold px-2 py-0.5 rounded-full text-xs">${count}</span>
                </div>
            </div>
        `;

        // Side preview in dashboard
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
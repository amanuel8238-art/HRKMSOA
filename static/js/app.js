// Dameewwan Komishinii Manneen Sirreessaa Oromiyaa (Head Office + Dameewwan 38)
const branchesList = [
    "Head Office (Finfinnee)",
    "Aanaa Dadar",
    "Damee Mana Sirreessaa Adaamaa",
    "Damee Mana Sirreessaa Amboo",
    "Damee Mana Sirreessaa Asaboo",
    "Damee Mana Sirreessaa Arsee Nagelle",
    "Damee Mana Sirreessaa Baatuu",
    "Damee Mana Sirreessaa Bulee Horaa",
    "Damee Mana Sirreessaa Ciroo",
    "Damee Mana Sirreessaa Daseneech",
    "Damee Mana Sirreessaa Diillaa",
    "Damee Mana Sirreessaa Finfinnee",
    "Damee Mana Sirreessaa Gimbii",
    "Damee Mana Sirreessaa Ginir",
    "Damee Mana Sirreessaa Hararii",
    "Damee Mana Sirreessaa Jimmaa",
    "Damee Mana Sirreessaa Magaalaa Finfinnee",
    "Damee Mana Sirreessaa Mattuu",
    "Damee Mana Sirreessaa Naqamte",
    "Damee Mana Sirreessaa Negele Arsee",
    "Damee Mana Sirreessaa Robee",
    "Damee Mana Sirreessaa Shashamanee",
    "Damee Mana Sirreessaa Wallagga Bahaa",
    "Damee Mana Sirreessaa Waliso",
    "Damee Mana Sirreessaa Yaabelloo",
    "Damee Mana Sirreessaa Godee",
    "Damee Mana Sirreessaa Jijjigaa",
    "Damee Mana Sirreessaa Negelle Booranaa",
    "Damee Mana Sirreessaa Fichee",
    "Damee Mana Sirreessaa Tullu Bulloo",
    "Damee Mana Sirreessaa Holeta",
    "Damee Mana Sirreessaa Sululta",
    "Damee Mana Sirreessaa Bishuuftuu",
    "Damee Mana Sirreessaa Mojo",
    "Damee Mana Sirreessaa Meettaa",
    "Damee Mana Sirreessaa Goba",
    "Damee Mana Sirreessaa Dambi Doolloo",
    "Damee Mana Sirreessaa Ayiraa",
    "Damee Mana Sirreessaa Gimbi"
];

// Caasaa Raankii Hojjetootaa
const ranksList = [
    "Komishinara General",
    "Komishinara Dooktar",
    "Komishinara Itti Aanaa",
    "Komishinara",
    "Kommanderii Guddaa",
    "Kommanderii",
    "Inspeekterii Olaanoo",
    "Inspeekterii Ibsaa",
    "Inspeekterii",
    "Sajjootti Olaanoo",
    "Sajjootti",
    "Hojjetaa Idilee"
];

// HTML Select options keessatti akkamitti fe'uu qabdu (Function)
function populateDropdowns() {
    const branchSelect = document.getElementById('emp-branch');
    const rankSelect = document.getElementById('emp-rank');

    if (branchSelect) {
        branchSelect.innerHTML = '<option value="">-- Damee Filadhu --</option>';
        branchesList.forEach(branch => {
            const option = document.createElement('option');
            option.value = branch;
            option.textContent = branch;
            branchSelect.appendChild(option);
        });
    }

    if (rankSelect) {
        rankSelect.innerHTML = '<option value="">-- Raankii Filadhu --</option>';
        ranksList.forEach(rank => {
            const option = document.createElement('option');
            option.value = rank;
            option.textContent = rank;
            rankSelect.appendChild(option);
        });
    }
}

// Page yeroo fe'amu (Load) ta'u
document.addEventListener('DOMContentLoaded', () => {
    populateDropdowns();
});
}
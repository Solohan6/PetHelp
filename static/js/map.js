// This function needs to be globally accessible for the popup's onclick to work
function enterPlacingMode(petId, color) {
    // Set a global state to indicate we are now placing a pin
    window.placingSighting = { active: true, color: color, petId: petId };
    
    // Change the cursor to a crosshair for better UX
    document.getElementById('map').style.cursor = 'crosshair';
    
    // Close the popup
    window.map.closePopup();
}

document.addEventListener('DOMContentLoaded', function () {
    // 1. INITIALIZE MAP & ICONS
    window.map = L.map('map').setView([31.5204, 74.3587], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(window.map);
    const createIcon = (color) => L.icon({
        iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
    });
    window.blueIcon = createIcon('blue');
    window.redIcon = createIcon('red');
    window.greenIcon = createIcon('green');
    window.yellowIcon = createIcon('yellow');

    // 2. GLOBAL STATE
    let lostPetsData = {};
    window.mapLayers = {};
    window.placingSighting = { active: false, color: null, petId: null }; // For the new pin placing mode

    // 3. RENDER FUNCTIONS (No changes here)
    const petListContainer = document.getElementById('pet-details-list');
    function renderPetList() {
        if (Object.keys(lostPetsData).length === 0) {
            petListContainer.innerHTML = '<p>Everyone\'s fluffy friends are currently safe and sound at home.</p>';
            return;
        }
        const sortedPets = Object.values(lostPetsData).sort((a, b) => a.status === 'found' ? 1 : -1);
        petListContainer.innerHTML = sortedPets.map(pet => {
            const daysAgo = Math.floor((Date.now() - pet.submissionTime) / (1000 * 60 * 60 * 24));
            const timeText = daysAgo === 0 ? "today" : `${daysAgo} day(s) ago`;
            const isFound = pet.status === 'found';
            const statusBtnText = isFound ? 'Mark as Not Found' : 'Mark as Found';
            const deleteBtn = isFound ? `<button class="delete-btn" data-pet-id="${pet.id}">Delete Report</button>` : '';
            return `
                <div class="pet-card ${isFound ? 'found' : ''}" id="${pet.id}">
                    <img src="${pet.imageUrl}" alt="Photo of ${pet.name}">
                    <div class="pet-info">
                        <h3>${pet.name}</h3>
                        <p><strong>Contact:</strong> ${pet.contact}</p>
                        <p><strong>Description:</strong> ${pet.description}</p>
                        <div class="pet-meta">
                            <span>Posted ${timeText}</span>
                            <div>
                                <button class="status-btn ${isFound ? 'status-found' : 'status-not-found'}" data-pet-id="${pet.id}">${statusBtnText}</button>
                                ${deleteBtn}
                            </div>
                        </div>
                    </div>
                </div>`;
        }).join('');
    }

    // 4. MAP OBJECT FUNCTIONS
    function addLostPetToMap(petData) {
        if (window.mapLayers[petData.id]) return;
        
        const redMarker = L.marker(petData.latlng, { icon: window.redIcon }).addTo(window.map);
        
        // ** THE NEW, SIMPLIFIED PIN CLICK LOGIC **
        const popupContent = `
            <div>
                <strong>${petData.name}</strong><br>
                <button class="popup-btn green" onclick="enterPlacingMode('${petData.id}', 'green')">Report Sighting (Green)</button>
                <button class="popup-btn yellow" onclick="enterPlacingMode('${petData.id}', 'yellow')">Mark Searched Area (Yellow)</button>
            </div>
        `;
        redMarker.bindPopup(popupContent);

        const radius = 1.5 * 0.009;
        const bounds = [[petData.latlng[0] - radius, petData.latlng[1] - radius], [petData.latlng[0] + radius, petData.latlng[1] + radius]];
        const grid = L.rectangle(bounds, { color: "#e74c3c", weight: 1, fillOpacity: 0.1 }).addTo(window.map);

        window.mapLayers[petData.id] = { marker: redMarker, grid: grid, sightings: [] };
    }
    
    function removePetFromMap(petId) {
        if (window.mapLayers[petId]) {
            window.map.removeLayer(window.mapLayers[petId].marker);
            window.map.removeLayer(window.mapLayers[petId].grid);
            window.mapLayers[petId].sightings.forEach(s => window.map.removeLayer(s));
            delete window.mapLayers[petId];
        }
    }

    // 5. API INTERACTIONS (Unchanged)
    async function loadInitialData() {
        const response = await fetch('/api/pets');
        lostPetsData = await response.json();
        renderPetList();
        Object.values(lostPetsData).forEach(pet => addLostPetToMap(pet));
    }

    // 6. EVENT LISTENERS
    // ** THE NEW, SINGLE MAP CLICK HANDLER **
    window.map.on('click', function(e) {
        // If we are in the special "placing a pin" mode
        if (window.placingSighting.active) {
            const { color, petId } = window.placingSighting;
            const icon = color === 'green' ? window.greenIcon : window.yellowIcon;
            const newSightingMarker = L.marker(e.latlng, { icon: icon }).addTo(window.map);
            window.mapLayers[petId].sightings.push(newSightingMarker);

            // Exit placing mode
            window.placingSighting = { active: false, color: null, petId: null };
            document.getElementById('map').style.cursor = ''; // Reset cursor
        } else {
            // Otherwise, this is a click to report a new pet
            document.getElementById('pet-lat').value = e.latlng.lat;
            document.getElementById('pet-lng').value = e.latlng.lng;
            document.getElementById('lost-pet-form-container').style.display = 'block';
        }
    });

    // Form and button listeners (Unchanged)
    const petForm = document.getElementById('lost-pet-form');
    // ... (rest of the form and button listeners are the same as before)
    petForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const formData = new FormData(petForm);
        formData.append('submissionTime', Date.now());
        const response = await fetch('/api/pets', { method: 'POST', body: formData });
        if (response.ok) {
            const newPet = await response.json();
            lostPetsData[newPet.id] = newPet;
            addLostPetToMap(newPet);
            renderPetList();
            petForm.reset();
            document.getElementById('lost-pet-form-container').style.display = 'none';
        } else { alert('Error submitting report.'); }
    });

    petListContainer.addEventListener('click', async function(e) {
        const target = e.target;
        if (!target.dataset.petId) return;
        const petId = target.dataset.petId;
        if (target.classList.contains('status-btn')) {
            const response = await fetch(`/api/pets/${petId}/status`, { method: 'POST' });
            if (response.ok) {
                lostPetsData[petId] = await response.json();
                renderPetList();
            }
        }
        if (target.classList.contains('delete-btn')) {
            if (confirm('Are you sure you want to permanently delete this report?')) {
                const response = await fetch(`/api/pets/${petId}`, { method: 'DELETE' });
                if (response.ok) {
                    removePetFromMap(petId);
                    delete lostPetsData[petId];
                    renderPetList();
                }
            }
        }
    });
    
    document.getElementById('cancel-btn').addEventListener('click', () => {
        petForm.reset();
        document.getElementById('lost-pet-form-container').style.display = 'none';
    });

    // 7. INITIALIZE PAGE
    centralLocations.forEach(loc => {
        L.marker(loc.coords, { icon: window.blueIcon }).addTo(window.map).bindTooltip(loc.name, { permanent: true, direction: 'top', offset: [0, -20] }).openTooltip();
    });
    
    loadInitialData();
});
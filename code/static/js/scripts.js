let eventsModal;
let allEvents = {};
let currentEvents = [];

// Initial Setup ------------------------------------------------------------------------------------

function setupCategoryCards() {
    document.querySelectorAll('.category-card').forEach(card => {
        const category = card.id;
        const events = allEvents[category] || [];
        const topEvents = events.sort((a, b) => b.popularity - a.popularity).slice(0, 2);
        const popularEventsList = card.querySelector('.popular-events ul');

        popularEventsList.innerHTML = '';
        topEvents.forEach(event => {
            const li = document.createElement('li');
            li.textContent = `${event.summary} (${event.popularity}★)`;
            popularEventsList.appendChild(li);
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    eventsModal = document.getElementById('eventsModal');
    
    fetch('/api/events')
        .then(response => response.json())
        .then(data => {
            allEvents = data;
            setupCategoryCards();
        });

    eventsModal.addEventListener('click', (e) => {
        if (e.target === eventsModal) {
            eventsModal.classList.remove('active');
        }
    });

    // Setup search functionality
    document.getElementById('searchButton').addEventListener('click', performSearch);
    document.getElementById('searchInput').addEventListener('keypress', handleSearchKeyPress);
});

// Search ------------------------------------------------------------------------------------
function handleSearchKeyPress(event) {
    if (event.key === 'Enter') {
        performSearch();
    }
}

function performSearch() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
    if (!searchTerm) {
        return;
    }
    
    const filteredEvents = [];
    Object.values(allEvents).forEach(categoryEvents => {
        categoryEvents.forEach(event => {
            if (event.summary.toLowerCase().includes(searchTerm)) {
                filteredEvents.push(event);
            }
        });
    });

    currentEvents = filteredEvents;
    openModal('search', 'Search Results', filteredEvents);
}

// Filters for Modal------------------------------------------------------------------------------------
function updatePopularityValue(e) {
    document.getElementById('popularityValue').textContent = e.target.value + '★';
}

function applyFilters() {
    const startDate = document.getElementById('startDate')?.value;
    const endDate = document.getElementById('endDate')?.value;
    const minPopularity = parseInt(document.getElementById('popularityFilter')?.value || '1');
    
    let filteredEvents = [...currentEvents];
    
    if (startDate) {
        filteredEvents = filteredEvents.filter(event => 
            new Date(event.start_datetime) >= new Date(startDate)
        );
    }
    
    if (endDate) {
        filteredEvents = filteredEvents.filter(event => 
            new Date(event.start_datetime) <= new Date(endDate)
        );
    }
    
    filteredEvents = filteredEvents.filter(event => 
        event.popularity >= minPopularity
    );
    
    renderEventsList(filteredEvents);
}

function handleSort() {
    const sortValue = document.getElementById('sortOptions').value;
    let sortedEvents = [...currentEvents];
    
    switch(sortValue) {
        case 'alphabetical':
            sortedEvents.sort((a, b) => a.name.localeCompare(b.name));
            break;
        case 'chronological':
            sortedEvents.sort((a, b) => new Date(a.date) - new Date(b.date));
            break;
        case 'popularity':
            sortedEvents.sort((a, b) => b.popularity - a.popularity);
            break;
    }
    
    renderEventsList(sortedEvents);
}

// Modal and Events rendering-----------------------------------------------------------------------------------------
function renderEventsList(events, tab="") {
    const listId = tab !== '' ? tab + "Events" : 'eventsList';
    const list = document.getElementById(listId);
    const noResultsElement = document.getElementById('noResults');
    console.log("here")
    if (noResultsElement) {
        if (!events || events.length === 0) {
            console.log("here2",events)
            noResultsElement.classList.remove('hidden');
        } else {
            noResultsElement.classList.add('hidden');
        }
    }
    
    list.innerHTML = '';
    
    events.forEach(event => {
        const li = document.createElement('li');
        li.className = 'event-item';
        const dateStr = event.start_datetime ? new Date(event.start_datetime).toLocaleDateString() : 'Date not set';
        
        li.innerHTML = `
        <div>
            <strong>${event.summary}</strong>
            <div class="badge-container">
                <span class="date-badge">${dateStr}</span>
                ${event.popularity ? `<span class="popularity-badge">${event.popularity}★</span>` : ''}
            </div>
        </div>
        ${listId !== 'eventsList' ? 
            `
            <div class="button-group">
                <button onclick="changeEvent('remove', '${event.event_id}', '${tab}')" class="favorite-btn">Remove</button>
                ${tab === 'private' || tab === 'hosted' ? 
                    `<button onclick="changeEvent('update', '${event.event_id}', '${tab}')" class="favorite-btn">Update</button>` : ''}
            </div>
            ` : 
            `
            <div class="button-group">
            <button onclick="addToMyEvents('${event.event_id}','Public')" class="favorite-btn">Add</button>
            </div>
            `
        }
        `;
        list.appendChild(li);
    });
}

function showEventsModal(category, events) {
    const modalTitle = eventsModal.querySelector('.modal-title');
    if (!category) {
        modalTitle.textContent = 'Events';
    } else {
        modalTitle.textContent = `${category} Events`;
    }

    renderEventsList(events);
}

function openModal(type, category = '', events = null) {
    const modal = document.getElementById('eventsModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    modalTitle.innerHTML = '';
    modalBody.innerHTML = '';

    if (type === 'myEvents') {
        modalTitle.innerHTML = 'My Events';
        modalBody.innerHTML = `
            <div class="tabs">
                <button class="tab-btn active" onclick="switchTab('registered')">Registered Events</button>
                <button class="tab-btn" onclick="switchTab('private')">Private Events</button>
                <button class="tab-btn" onclick="switchTab('hosted')">Hosted Events</button>
            </div>

            <div id="registeredEvents" class="tab-content active">
                <ul class="list-group" id="registeredEventsList"></ul>
            </div>
            <div id="privateEvents" class="tab-content">
                <ul class="list-group" id="privateEventsList"></ul>
            </div>
            <div id="hostedEvents" class="tab-content">
                <ul class="list-group" id="hostedEventsList"></ul>
            </div>
        `;
        loadTabContent('registered')
    } else if (type === 'category' || type === 'search') {
        modalTitle.innerHTML = category;
        modalBody.innerHTML = `
            <div class="filters-container">
                <div class="date-range-container">
                    <div class="date-range-input">
                        <label class="input-label">Date Range</label>
                        <input type="date" class="date-input" id="startDate" onchange="applyFilters()">
                    </div>
                    <div class="date-range-input">
                        <label class="input-label">To</label>
                        <input type="date" class="date-input" id="endDate" onchange="applyFilters()">
                    </div>
                </div>
                
                <div class="popularity-filter-container">
                    <label class="input-label">Min. Popularity</label>
                    <input type="range" class="popularity-slider" id="popularityFilter" min="0" max="10" value="1" 
                        oninput="updatePopularityValue(event); applyFilters()">
                    <div class="popularity-value" id="popularityValue">1★</div>
                </div>
            </div>

            <div class="sort-options">
                <select class="form-select" id="sortOptions" onchange="handleSort()">
                    <option value="alphabetical">Sort by Name</option>
                    <option value="chronological">Sort by Date</option>
                    <option value="popularity">Sort by Popularity</option>
                </select>
            </div>

            <div id="noResults" class="no-results hidden">
                No events found matching your criteria
            </div>

            <ul id="eventsList" class="list-group"></ul>
        `;
        
        if (events) {
            currentEvents = events;
            showEventsModal(category, events);
        } else {
            currentEvents = allEvents[category] || [];
            showEventsModal(category, currentEvents);
        }
    }

    modal.classList.add('active');
}

// Add events button -----------------------------------------------------------------------------------------
function addToMyEvents(event_id, event_type) {
    fetch(`/api/my-events/add_event/${event_id}/${event_type}`, {  
        method: "POST",
        headers: { "Content-Type": "application/json" },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Event successfully added to your list!');
        } else {
            alert(data.message || 'Failed to add event. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    });
}


// My Events and Tabs-----------------------------------------------------------------------------------------
function changeEvent(action, event_id, tab) {
    let event_type;
    if (tab ==='private')
        event_type = 'Private'
    else
        event_type = 'Public'
    let url = `/api/my-events/${action}_event/${event_id}/${event_type}`;
    if (action==='remove'){
        console.log(url)
        fetch(url, {
            method: "GET",
            headers: { "Content-Type": "application/json" },
        })
        .then(response => response.json()) 
        .then(data => {
            alert(data.message);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to perform action. Please try again.');
        });
        loadTabContent(tab);    
    }
    else{
        let url2 = `/api/my-events/${action}_event/${event_id}/${event_type}`;
        window.location.href = url2;
    }
}

function switchTab(tab) {
    openModal('myEvents')
    const allTabs = ['registeredEvents', 'privateEvents', 'hostedEvents'];
    const allButtons = document.querySelectorAll('.tab-btn');
    
    allTabs.forEach(tabId => {
        document.getElementById(tabId).classList.remove('active');
    });
    allButtons.forEach(btn => btn.classList.remove('active'));
    
    document.getElementById(tab + 'Events').classList.add('active');
    document.querySelector(`.tab-btn[onclick="switchTab('${tab}')"]`).classList.add('active');
    loadTabContent(tab);
}

function loadTabContent(tab) {
    const listId = tab + "Events"
    const list = document.getElementById(listId);
    fetch(`/api/my-events/${tab}`)
        .then(response => response.json())
        .then(events => {
            console.log(events);
            renderEventsList(events, tab);
        })
        .catch(error => {
            if (list) {
                list.innerHTML = '<li class="event-item">Failed to load events</li>';
            }
            console.error('Error loading events:', error);
        });
}

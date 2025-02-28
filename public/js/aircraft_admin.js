// public/js/aircraft_admin.js

// Run after DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  loadRegistrations();
  loadAircraftTypes();
  loadAirlines();

  const form = document.getElementById('new-registration-form');
  form.addEventListener('submit', handleFormSubmit);
});

/**
 * Fetch existing aircraft registrations and populate #registration-table.
 */
async function loadRegistrations() {
  try {
    const response = await fetch('/api/aircraft');
    if (!response.ok) {
      throw new Error(`Error fetching aircraft. Status: ${response.status}`);
    }

    // The server returns an object like:
    // { "aircraft": [...], "count": 20 }
    // So extract the array
    const data = await response.json();
    const aircraftList = data.aircraft;

    populateRegistrationTable(aircraftList);
  } catch (err) {
    console.error('Failed to load registrations:', err);
  }
}

function populateRegistrationTable(list) {
  const tbody = document.querySelector('#registration-table tbody');
  tbody.innerHTML = '';
  list.forEach((item) => {
    const tr = document.createElement('tr');
    const reg = item.registration || '--';
    const type = item.aircraft_type?.type_code || '(Unknown type)';
    const airline = item.airline?.name || '(Unknown airline)';

    tr.innerHTML = `
      <td>${reg}</td>
      <td>${type}</td>
      <td>${airline}</td>
      <td>
        <!-- Example "delete" or "edit" button, if you want -->
        <button data-reg="${reg}" class="delete-btn" style="padding: 4px 8px;">
          <i class="bi bi-trash"></i>
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

/**
 * Fetch existing aircraft types (from your AircraftType model)
 * and populate the #typeSelect dropdown.
 */
async function loadAircraftTypes() {
  try {
    const response = await fetch('/api/aircraft_types');
    if (!response.ok) {
      throw new Error(`Error fetching aircraft types. Status: ${response.status}`);
    }
    const types = await response.json();
    const select = document.getElementById('typeSelect');
    types.forEach((t) => {
      const option = document.createElement('option');
      option.value = t.id;  // you might store the ID
      option.textContent = `${t.manufacturer} ${t.model_name} (${t.type_code})`;
      select.appendChild(option);
    });
  } catch (err) {
    console.error('Failed to load aircraft types:', err);
  }
}

/**
 * Fetch existing airlines and populate #airlineSelect dropdown.
 */
async function loadAirlines() {
  try {
    const response = await fetch('/api/airlines');
    if (!response.ok) {
      throw new Error(`Error fetching airlines. Status: ${response.status}`);
    }
    const airlines = await response.json();
    const select = document.getElementById('airlineSelect');
    airlines.forEach((a) => {
      const option = document.createElement('option');
      option.value = a.id;
      option.textContent = `${a.name} (${a.iata_code || ''})`;
      select.appendChild(option);
    });
  } catch (err) {
    console.error('Failed to load airlines:', err);
  }
}

/**
 * Handle form submission for creating a new registration.
 */
async function handleFormSubmit(event) {
  event.preventDefault();
  const form = event.target;

  // Gather form data
  const formData = {
    registration: form.regInput.value.trim(),
    icao24: form.icao24Input.value.trim(),
    aircraft_type_id: form.typeSelect.value,
    airline_id: form.airlineSelect.value
    // Add more fields as needed, e.g. SELCAL, remarks, etc.
  };

  // POST to your existing endpoint.
  // Adjust the route to match your actual back-end route for creating an aircraft.
  try {
    const response = await fetch('/api/aircraft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Create failed: ${errorText}`);
    }
    // Registration created. Reload table or just add to table dynamically.
    form.reset();
    loadRegistrations(); // re-fetch to see the new entry
    alert('Registration created successfully!');
  } catch (err) {
    console.error('Error creating registration:', err);
    alert('Failed to create registration. Check console for details.');
  }
}

async function createRegistration(formData) {
  const response = await fetch('/api/aircraft', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData)
  });
  if (!response.ok) {
    // handle error
  }
  // success => reload or update your table
}
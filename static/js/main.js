// Store the ID of the professor to delete
let professorToDelete = null;

// Function to edit a professor
function editProfessor(professorId) {
    // Fetch the professor's data from the server
    fetch(`/get_professor/${professorId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Redirect to the add_professor page with the professor data as query parameters
            // We'll use URLSearchParams to construct the query string
            const params = new URLSearchParams();
            params.append('id', data.id);
            params.append('name', data.name);
            params.append('title', data.title);
            params.append('university_name', data.university_name);
            params.append('university_country', data.university_country);
            params.append('university_state', data.university_state);
            params.append('university_city', data.university_city);
            params.append('university_ranking', data.university_ranking);
            params.append('department_name', data.department_name);
            params.append('email', data.email);
            params.append('personal_website', data.personal_website);
            params.append('lab_group_name', data.lab_group_name);
            params.append('lab_website', data.lab_website);
            params.append('hiring_status', data.hiring_status);
            params.append('contact_through', data.contact_through);
            params.append('form_link', data.form_link);
            params.append('notes', data.notes);

            // Join program and research area names with commas for input
            params.append('program_names', data.programs.join(','));
            params.append('research_area_names', data.research_areas.join(','));

            window.location.href = `/add_professor?${params.toString()}`;
        })
        .catch(error => {
            console.error('Error fetching professor data:', error);
            alert('Error loading professor data for editing.');
        });
}

// Function to delete a professor
function deleteProfessor(professorId) {
    professorToDelete = professorId;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

// Confirm deletion when the confirm button is clicked
document.getElementById('confirmDeleteBtn')?.addEventListener('click', function() { // Optional chaining
    if (professorToDelete !== null) {
        // Send a DELETE request to the server
        fetch(`/delete_professor/${professorToDelete}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (response.ok) {
                // Remove the row from the table using the professor ID
                const row = document.querySelector(`tr[data-professor-id="${professorToDelete}"]`);
                if (row) {
                    row.remove();
                }

                // Hide the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
                modal.hide();
                // Reset the variable
                professorToDelete = null;
                location.reload();
            } else {
                alert('Error deleting professor');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting professor');
        });
    }
});

// --- utils ---
const normalize = (s) => (s || "").toString().toLowerCase().trim().replace(/\s+/g, " ");
const tokenize = (s) => normalize(s).split(" ").filter(Boolean);

// Simple debounce for input typing
function debounce(fn, delay = 250) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), delay);
  };
}
const toNum = (v, fallback = NaN) => {
  const n = Number(v); return Number.isFinite(n) ? n : fallback;
};

// --- core filtering ---
function filterTable() {
  // Check if professor table exists before running this function
  const profTable = document.getElementById('professorTable');
  if (!profTable) return; // Exit if not on the professor page

  // Search only these fields:
  // name + location (country, city, state)
  const tokens = tokenize(document.getElementById('globalSearch').value);

  // Filters (do not participate in global search)
  const hiringStatusFilter = normalize(document.getElementById('filterHiringStatus').value);
  const contactMethodFilter = normalize(document.getElementById('filterContactMethod').value);
  const programFilter = normalize(document.getElementById('filterProgram').value);
  const researchAreaFilter = normalize(document.getElementById('filterResearchArea').value);
  const titleFilter = normalize(document.getElementById('filterTitle').value);
  const universityFilter = normalize(document.getElementById('filterUniversity').value);
  const departmentFilter = normalize(document.getElementById('filterDepartment').value);

  const rows = document.querySelectorAll('#professorTable tbody tr');

  rows.forEach(row => {
    // row dataset
    const name = normalize(row.getAttribute('data-name'));
    const country = normalize(row.getAttribute('data-country'));
    const city = normalize(row.getAttribute('data-city'));
    const state = normalize(row.getAttribute('data-state'));
    const hiringStatus = normalize(row.getAttribute('data-hiring-status'));
    const contactMethod = normalize(row.getAttribute('data-contact-method'));
    const title = normalize(row.getAttribute('data-title'));
    const university = normalize(row.getAttribute('data-university'));
    const department = normalize(row.getAttribute('data-department'));
    const programs = normalize(row.querySelector('.programs-cell')?.getAttribute('data-programs') || "");
    const researchAreas = normalize(row.querySelector('.research-areas-cell')?.getAttribute('data-research-areas') || "");

    // Global search haystack (name + location only)
    const haystack = `${name} ${country} ${city} ${state}`;
    const matchesGlobal = tokens.every(t => haystack.includes(t));

    // Independent filters (substring matches)
    const matchesHiring = !hiringStatusFilter || hiringStatus.includes(hiringStatusFilter);
    const matchesContact = !contactMethodFilter || contactMethod.includes(contactMethodFilter);
    const matchesProgram = !programFilter || programs.includes(programFilter);
    const matchesRA = !researchAreaFilter || researchAreas.includes(researchAreaFilter);
    const matchesTitle = !titleFilter || title.includes(titleFilter);
    const matchesUni = !universityFilter || university.includes(universityFilter);
    const matchesDept = !departmentFilter || department.includes(departmentFilter);

    const show = matchesGlobal && matchesHiring && matchesContact && matchesProgram &&
                 matchesRA && matchesTitle && matchesUni && matchesDept;

    row.style.display = show ? '' : 'none';
  });

  sortRows(); // apply current sort on the visible set
}

// --- sorting ---
function sortRows() {
  // Check if professor table exists before running this function
  const profTable = document.getElementById('professorTable');
  if (!profTable) return; // Exit if not on the professor page

  const sortBy = document.getElementById('sortBy').value;
  if (!sortBy) return;

  const tbody = document.querySelector('#professorTable tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  const visibleRows = rows.filter(r => r.style.display !== 'none');

  const getName = (r) => normalize(r.getAttribute('data-name'));
  const getRanking = (r) => {
    const raw = (r.getAttribute('data-ranking') || '').trim();
    const n = parseFloat(raw);
    return Number.isFinite(n) ? n : Number.POSITIVE_INFINITY; // push non-numeric to bottom
  };

  visibleRows.sort((a, b) => {
    switch (sortBy) {
      case 'name-asc':   return getName(a).localeCompare(getName(b));
      case 'name-desc':  return getName(b).localeCompare(getName(a));
      case 'ranking-asc':  return getRanking(a) - getRanking(b);
      case 'ranking-desc': return getRanking(b) - getRanking(a);
      default: return 0;
    }
  });

  // Re-append visible rows in new order, keep hidden in place
  visibleRows.forEach(r => tbody.appendChild(r));
}

// --- clear ---
function clearFilters() {
  // Check if professor table exists before running this function
  const profTable = document.getElementById('professorTable');
  if (!profTable) return; // Exit if not on the professor page

  document.getElementById('globalSearch').value = '';
  document.getElementById('filterHiringStatus').value = '';
  document.getElementById('filterContactMethod').value = '';
  document.getElementById('filterProgram').value = '';
  document.getElementById('filterResearchArea').value = '';
  document.getElementById('filterTitle').value = '';
  document.getElementById('filterUniversity').value = '';
  document.getElementById('filterDepartment').value = '';
  document.getElementById('sortBy').value = '';
  filterTable();
}

// --- wire up live filtering ---
// Add checks before attaching listeners
document.getElementById('globalSearch')?.addEventListener('input', debounce(filterTable, 200));
document.getElementById('filterHiringStatus')?.addEventListener('change', filterTable);
document.getElementById('filterContactMethod')?.addEventListener('change', filterTable);
document.getElementById('filterProgram')?.addEventListener('input', debounce(filterTable, 200));
document.getElementById('filterResearchArea')?.addEventListener('input', debounce(filterTable, 200));
document.getElementById('filterTitle')?.addEventListener('input', debounce(filterTable, 200));
document.getElementById('filterUniversity')?.addEventListener('input', debounce(filterTable, 200));
document.getElementById('filterDepartment')?.addEventListener('input', debounce(filterTable, 200));
document.getElementById('sortBy')?.addEventListener('change', filterTable);

// Initial run (optional) - also add check
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('professorTable')) {
        filterTable();
    }
});

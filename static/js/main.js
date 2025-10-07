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
document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
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

// Function to filter the professor table based on search criteria
function filterTable() {
    const nameFilter = document.getElementById('searchName').value.toLowerCase();
    const universityFilter = document.getElementById('searchUniversity').value.toLowerCase();
    const departmentFilter = document.getElementById('searchDepartment').value.toLowerCase();
    const programFilter = document.getElementById('searchProgram').value.toLowerCase();
    const researchAreaFilter = document.getElementById('searchResearchArea').value.toLowerCase();
    const emailFilter = document.getElementById('searchEmail').value.toLowerCase();
    const hiringStatusFilter = document.getElementById('filterHiringStatus').value.toLowerCase();
    const contactMethodFilter = document.getElementById('filterContactMethod').value.toLowerCase();
    const countryFilter = document.getElementById('searchCountry').value.toLowerCase();
    const cityFilter = document.getElementById('searchCity').value.toLowerCase();
    const stateFilter = document.getElementById('searchState').value.toLowerCase();
    const rankingFilter = document.getElementById('searchRanking').value.toLowerCase();

    const rows = document.querySelectorAll('#professorTable tbody tr');
    
    rows.forEach(row => {
        const name = row.getAttribute('data-name');
        const university = row.getAttribute('data-university');
        const department = row.getAttribute('data-department');
        const hiringStatus = row.getAttribute('data-hiring-status');
        const contactMethod = row.getAttribute('data-contact-method');
        const email = row.getAttribute('data-email');
        const country = row.getAttribute('data-country');
        const city = row.getAttribute('data-city');
        const state = row.getAttribute('data-state');
        const ranking = row.getAttribute('data-ranking');
        const programs = row.querySelector('.programs-cell').getAttribute('data-programs');
        const researchAreas = row.querySelector('.research-areas-cell').getAttribute('data-research-areas');

        const matchesName = nameFilter === '' || name.includes(nameFilter);
        const matchesUniversity = universityFilter === '' || university.includes(universityFilter);
        const matchesDepartment = departmentFilter === '' || department.includes(departmentFilter);
        const matchesProgram = programFilter === '' || programs.includes(programFilter);
        const matchesResearchArea = researchAreaFilter === '' || researchAreas.includes(researchAreaFilter);
        const matchesEmail = emailFilter === '' || email.includes(emailFilter);
        const matchesHiringStatus = hiringStatusFilter === '' || hiringStatus.includes(hiringStatusFilter);
        const matchesContactMethod = contactMethodFilter === '' || contactMethod.includes(contactMethodFilter);
        const matchesCountry = countryFilter === '' || country.includes(countryFilter);
        const matchesCity = cityFilter === '' || city.includes(cityFilter);
        const matchesState = stateFilter === '' || state.includes(stateFilter);
        const matchesRanking = rankingFilter === '' || ranking.includes(rankingFilter);

        if (matchesName && matchesUniversity && matchesDepartment && 
            matchesProgram && matchesResearchArea && matchesEmail && 
            matchesHiringStatus && matchesContactMethod && 
            matchesCountry && matchesCity && matchesState && matchesRanking) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Function to clear all filters
function clearFilters() {
    document.getElementById('searchName').value = '';
    document.getElementById('searchUniversity').value = '';
    document.getElementById('searchDepartment').value = '';
    document.getElementById('searchProgram').value = '';
    document.getElementById('searchResearchArea').value = '';
    document.getElementById('searchEmail').value = '';
    document.getElementById('filterHiringStatus').value = '';
    document.getElementById('filterContactMethod').value = '';
    document.getElementById('searchCountry').value = '';
    document.getElementById('searchCity').value = '';
    document.getElementById('searchState').value = '';
    document.getElementById('searchRanking').value = '';
    filterTable();
}
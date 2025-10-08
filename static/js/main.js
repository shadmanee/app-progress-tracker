(() => {
  // Store the ID of the professor to delete
  let professorToDelete = null;

  const getById = (id) => document.getElementById(id);

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

  // Function to edit a professor
  function editProfessor(professorId) {
    fetch(`/get_professor/${professorId}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then((data) => {
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
        params.append('program_names', (data.programs || []).join(','));
        params.append('research_area_names', (data.research_areas || []).join(','));

        window.location.href = `/add_professor?${params.toString()}`;
      })
      .catch((error) => {
        console.error('Error fetching professor data:', error);
        alert('Error loading professor data for editing.');
      });
  }

  // Function to delete a professor
  function deleteProfessor(professorId) {
    const modalElement = getById('deleteModal');
    if (!modalElement || typeof bootstrap === 'undefined') {
      console.warn('Delete modal or Bootstrap is unavailable.');
      return;
    }

    professorToDelete = professorId;
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
  }

  // --- core filtering ---
  function filterTable() {
    const table = getById('professorTable');
    if (!table) {
      return;
    }

    const tbody = table.querySelector('tbody');
    if (!tbody) {
      return;
    }

    const tokens = tokenize(getById('globalSearch')?.value || '');
    const hiringStatusFilter = normalize(getById('filterHiringStatus')?.value);
    const contactMethodFilter = normalize(getById('filterContactMethod')?.value);
    const programFilter = normalize(getById('filterProgram')?.value);
    const researchAreaFilter = normalize(getById('filterResearchArea')?.value);
    const titleFilter = normalize(getById('filterTitle')?.value);
    const universityFilter = normalize(getById('filterUniversity')?.value);
    const departmentFilter = normalize(getById('filterDepartment')?.value);

    const rows = tbody.querySelectorAll('tr');

    rows.forEach((row) => {
      const name = normalize(row.getAttribute('data-name'));
      const country = normalize(row.getAttribute('data-country'));
      const city = normalize(row.getAttribute('data-city'));
      const state = normalize(row.getAttribute('data-state'));
      const hiringStatus = normalize(row.getAttribute('data-hiring-status'));
      const contactMethod = normalize(row.getAttribute('data-contact-method'));
      const title = normalize(row.getAttribute('data-title'));
      const university = normalize(row.getAttribute('data-university'));
      const department = normalize(row.getAttribute('data-department'));
      const programs = normalize(row.querySelector('.programs-cell')?.getAttribute('data-programs') || '');
      const researchAreas = normalize(row.querySelector('.research-areas-cell')?.getAttribute('data-research-areas') || '');

      const haystack = `${name} ${country} ${city} ${state}`;
      const matchesGlobal = tokens.every((t) => haystack.includes(t));

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

    sortRows();
  }

  // --- sorting ---
  function sortRows() {
    const sortSelect = getById('sortBy');
    const table = getById('professorTable');
    if (!sortSelect || !table) {
      return;
    }

    const sortBy = sortSelect.value;
    if (!sortBy) {
      return;
    }

    const tbody = table.querySelector('tbody');
    if (!tbody) {
      return;
    }

    const rows = Array.from(tbody.querySelectorAll('tr'));
    const visibleRows = rows.filter((r) => r.style.display !== 'none');

    const getName = (r) => normalize(r.getAttribute('data-name'));
    const getRanking = (r) => {
      const raw = (r.getAttribute('data-ranking') || '').trim();
      const n = parseFloat(raw);
      return Number.isFinite(n) ? n : Number.POSITIVE_INFINITY;
    };

    visibleRows.sort((a, b) => {
      switch (sortBy) {
        case 'name-asc':
          return getName(a).localeCompare(getName(b));
        case 'name-desc':
          return getName(b).localeCompare(getName(a));
        case 'ranking-asc':
          return getRanking(a) - getRanking(b);
        case 'ranking-desc':
          return getRanking(b) - getRanking(a);
        default:
          return 0;
      }
    });

    visibleRows.forEach((row) => tbody.appendChild(row));
  }

  // --- clear ---
  function clearFilters() {
    const filterIds = [
      'globalSearch',
      'filterHiringStatus',
      'filterContactMethod',
      'filterProgram',
      'filterResearchArea',
      'filterTitle',
      'filterUniversity',
      'filterDepartment',
      'sortBy',
    ];

    filterIds.forEach((id) => {
      const el = getById(id);
      if (el) {
        el.value = '';
      }
    });

    filterTable();
  }

  function attachFilterListeners() {
    const map = [
      ['globalSearch', 'input', debounce(filterTable, 200)],
      ['filterHiringStatus', 'change', filterTable],
      ['filterContactMethod', 'change', filterTable],
      ['filterProgram', 'input', debounce(filterTable, 200)],
      ['filterResearchArea', 'input', debounce(filterTable, 200)],
      ['filterTitle', 'input', debounce(filterTable, 200)],
      ['filterUniversity', 'input', debounce(filterTable, 200)],
      ['filterDepartment', 'input', debounce(filterTable, 200)],
      ['sortBy', 'change', filterTable],
    ];

    map.forEach(([id, event, handler]) => {
      const el = getById(id);
      if (el) {
        el.addEventListener(event, handler);
      }
    });
  }

  function setupDeletionHandler() {
    const confirmDeleteBtn = getById('confirmDeleteBtn');
    const modalElement = getById('deleteModal');

    if (!confirmDeleteBtn || !modalElement) {
      return;
    }

    confirmDeleteBtn.addEventListener('click', () => {
      if (professorToDelete === null) {
        return;
      }

      fetch(`/delete_professor/${professorToDelete}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error('Failed to delete professor');
          }

          const row = document.querySelector(`tr[data-professor-id="${professorToDelete}"]`);
          if (row) {
            row.remove();
          }

          if (typeof bootstrap !== 'undefined') {
            const modal = bootstrap.Modal.getInstance(modalElement);
            modal?.hide();
          }

          professorToDelete = null;
          location.reload();
        })
        .catch((error) => {
          console.error('Error deleting professor:', error);
          alert('Error deleting professor');
        });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    attachFilterListeners();
    setupDeletionHandler();

    if (getById('professorTable')) {
      filterTable();
    }
  });

  // Expose functions for inline handlers
  window.editProfessor = editProfessor;
  window.deleteProfessor = deleteProfessor;
  window.clearFilters = clearFilters;
})();

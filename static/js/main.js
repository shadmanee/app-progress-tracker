// Chart initialization
document.addEventListener('DOMContentLoaded', function() {
    // Load chart data
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('progressChart').getContext('2d');
            
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.map(d => d.week),
                    datasets: [{
                        label: 'Emails Sent',
                        data: data.map(d => d.contacted),
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        tension: 0.1
                    }, {
                        label: 'Responses Received',
                        data: data.map(d => d.responded),
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        });
    
    // Filter functionality
    document.getElementById('universityFilter').addEventListener('change', filterTable);
    document.getElementById('researchAreaFilter').addEventListener('change', filterTable);
    document.getElementById('statusFilter').addEventListener('change', filterTable);
});

function filterTable() {
    const universityFilter = document.getElementById('universityFilter').value;
    const researchAreaFilter = document.getElementById('researchAreaFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;
    
    const rows = document.querySelectorAll('#professorTable tbody tr');
    
    rows.forEach(row => {
        const university = row.getAttribute('data-university');
        const researchArea = row.getAttribute('data-research-area');
        const status = row.getAttribute('data-status');
        
        const matchesUniversity = !universityFilter || university === universityFilter;
        const matchesResearchArea = !researchAreaFilter || researchArea === researchAreaFilter;
        const matchesStatus = !statusFilter || status === statusFilter;
        
        if (matchesUniversity && matchesResearchArea && matchesStatus) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}
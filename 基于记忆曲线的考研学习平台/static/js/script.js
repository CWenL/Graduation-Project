document.addEventListener('DOMContentLoaded', function() {
    const toggleButton = document.getElementById('toggleSidebar');
    const sidebar = document.getElementById('sidebar');

    toggleButton.addEventListener('click', function(e) {
        e.preventDefault();
        sidebar.classList.toggle('collapsed');
        this.classList.toggle('collapsed');
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const dropdown_label = document.getElementById('dropdown_label');
    const show_label = document.getElementById('show_label');
    dropdown_label.addEventListener('click', function(e) {
        e.preventDefault();
        this.classList.toggle('active');
        show_label.classList.toggle('collapsed');
    });
});
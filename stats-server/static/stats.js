$(document).ready(function () {
    $('#include').load('stats.html', callback);
});

function callback() {
    $('#statsTable').DataTable({
        "paging": false,
        "info": false,
        "searching": false,
        "ordering": true,
        "order": [[1, "desc"]]
    });
}
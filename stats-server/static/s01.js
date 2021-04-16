$(document).ready(function () {
    $('#include').load('stats01.html', callback);
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

$(document).ready(function () {
    stylizeTable();
});

function stylizeTable() {
    $('#statsTable').DataTable({
        "paging": false,
        "info": false,
        "searching": false,
        "ordering": true,
        "order": [[1, "desc"]]
    });
}

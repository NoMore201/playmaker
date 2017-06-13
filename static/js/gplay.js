function fillTable(apps) {
  let tableBox = document.getElementById('searchTable');
  let tableHtml = "";
  tableHtml += '<table class="table" id="appsTable">' +
    '<thead><tr><th>Name</th><th>Developer</th><th>Version</th>' +
    '<th>Downloads</th><th>Upload Date</th><th>Stars</th></tr>' +
    '</thead><tbody id="appsTableBody">';
  for (var i = 0; i < apps.length; i++) {
    tableHtml +=
      '<tr><td>' + apps[i].title + '</td>' +
      '<td>' + apps[i].developer + '</td>' +
      '<td>' + apps[i].version + '</td>' +
      '<td>' + apps[i].numDownloads + '</td>' +
      '<td>' + apps[i].uploadDate + '</td>' +
      '<td>' + apps[i].stars + '</td></tr>';
  }
  tableHtml += '</tbody></table>';
  tableBox.innerHTML = tableHtml;
}

function search() {
  let app = document.getElementById('searchInput').value;
  if (app.length === 0) {
    // error
    return;
  }
  let headers = new Headers();
  headers.append('Content-Type', 'application/json');
  let form = new FormData();
  form.append('search', app);

  fetch('/gplay/search', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({ 'search': app })
  }).then(response => {
    return response.text();
  }).then(text => {
    let apps = JSON.parse(text);
    if (apps.length === 0)
      return;
    fillTable(apps);
  }).catch(error => {
    console.log(error);
  });
}

switch (window.location.pathname) {
  case '/':
    break;
  case '/search':
    document.getElementById('searchBtn')
      .onclick = search;
    break;
  case '/config':
    break;
}

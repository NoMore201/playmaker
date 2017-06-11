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
  let headers = new Headers();
  headers.append("Content-Type", "text/plain");

  fetch('/gplay/search', {
    method: 'POST',
    headers: headers
  }).then(response => {
    return response.text();
  }).then(text => {
    console.log(text);
    let apps = JSON.parse(text);
    if (apps.length === 0)
      return;
    fillTable(apps);
  }).catch(error => {
    console.log(error);
  });
}

function onClickSearch() {
  let input = document.getElementById('searchInput');
  console.log(input.value);
  search();
}

switch (window.location.pathname) {
  case '/':
    console.log('home');
    break;
  case '/search':
    document.getElementById('searchBtn')
      .onclick = onClickSearch;
    break;
  case '/config':
    console.log('config');
    break;
}

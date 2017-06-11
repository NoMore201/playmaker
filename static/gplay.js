const logBox = document.getElementById('devlog');
const tBody = document.getElementById('appsTableBody');

let headers = new Headers();
headers.append("Content-Type", "text/plain");

fetch('/gplay/search', {
  method: 'POST',
  headers: headers
}).then(response => {
  if (response.ok) {
    return response.text();
  } else {
    throw Error(response.statusText);
  }
}).then(text => {
  console.log(text);
  let apps = JSON.parse(text);
  if (apps.length === 0)
    return;
  apps.forEach(app => {
    tBody.innerHTML += '<tr><td>' + app.title + '</td>' +
                       '<td>' + app.developer + '</td>' +
                       '<td>' + app.version + '</td></tr>';
  });
}).catch(error => {
  console.log(error);
});

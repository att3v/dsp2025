const http = require('http');

const server = http.createServer((req, res) => {
  // ...
});

server.listen(3000, () => {
  console.log('Server started on port 3000');
});
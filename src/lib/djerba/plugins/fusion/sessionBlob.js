// compress.js
const BGZip = require('./bgzf.js');
let input = '';

process.stdin.on('data', function (chunk) {
  input += chunk;
});

process.stdin.on('end', function () {
  const blobParameter = BGZip.compressString(input);
  console.log(blobParameter);
});


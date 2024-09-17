// compress.js
import * as BGZip from './bgzf.js'; // Adjust the path if necessary

let input = '';

process.stdin.on('data', function (chunk) {
  input += chunk;
});

process.stdin.on('end', function () {
  const blobParameter = BGZip.compressString(input);
  console.log(blobParameter);
});


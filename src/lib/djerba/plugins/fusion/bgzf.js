
const { ungzip, gzip, deflateRaw, inflateRaw, inflate } = require("./pako.esm.js");


const FEXTRA = 4;  // gzip spec F.EXTRA flag

function isgzipped(data) {
    const b = ArrayBuffer.isView(data) ? data : new Uint8Array(data);
    return b[0] ===31 && b[1] === 139;
}

/**
 * Pako does not properly ungzip block compressed files if > 1 block is present.  Test for bgzip and use wrapper.
 */
function ungzip_blocks(data) {
    const ba = ArrayBuffer.isView(data) ? data : new Uint8Array(data);
    const b = ba[3] & FEXTRA;
    if (b !== 0 && ba[12] === 66 && ba[13] === 67) {
        return unbgzf(ba.buffer);
    } else {
        return ungzip(ba);
    }
}

// Uncompress data,  assumed to be series of bgzipped blocks
function unbgzf(data, lim) {

    const oBlockList = [];
    let ptr = 0;
    let totalSize = 0;

    lim = lim || data.byteLength - 18;

    while (ptr < lim) {
        try {
            const ba = ArrayBuffer.isView(data) ? data : new Uint8Array(data, ptr, 18);
            const xlen = (ba[11] << 8) | (ba[10]);
            const flg = ba[3];
            const fextra = flg & FEXTRA;
            const si1 = ba[12];
            const si2 = ba[13];
            const slen = (ba[15] << 8) | (ba[14]);
            const bsize = ((ba[17] << 8) | (ba[16])) + 1;
            const start = 12 + xlen + ptr;    // Start of CDATA
            const bytesLeft = data.byteLength - start;
            const cDataSize = bsize - xlen - 19;
            if (bytesLeft < cDataSize || cDataSize <= 0) break;

            const a = new Uint8Array(data, start, cDataSize);
            const unc = inflateRaw(a);

            // const inflate = new Zlib.RawInflate(a);
            // const unc = inflate.decompress();

            ptr += (cDataSize - 1) + 26; //inflate.ip + 26
            totalSize += unc.byteLength;
            oBlockList.push(unc);
        } catch (e) {
            console.error(e)
            break;
        }
    }

    // Concatenate decompressed blocks
    if (oBlockList.length === 1) {
        return oBlockList[0];
    } else {
        const out = new Uint8Array(totalSize);
        let cursor = 0;
        for (let i = 0; i < oBlockList.length; ++i) {
            var b = new Uint8Array(oBlockList[i]);
            arrayCopy(b, 0, out, cursor, b.length);
            cursor += b.length;
        }
        return out;
    }
}

function bgzBlockSize(data) {
    const ba = ArrayBuffer.isView(data) ? data : new Uint8Array(data);
    const bsize = (ba[17] << 8 | ba[16]) + 1;
    return bsize;
}

// From Thomas Down's zlib implementation

const testArray = new Uint8Array(1);
const hasSubarray = (typeof testArray.subarray === 'function');

function arrayCopy(src, srcOffset, dest, destOffset, count) {
    if (count === 0) {
        return;
    }
    if (!src) {
        throw "Undef src";
    } else if (!dest) {
        throw "Undef dest";
    }
    if (srcOffset === 0 && count === src.length) {
        arrayCopy_fast(src, dest, destOffset);
    } else if (hasSubarray) {
        arrayCopy_fast(src.subarray(srcOffset, srcOffset + count), dest, destOffset);
    } else if (src.BYTES_PER_ELEMENT === 1 && count > 100) {
        arrayCopy_fast(new Uint8Array(src.buffer, src.byteOffset + srcOffset, count), dest, destOffset);
    } else {
        arrayCopy_slow(src, srcOffset, dest, destOffset, count);
    }
}

function arrayCopy_slow(src, srcOffset, dest, destOffset, count) {
    for (let i = 0; i < count; ++i) {
        dest[destOffset + i] = src[srcOffset + i];
    }
}

function arrayCopy_fast(src, dest, destOffset) {
    dest.set(src, destOffset);
}


/**
 * Compress string and encode in a url safe form
 * @param s
 */
function compressString(str) {

    const bytes = new Uint8Array(str.length);
    for (var i = 0; i < str.length; i++) {
        bytes[i] = str.charCodeAt(i);
    }
    const compressedBytes = new deflateRaw(bytes);            // UInt8Arry
    const compressedString = String.fromCharCode.apply(null, compressedBytes);      // Convert to string
    let enc = btoa(compressedString);
    return enc.replace(/\+/g, '.').replace(/\//g, '_').replace(/=/g, '-');   // URL safe
}

/**
 * Uncompress the url-safe encoded compressed string, presumably created by compressString above
 *
 * @param enc
 * @returns {string}
 */
function uncompressString(enc) {

    enc = enc.replace(/\./g, '+').replace(/_/g, '/').replace(/-/g, '=')

    const compressedString = atob(enc);
    const compressedBytes = [];
    for (let i = 0; i < compressedString.length; i++) {
        compressedBytes.push(compressedString.charCodeAt(i));
    }
    //const bytes = new Zlib.RawInflate(compressedBytes).decompress();
    const bytes = inflateRaw(compressedBytes);

    let str = ''
    for (let b of bytes) {
        str += String.fromCharCode(b)
    }
    return str;
}


/**
 * @param dataURI
 * @returns {Array<number>|Uint8Array}
 */
function decodeDataURI(dataURI, gzip) {

    const split = dataURI.split(',');
    const info = split[0].split(':')[1];
    let dataString = split[1];

    if (info.indexOf('base64') >= 0) {
        dataString = atob(dataString);

        const bytes = new Uint8Array(dataString.length);
        for (let i = 0; i < dataString.length; i++) {
            bytes[i] = dataString.charCodeAt(i);
        }

        let plain
        if (gzip || info.indexOf('gzip') > 0) {
            plain = ungzip(bytes)
        } else {
            plain = bytes
        }
        return plain
    } else {
        return decodeURIComponent(dataString);      // URL encoded string -- not currently used or tested
    }
}

export {
    unbgzf,
    bgzBlockSize,
    gzip,
    ungzip_blocks as ungzip,
    isgzipped,
    compressString,
    uncompressString,
    decodeDataURI,
    inflate,
    inflateRaw
}

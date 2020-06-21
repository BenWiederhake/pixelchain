'use strict';

/* Returns an object.
 * TODO: Should return a Promise or something. How to deal with errors? */
function readForm() {
    var rgbString = document.getElementById('f-rgb').value;
    if (rgbString.length !== 7) {
        throw `rgb has length != 7: "${rgbString}"`;
    }
    if (rgbString[0] !== '#') {
        throw `rgb does not start with "#": "${rgbString}"`;
    }
    var rgbInt = parseInt(rgbString.slice(1), 16);
    if (isNaN(rgbInt)) {
        throw `rgb is NaN?! Parsing probably failed: "${rgbString}"`;
    }
    var x = parseInt(document.getElementById('f-x').value);
    var y = parseInt(document.getElementById('f-y').value);
    var newdiff = parseInt(document.getElementById('f-newdiff').value);
    if (x > 65535 || y > 65535 || x < 0 || y < 0) {
        throw `weird x/y: ${x}/${y}"`;
    }
    if (newdiff > 32 || newdiff < 0) {
        throw `weird newdiff: ${newdiff}"`;
    }
    /* The validation is done by the server anyway, don't worry.
     * However, we want clear error messages in the client, and things
     * *will* break if x>65535, for example. */
    return {
        x: x,
        y: y,
        rgb: rgbInt,
        newdiff: newdiff,
    };
}

function updateFormStatus(status) {
    console.log(status);
    document.getElementById('submission-status').textContent = status;
}

function checkBlock(lastBlockBytesList, nonceBytesList, payloadBytesList, requiredDifficulty) {
    var hashMsg = lastBlockBytesList + nonceBytesList + payloadBytesList;
    var blockHex = sha256(hashMsg);
    console.log('blockHex', blockHex);
    var achievedDifficulty = 0;
    var wasZero = true;
    for (var i = 0; wasZero && i < blockHex.length; i++) {
        var c = blockHex[i];
        wasZero = false;
        switch (c) {
        case '0':
            achievedDifficulty += 4;
            wasZero = true;
            break;
        case '1':
            achievedDifficulty += 3;
            break;
        case '2':
        case '3':
            achievedDifficulty += 2;
            break;
        case '4':
        case '5':
        case '6':
        case '7':
            achievedDifficulty += 1;
            break;
        case '8':
        case '9':
        case 'a':
        case 'b':
        case 'c':
        case 'd':
        case 'e':
        case 'f':
            break;
        default:
            throw `Unknown hexit ${c} at position ${i} of hexhash ${blockHex}?!`;
        }
    }
    console.log('achievedDifficulty', achievedDifficulty, ', requiredDifficulty', requiredDifficulty);

    return achievedDifficulty >= requiredDifficulty;
}

function computePayload(formdata) {
    // In python:
    // payload: struct.pack('!HH3BB', x, y, r_r, r_g, r_b, r_new_diff)
    var byteList = []; // TODO: Look up actual byte array type
    byteList.push(Math.floor(formdata.x / 256));
    byteList.push(formdata.x % 256);
    byteList.push(Math.floor(formdata.y / 256));
    byteList.push(formdata.y % 256);
    byteList.push(Math.floor(formdata.rgb / 65536));
    byteList.push(Math.floor((formdata.rgb % 65536) / 256));
    byteList.push(formdata.rgb % 256);
    byteList.push(formdata.newdiff);
    return byteList;
}

function hexToByteList(hex) {
    if (hex.length % 2 == 1) {
        throw `hex has length ${hex.length}?! (was ${hex})`;
    }
    var byteList = [];
    for (var i = 0; i < hex.length / 2; i++) {
        byteList.push(parseInt(hex.slice(i * 2, i * 2 + 2), 16));
    }
    return byteList;
}

function trySubmit() {
    updateFormStatus("Parsing ...");
    var formdata = readForm();
    console.log("Parsed:", formdata);
    var payload = computePayload(formdata);
    console.log("Payload (!HH3BB, xyrgbd):", payload);
    updateFormStatus("Requesting current state ...");
    var pixelUrl = `/pixel/${formdata.x}/${formdata.y}/`;
    fetch(
        new Request(pixelUrl)
        //new Request(pixelUrl, {method: 'POST', body: '{"A": "B", "C": 42, asdfasdf asdf asdfq2t2h h4}'})
    ).then(response => {
        console.log(response);
        return response.json();
    }).then(responseJson => {
        console.log("Request result:");
        console.log(responseJson);
        updateFormStatus("Computing a block ...");
        //lastBlock: "7e49c83b400ab55e405f7396162309c0e311ee0eba248f960878c1d729987ff1", requiredDifficulty: 8, rgb: 0

        throw "NOT IMPLEMENTED";
    }).then(_ => {
        updateFormStatus("DONE, YESYESYES! :D");
    }).catch(error => {
        updateFormStatus("ERROR'D");
        console.error(error);
    });
}

function cancelSubmit() {
    console.log("Wanna cancel");
    console.error("NOT IMPLEMENTED");
}

(function () {
    updateFormStatus('Ready.');
})();

'use strict';

/* Returns an object.
 * TODO: Should return a Promise or something. How to deal with errors? */
function readForm() {
    var rgb_string = document.getElementById('f-rgb').value;
    if (rgb_string.length !== 7) {
        throw `rgb has length != 7: "${rgb_string}"`;
    }
    if (rgb_string[0] !== '#') {
        throw `rgb does not start with "#": "${rgb_string}"`;
    }
    var rgb_int = parseInt(rgb_string.slice(1), 16);
    if (isNaN(rgb_int)) {
        throw `rgb is NaN?! Parsing probably failed: "${rgb_string}"`;
    }
    return {
        x: parseInt(document.getElementById('f-x').value),
        y: parseInt(document.getElementById('f-y').value),
        rgb: rgb_int,
        newdiff: parseInt(document.getElementById('f-newdiff').value),
    };
}

function checkBlock(last_block_bytes_list, nonce_bytes_list, payload_bytes_list, required_difficulty) {
    var hash_msg = last_block_bytes_list + nonce_bytes_list + payload_bytes_list;
    var block_hex = sha256(hash_msg);
    console.log('block_hex', block_hex);
    var achieved_difficulty = 0;
    var was_zero = true;
    for (var i = 0; was_zero && i < block_hex.length; i++) {
        var c = block_hex[i];
        was_zero = false;
        switch (c) {
        case '0':
            achieved_difficulty += 4;
            was_zero = true;
            break;
        case '1':
            achieved_difficulty += 3;
            break;
        case '2':
        case '3':
            achieved_difficulty += 2;
            break;
        case '4':
        case '5':
        case '6':
        case '7':
            achieved_difficulty += 1;
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
            throw `Unknown hexit ${c} at position ${i} of hexhash ${block_hex}?!`;
        }
    }
    console.log('achieved_difficulty', achieved_difficulty, ', required_difficulty', required_difficulty);

    return achieved_difficulty >= required_difficulty;
}

function trySubmit() {
    console.log("Parsing ...");
    var formdata = readForm();
    console.log("Parsed:", formdata);
    console.log("Requesting current state ...");
    var pixel_url = `/pixel/${formdata.x}/${formdata.y}/`;
    fetch(
        new Request(pixel_url)
        //new Request(pixel_url, {method: 'POST', body: '{"A": "B", "C": 42, asdfasdf asdf asdfq2t2h h4}'})
    ).then(response => {
        console.log(response);
        return response.json();
    }).then(response_json => {
        console.log('Request result:');
        console.log(response_json);
        //lastBlock: "7e49c83b400ab55e405f7396162309c0e311ee0eba248f960878c1d729987ff1", requiredDifficulty: 8, rgb: 0
        console.error("NOT IMPLEMENTED");
    }).catch(error => {
        console.error(error);
    });
}

function cancelSubmit() {
    console.log("Wanna cancel");
    console.error("NOT IMPLEMENTED");
}

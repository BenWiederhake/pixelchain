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
        console.log('Request result:');
        console.log(response);
        // JSON.parse(response.body);
        console.error("NOT IMPLEMENTED");
    }).catch(error => {
        console.error(error);
    });
}

function cancelSubmit() {
    console.log("Wanna cancel");
    console.error("NOT IMPLEMENTED");
}

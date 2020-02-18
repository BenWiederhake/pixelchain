#!/usr/bin/env python3

from PIL import Image
import argparse
import binascii
import flask
import hashlib
import io
import secrets
import struct
import sys

app = flask.Flask('farbchain')


def log_changes(payload):
    # TODO: Do some clever logging here?
    pass


def hex_to_bytes(hex_str):
    try:
        return binascii.a2b_hex(hex_str)
    except binascii.Error:
        return None


def bytes_to_hex(bstr):
    return binascii.b2a_hex(bstr).decode('ascii')


# next_block = check_block(px.last_block, r_nonce_bytes, payload, required_difficulty)
def check_block(last_block_bytes, nonce_bytes, payload, required_difficulty):
    hash_msg = last_block_bytes + nonce_bytes + payload
    # last_block is server-assigned, payload has fixed length, so in
    # theory parsing would be possible.  This is nice as it guarantees
    # that there is no confusion attack possible.
    block_bytes = app.fc_config.hashfn(hash_msg).digest()
    achieved_difficulty = 0
    for b in block_bytes:
        if b < 0x01:  # i.e. `b == 0x00`
            achieved_difficulty += 8
            continue
        if b < 0x02:
            achieved_difficulty += 7
        elif b < 0x04:
            achieved_difficulty += 6
        elif b < 0x08:
            achieved_difficulty += 5
        elif b < 0x10:
            achieved_difficulty += 4
        elif b < 0x20:
            achieved_difficulty += 3
        elif b < 0x40:
            achieved_difficulty += 2
        elif b < 0x80:
            achieved_difficulty += 1
        break
    if achieved_difficulty >= required_difficulty:
        return block_bytes
    else:
        return None


class Pixel:
    def __init__(self, x, y, init_rgb):
        self.rgb = init_rgb
        self.last_block_bytes = secrets.token_bytes(8)
        self.difficulty = 0
        log_changes(dict(x=x, y=y, rgb=init_rgb, last_block_bytes=self.last_block_bytes, diff=self.difficulty))

    def rgb_int32(self):
        r, g, b = self.rgb
        return (r * 256 + g) * 256 + b

    def update(self, x, y, rgb, block_bytes, difficulty):
        log_changes(dict(x=x, y=y, rgb=rgb, last_block_bytes=block_bytes, diff=self.difficulty))
        self.rgb, self.last_block_bytes, self.difficulty = rgb, block_bytes, difficulty


class Canvas:
    def __init__(self, fc_config):
        self.fc_config = fc_config
        self.data = [Pixel(x, y, fc_config.init_rgb) for y in range(self.fc_config.resolution[1]) for x in range(self.fc_config.resolution[0])]
        self.update_png()
        self.pending_pokes = 0
        self.estimated_work = 0
        self.updates = 0

    def resize(self, new_size):
        raise NotImplementedError()

    def update_png(self):
        self.pending_pokes = 0
        img = Image.new('RGB', self.fc_config.resolution)
        img.putdata([p.rgb for p in self.data])
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        self.png = buf.getvalue()

    def get_pixel(self, x, y):
        w, h = self.fc_config.resolution
        if 0 <= x < w and 0 <= y < h:
            return self.data[y * w + x]
        else:
            return None

    def poke(self, difficulty):
        self.pending_pokes += 1
        self.updates += 1
        self.estimated_work += 1 << difficulty
        if self.pending_pokes >= app.fc_config.cache_latency_pixels:
            self.update_png()


@app.route('/')
def api_hello_world():
    return 'Hello World!  FIXME: Insert link to project page here.'


@app.route('/config/')
def api_config():
    return flask.json.jsonify(
        width=app.fc_config.resolution[0],
        height=app.fc_config.resolution[1],
        hash=app.fc_config.hash,
        pixelPenalty=app.fc_config.pixel_penalty,
        capturePenalty=app.fc_config.capture_penalty,
    )


@app.route('/stats/')
def api_stats():
    return flask.json.jsonify(
        lagging_pixels=app.canvas.pending_pokes,
        total_estimated_hashes=app.canvas.estimated_work,
        total_updates=app.canvas.updates,
        connections='unknown',
        bandwidth_bips='unknown',
        estimated_hps='unknown',
    )


@app.route('/pixel/<int:x>/<int:y>/', methods=['GET', 'PUT'])
def api_pixel(x=-1, y=-1):
    px = app.canvas.get_pixel(x, y)
    if px is None:
        flask.abort(404)
    required_difficulty = app.fc_config.pixel_penalty + px.difficulty
    response = flask.json.jsonify(
        rgb=px.rgb_int32(),
        requiredDifficulty=required_difficulty,
        lastBlock=bytes_to_hex(px.last_block_bytes),
    )

    if flask.request.method == 'GET':
        return response

    if flask.request.method != 'PUT':
        flask.abort(400)

    # Alrighty!  Let's see whether this makes sense:
    if flask.request.content_length > 200:
        # Requests have no business being that long.
        flask.abort(400)
    req = flask.request.get_json(force=True)
    if not isinstance(req, dict):
        flask.abort(400)
    r_last_block_hex = req.pop('lastBlock', None)
    r_nonce = req.pop('nonce', None)
    r_new_diff = req.pop('newDifficulty', None)
    r_rgb = req.pop('rgb', None)
    if req or not isinstance(r_last_block_hex, str) or not isinstance(r_nonce, str) or not isinstance(r_new_diff, int) or not isinstance(r_rgb, int):
        flask.abort(400)
    if r_new_diff < 0 or r_new_diff >= 64 or r_rgb < 0 or r_rgb > 0xFFFFFF:
        flask.abort(400)
    if r_last_block_hex != bytes_to_hex(px.last_block_bytes):
        response.status_code = 409
        response.status = "409 CONFLICT"
        return response
    r_nonce_bytes = hex_to_bytes(r_nonce)
    if r_nonce_bytes is None:
        flask.abort(400)
    required_difficulty += r_new_diff
    r_r = (r_rgb >> 16) & 0xFF
    r_g = (r_rgb >>  8) & 0xFF
    r_b = (r_rgb >>  0) & 0xFF
    payload = struct.pack('!HH3BB', x, y, r_r, r_g, r_b, r_new_diff)
    next_block_bytes = check_block(px.last_block_bytes, r_nonce_bytes, payload, required_difficulty)
    if next_block_bytes is None:
        flask.abort(403)  # Something didn't work out, but we can't detect what.
    px.update(x, y, (r_r, r_g, r_b), next_block_bytes, r_new_diff)
    app.canvas.poke(required_difficulty)
    response = flask.Response()
    response.status = '201 CREATED'
    response.status_code = 201
    return response


@app.route('/latest/', methods=['GET', 'POST'])
def api_latest():
    app.canvas.update_png()  # FIXME: Remove in production
    return flask.Response(app.canvas.png, mimetype='image/png')


@app.route('/capture/', methods=['GET', 'POST'])
def api_capture():
    flask.abort(501)  # Not implemented


def parse_resolution(r):
    assert isinstance(r, str)
    parts_s = r.split('x')
    if len(parts_s) != 2:
        raise argparse.ArgumentTypeError('Resolution "{!r}" must be of form WxH, but contains {} parts instead of 2.'.format(r, len(parts_s)))
    try:
        parts_i = [int(p) for p in parts_s]
    except ValueError:
        parts_i = [-1]
    if not all(0 < p < 65536 for p in parts_i):
        raise argparse.ArgumentTypeError('Resolution "{!r}" must be of form WxH with reasonable integers.'.format(r, len(parts_s)))
    return tuple(parts_i)


def parse_rgb(rgb_str):
    assert isinstance(rgb_str, str)
    if len(rgb_str) != 6:
        raise argparse.ArgumentTypeError('RGB value "{}" must consist of 6 hexits (RRGGBB), but had only {}.'.format(rgb_str, len(rgb_str)))
    rgb_parts = (rgb_str[0:2], rgb_str[2:4], rgb_str[4:6])
    try:
        rgb_components = [min(255, max(0, int(p, 16))) for p in rgb_parts]
    except ValueError as e:
        raise argparse.ArgumentTypeError('RGB value "{}" must consist of 6 hexits: {}'.format(rgb_str, e.msg))
    return tuple(rgb_components)


def make_parser(progname):
    parser = argparse.ArgumentParser(
        prog=progname, description='Starts a new farbchain server.')
    parser.add_argument('-r', '--resolution', default='640x480',
        metavar='WxH', type=parse_resolution,
        help='The size of the screen (defaults to 640x480)')
    parser.add_argument('--hash', default='sha256', choices=hashlib.algorithms_available,
        help='The hash function to be used (defaults to sha256)')
    parser.add_argument('--init-rgb', default='000000', type=parse_rgb,
        help='The hash function to be used (defaults to sha256)')
    parser.add_argument('--pixel-penalty', default=8, type=int,
        help='Additional difficulty when setting a pixel (defaults to 8)')
    parser.add_argument('--capture-penalty', default=20, type=int,
        help='Difficulty when getting a canvas capture, should be less that log2(W*H) (defaults to 20)')
    parser.add_argument('--cache-latency-pixels', default=200, type=int,
        help='When to automatically regenerate the screenshot (defaults to 200)')
    return parser


def postprocess_app():
    log_changes(app.fc_config)
    app.fc_config.hashfn = getattr(hashlib, app.fc_config.hash)
    app.canvas = Canvas(app.fc_config)


def run():
    global app
    app.fc_config = make_parser(sys.argv[0]).parse_args(sys.argv[1:])
    print('Generating image ...')
    postprocess_app()    
    print('Running with config:\n{}'.format(app.fc_config))
    app.run(port=8080)


if __name__ == '__main__':
    run()

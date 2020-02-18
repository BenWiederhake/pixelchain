#!/usr/bin/env python3

from PIL import Image
import argparse
import flask
import hashlib
import io
import secrets
import sys

app = flask.Flask('farbchain')


class Pixel:
    def __init__(self, x, y, init_rgb):
        self.rgb = init_rgb
        self.last_block = secrets.token_hex(8)
        self.difficulty = 0

    def rgb_int32(self):
        r, g, b = self.rgb
        return (r * 256 + g) * 256 + b

    # FIXME: Other accessors?


class Canvas:
    def __init__(self, fc_config):
        self.fc_config = fc_config
        self.data = [Pixel(x, y, fc_config.init_rgb) for y in range(self.fc_config.resolution[1]) for x in range(self.fc_config.resolution[0])]
        self.update_png()

    def resize(self, new_size):
        raise NotImplementedError()

    def update_png(self):
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

    # FIXME: Other accessors?


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


@app.route('/pixel/<int:x>/<int:y>/', methods=['GET'])
def api_pixel(x=-1, y=-1):
    px = app.canvas.get_pixel(x, y)
    if px is None:
        flask.abort(404)
    required_difficulty = app.fc_config.pixel_penalty + px.difficulty

    return flask.json.jsonify(
        rgb=px.rgb_int32(),
        requiredDifficulty=required_difficulty,
        lastBlock=px.last_block,
    )


# request.get_json(force=True)


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
    return parser


def postprocess_app():
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

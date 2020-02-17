# farbchain

> Colors in a block-ish chain.  Like pixelflut, but slower.

This is an interactive competition for screenspace / canvas space.

This repository provides a Proof-of-Concept python server,
performant Rust server, and a Proof-of-Concept (and intentionally bad) python client.

## Table of Contents

- [Install](#install)
- [Usage](#usage)
- [Performance](#performance)
- [TODOs](#todos)
- [NOTDOs](#notdos)
- [Contribute](#contribute)

## Install

Depends on which part we're talking about.

### Python server

FIXME

### Rust server

FIXME

### Python client

FIXME

## Usage

The idea is that you run the server while connected to a projector,
and make it available to the network.  Kinda like [pixelflut](https://github.com/defnull/pixelflut#pixelflut-multiplayer-canvas).

### Python server

FIXME

### Rust server

FIXME

### Python client

FIXME

## Performance

FIXME

## TODOs

* Everything!
* Maybe limit connections to 20 per IP?

## NOTDOs

Here are some things this project will definitely not support:
* Fancy streaming to anywhere.  If you need that, make a video capture of the window.
* Making coffee for you.  (Bring your own!)

Here are things that I won't implement, but you might find nice:
* Logging which updates are processed in which order, or even better: Properly outputting the "farb-blockchain" to a file or something.
* Fancy quotas: the idea is to adjust the difficulties such that farbchain is CPU-bound on the client side, so quotas should not be necessary.

## Contribute

Feel free to dive in! [Open an issue](https://github.com/BenWiederhake/farbchain/issues/new) or submit PRs.

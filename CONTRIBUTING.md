# Contributing Guidelines

Please follow common guidelines for our projects [here](https://github.com/packit/contributing).

## Testing

We recommend running the tests in a container. You need to have `podman` or
`docker` installed for this.

To build the test image run:

    make build-test-image

You can run the test now with:

    make check-in-container

`TEST_TARGET` can be used to select a subset of the tests to run, for example:

    TEST_TARGET=tests/test_duplication.py make check-in-container

`make check` is also available to run the tests in the environment of your
choice, but first you'll need to make sure to install all the package and test
dependencies. For now it is up to the reader to figure out how to do this on
their system.

---

Thank you for your interest!

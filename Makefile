TEST_TARGET := ./tests
CONTAINER_ENGINE ?= $(shell command -v podman 2> /dev/null || echo docker)
TESTS_CONTAINER_RUN=$(CONTAINER_ENGINE) run --rm -ti -v $(CURDIR):/src:Z $(TESTS_IMAGE)
TESTS_IMAGE=requre_tests

build-test-image:
	$(CONTAINER_ENGINE) build --tag $(TESTS_IMAGE) -f Dockerfile.tests .

check-in-container:
	$(TESTS_CONTAINER_RUN) bash -c "pip3 install .; make check TEST_TARGET=$(TEST_TARGET)"


install:
	pip3 install --user .

clean:
	git clean -fd
	find . -name __pycache__ -exec rm -r {} \;
	find . -name \*.pyc -exec rm {} \;

check:
	PYTHONPATH=$(CURDIR) PYTHONDONTWRITEBYTECODE=1 python3 -m pytest --verbose --showlocals $(TEST_TARGET)

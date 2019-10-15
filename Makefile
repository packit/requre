TESTS_TARGET := ./tests
TESTS_CONTAINER_RUN=podman run --rm -ti -v $(CURDIR):/src --security-opt label=disable $(TESTS_IMAGE)
TESTS_IMAGE=requre_tests

tests_image:
	podman build --tag $(TESTS_IMAGE) -f Dockerfile.tests .
	sleep 2

check_in_container: tests_image
	$(TESTS_CONTAINER_RUN) bash -c "pip3 install .; make check TESTS_TARGET=$(TESTS_TARGET)"


install:
	pip3 install --user .

clean:
	git clean -fd
	find . -name __pycache__ -exec rm -r {} \;
	find . -name \*.pyc -exec rm {} \;

check:
	PYTHONPATH=$(CURDIR) PYTHONDONTWRITEBYTECODE=1 python3 -m pytest --verbose --showlocals $(TESTS_TARGET)

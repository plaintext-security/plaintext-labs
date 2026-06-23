FROM python:3.12.9-slim

WORKDIR /lab

# The eval itself is pure stdlib; pytest + coverage are for the test suite and the
# coverage-as-foil step. No model, no network needed at runtime.
RUN pip install --no-cache-dir pytest==8.3.5 coverage==7.6.12

COPY . /lab

CMD ["sleep", "infinity"]

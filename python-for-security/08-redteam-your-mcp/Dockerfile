FROM python:3.12-slim

# Offline red-team demo: no model call needed to show direct + indirect prompt
# injection and the structural guards that catch them. pydantic backs the indicator
# allow-list (Module 02 models); pytest runs the regression gate.
RUN pip install --no-cache-dir "pytest==8.*" "pydantic>=2,<3"

WORKDIR /lab
COPY . /lab

CMD ["sleep", "infinity"]

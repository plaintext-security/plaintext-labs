FROM ghcr.io/opentofu/opentofu:1.9.1

WORKDIR /lab

COPY . /lab

# The opentofu base image sets ENTRYPOINT ["tofu"]; reset it so the
# Makefile's `sh -c` wrappers and `sleep infinity` run as plain commands.
ENTRYPOINT []

CMD ["sleep", "infinity"]

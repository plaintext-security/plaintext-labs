# Module 08 — CI/CD Pipeline Security
# gitleaks + trivy, pinned versions.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl git jq \
    && rm -rf /var/lib/apt/lists/*

# Resolve the build arch so the pinned binaries match the host (CI is amd64;
# Apple Silicon is arm64). gitleaks names its arm64 asset *_linux_arm64 and its
# amd64 asset *_linux_x64, so map TARGETARCH accordingly.
ARG TARGETARCH
RUN case "$TARGETARCH" in \
      arm64) GL_ARCH=arm64 ;; \
      *)     GL_ARCH=x64 ;; \
    esac; \
    echo "$GL_ARCH" > /tmp/gl_arch

# gitleaks — fast secrets scanner, offline CI gate
RUN GL_ARCH="$(cat /tmp/gl_arch)"; curl -sSfL \
      "https://github.com/gitleaks/gitleaks/releases/download/v8.18.4/gitleaks_8.18.4_linux_${GL_ARCH}.tar.gz" \
      | tar -xz -C /usr/local/bin gitleaks

# trivy — vulnerability and misconfiguration scanner. v0.52.2 was retracted
# upstream (tag resolves but the asset 404s); re-pinned to a current release.
RUN curl -sSfL \
      "https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh" \
      | sh -s -- -b /usr/local/bin v0.71.2

WORKDIR /lab
COPY . /lab

CMD ["bash"]

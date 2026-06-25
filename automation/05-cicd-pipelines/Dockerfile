FROM python:3.12.9-slim

ARG GITLEAKS_VERSION=8.30.1
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates git && \
    case "$(dpkg --print-architecture)" in \
      arm64) GL_ARCH=arm64 ;; \
      amd64) GL_ARCH=x64 ;; \
      *) echo "unsupported arch" && exit 1 ;; \
    esac && \
    curl -sSL \
      "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_${GL_ARCH}.tar.gz" \
      | tar -xz -C /usr/local/bin/ gitleaks && \
    chmod +x /usr/local/bin/gitleaks && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /lab

COPY . /lab

CMD ["sleep", "infinity"]

# This is a Dockerfile for the Development Container

# Use the Python base image
ARG VARIANT="3.12-bullseye"
FROM mcr.microsoft.com/devcontainers/python:${VARIANT}

# Explicitly disable health check for development container
HEALTHCHECK NONE

USER root
COPY ca-certs.crt /usr/local/share/ca-certificates
RUN update-ca-certificates

USER vscode

FROM mambaorg/micromamba:latest
USER root
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --no-install-recommends --reinstall \
    libgl1 \
    libglib2.0-0 \
    libgl1-mesa-glx
COPY --chown=$MAMBA_USER:$MAMBA_USER ./environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes
ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /benchmark
COPY ./apis ./apis
COPY ./static ./static
COPY ./server.py ./server.py
CMD ["gunicorn", "--bind=0.0.0.0:80", "--threads=10", "server:app"]
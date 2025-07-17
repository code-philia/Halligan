# Halligan

[![Paper](https://img.shields.io/badge/Paper-green)](http://linyun.info/publications/usenix-sec25.pdf)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

📢 [[Project Page](https://halligan.pages.dev/)] [[Examples](https://github.com/gyataro/halligan-examples)] [[Zenodo](https://zenodo.org/records/15709075)] [[Models](https://huggingface.co/code-philia/halligan-models/tree/main)]

Halligan is a vision-language model (VLM) agent designed to solve visual CAPTCHA challenges. It is published in *"Are CAPTCHAs Still Bot-hard? Generalized Visual CAPTCHA Solving with Agentic Vision Language Model"* (USENIX Security'25)

> [!IMPORTANT] 
> **Disclaimer:**
> Halligan is provided strictly for *research purposes* only. By using this tool, you agree to:
> - Abide by ethical principles of Internet and AI usage
> - Not use Halligan to bypass CAPTCHA protections on real-world services
> - Not violate the terms of service or usage policies of any vision-language model (VLM) providers (e.g., OpenAI, Anthropic, etc.)
>
> You are solely responsible for any misuse of this system, including activities that result in harm, unauthorized access, or financial loss to others. The authors disclaim any liability arising from improper or malicious use.

## Environment

- **Hardware Dependencies:** We tested the functionality on a desktop computer with 16GB of GPU VRAM (Optional), 8GB of system RAM, and 16GB of available disk space.

- **Software Dependencies:** We recommend using Linux. Our setup was tested on Ubuntu 20.04.3 LTS with Pixi 0.47.0, CUDA 12.1 (Optional), Docker 24.0.7, and Docker Compose 2.21.0.

## Setup

1. Install [Docker Desktop](https://docs.docker.com/compose/install/) and [Pixi](https://pixi.sh/dev/installation/).

2. Run the benchmark server and browser using Docker:

    ```bash
    cd benchmark
    docker compose up
    ```

3. To setup Halligan, setup the Pixi environment in `/halligan`. Then, download the models used in Halligan. Finally, edit the .env file to include your OpenAI API key and other relevant credentials.

    ```bash
    cd halligan
    pixi install
    bash get_models.sh
    cp .env.example .env
    ```

## Usage

1. (Sanity Check) Verify that the benchmark, browser, and Halligan’s core components are all functional:

    ```bash
    pixi run pytest basic_test.py --verbose
    ```

2. (Generate CAPTCHA Solution Scripts) This will run Halligan to generate Python solutions for 26 types of CAPTCHAs. Output is saved to `/results/generation`.

    ```bash
    pixi run python generate.py
    ```

3. (Execute the Solutions) This will run the generated solutions and demonstrate Halligan solving the CAPTCHAs. Results are saved to `/results/execution`.

    ```
    pixi run python execute.py
    ```

# CAPTCHA Benchmark

This benchmark contains 26 types of visual CAPTCHAs, totaling 2600 challenges.

Each CAPTCHA type is implemented as a modular Flask Blueprint (`/apis`) that encapsulates its routes, challenges (`.json`), and static (`.html`, `.css`, `.js`) files. These Blueprints are registered in the main Flask application (`/server.py`). You can extend the benchmark by adding new CAPTCHA types as Blueprints.

## Usage

### Running Locally

1. **Setup Local Environment:**

    Create a new Conda environment from YAML file.
    ```bash
    conda env create --f environment.yml --name [ENV_NAME]
    conda activate [ENV_NAME]
    ```

2. **Start Flask Server**
    
    Server defaults to `localhost:3334`.
    ```bash
    python server.py
    ```

### Running via Docker Container

1. **Build Docker Image**

    Build a new docker image `[IMAGE_NAME]` from the default `Dockerfile` in the current directory.
    ```bash
    docker build -t [IMAGE_NAME] .
    ```

2. **Create a New Container**

    Create a new container from `[IMAGE_NAME]`. The server listens on container port `80` by default, and you can map it to `[HOST_PORT]` on your machine.
    ```
    docker run -p [HOST_PORT]:80 -d [IMAGE_NAME]
    ```

### Getting Evaluation Results

Once you `POST` a challenge solution, the server responds with a JSON payload in the format `{solved: true/false}`. Additionally, the server automatically logs each attempt in a `results.log` file that you can review.

## Routes

Request the routes in a browser to load interactive CAPTCHA challenges, where the id represents the challenge number ranging from 1 to 100.

| Route | Description |
| --- | --- |
| `/lemin/{id}` | [Lemin](https://www.leminnow.com/) drag-and-drop puzzle CAPTCHA. |
| `/geetest/slide/{id}` | [GeeTest](https://www.geetest.com/en) drag slider to align puzzle piece with its slot. |
| `/geetest/gobang/{id}` | [GeeTest](https://www.geetest.com/en) match 5 identifical items horizontally / vertically / diagonally. |
| `/geetest/icon/{id}` | [GeeTest](https://www.geetest.com/en) click on colored icons in a 2D area according to order. |
| `/geetest/iconcrush/{id}` | [GeeTest](https://www.geetest.com/en) match 3 identifacal tiles in a row or column. |
| `/baidu/{id}` | Drag slider to adjust randomly rotated images to their upright orientation. |
| `/hcaptcha/{id}` | [hCaptcha](https://www.hcaptcha.com/) (1) Select items in 3x3 grid according to instruction. (2) Click on point in 2d area according to instruction. |
| `/botdetect/{id}` | [BotDetect](https://captcha.com/) text-based CAPTCHA. |
| `/arkose/multichoice/square_icon/{id}` | Pick one square that shows two identical objects. |
| `/arkose/multichoice/galaxies/{id}` | Pick the spiral galaxy. |
| `/arkose/multichoice/dice_pair/{id}` | Pick the dice pair with the same icon facing up. |
| `/arkose/multichoice/hand_number/{id}` | Pick the image where the total fingers add up to 4. |
| `/arkose/multichoice/card/{id}` | Pick the matching cards. |
| `/arkose/multichoice/counting/{id}` | Pick the image where the number matches the amount of animals. |
| `/arkose/multichoice/rotated/{id}` | Pick the image that is the correct way up. |
| `/arkose/paged/dice_match/{id}` | Click the arrows to sum the dice and match the number in the reference image. |
| `/arkose/paged/rockstack/{id}` | Click the arrows to pick the group of rocks that has the amount indicated in the reference image. |
| `/arkose/paged/numbermatch/{id}` | Click the arrows to change the number of objects until it matches the reference image. |
| `/arkose/paged/orbit_match_game/{id}` | Click the arrows to move the icon into the orbit in the indicated reference image. |
| `/arkose/paged/3d_rollball_objects/{id}` | Click the arrows to rotate the object to face in the direction of the hand in the reference image. |
| `/mtcaptcha/{id}` | [MTCaptcha](https://www.mtcaptcha.com/) text-based CAPTCHA. |
| `/recaptchav2/{id}` | [reCAPTCHA v2](https://developers.google.com/recaptcha/docs/display) |
| `/tencent/{id}` | [Tencent CAPTCHA](https://www.tencentcloud.com/products/captcha) visual reasoning on 3D objects in a scene. |
| `/yandex/text/{id}` | Yandex text-based CAPTCHA. |
| `/yandex/kaleidoscope/{id}` | Yandex drag slider to restore image scrambled in a 4x4 set of tiles. |
| `/amazon/{id}` | [AWS WAF](https://aws.amazon.com/waf/) Click on the end of the car's path in a 2D map. |
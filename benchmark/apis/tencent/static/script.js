function init(id) {
    document.addEventListener("DOMContentLoaded", async () => {
        const challenge = document.querySelector("#captcha-container");
        let response = await fetch(`./challenge/${id}`);
        let data = await response.json();
        if (!response.ok) {
            console.error(data.message);
            return
        }

        const instruction = data["instruction"];
        const instruction_image = data["instruction_image"][0];
        new Captcha(id, challenge, instruction, instruction_image);
    })
}

class Captcha {
    /**
     * @param {string} id captcha challenge id
     * @param {Element} challenge
     * @param {string} instruction
     * @param {string} image
     */
    constructor(id, challenge, instruction, image) {
        this.id = id;
        this.width = 340;
        this.height = 230;
        this.state = [0, 0];

        // Load instruction
        challenge.querySelector(".tcaptcha-instruction").innerText = instruction;

        // Load challenge image
        const canvas = challenge.querySelector("canvas");
        const context = canvas.getContext("2d");
        const challenge_image = new Image();
        challenge_image.src = `data:image/png;base64,${image}`;
        challenge_image.onload = () => {
            context.drawImage(challenge_image, 0, 0, this.width, this.height);
            let background = context.getImageData(0, 0, this.width, this.height);

            canvas.onclick = (event) => {
                let rect = event.target.getBoundingClientRect();
                let canvas_x = event.clientX - rect.left;
                let canvas_y = event.clientY - rect.top;
                let x = canvas_x / this.width;
                let y = canvas_y / this.height;

                if (x > 0 && x < 1 && y > 0 && y < 1) {
                    context.putImageData(background, 0, 0);
                    this.state = [x, y];

                    context.fillStyle = "white";
                    context.beginPath();
                    context.arc(canvas_x, canvas_y, 6, 0, 2 * Math.PI);
                    context.fill();
                    this.submit();
                }
            }
        }
    }

    // Submit challenge
    submit = async () => {
        let config = {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                id: this.id, 
                state: this.state
            })
        }
        let response = await fetch("./submit", config);
        let data = await response.json();
        if (!response.ok) console.error(data.message);
        else console.log(data);
    }
}
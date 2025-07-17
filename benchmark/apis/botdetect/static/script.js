
function init(id) {
    document.addEventListener("DOMContentLoaded", async () => {
        let response = await fetch(`./challenge/${id}`);
        let data = await response.json();
        if (!response.ok) {
            console.error(data.message);
            return
        }

        image = data["instruction_image"][0];
        length = data["labels"][0].length;

        new Captcha(id, image, length);
    })
}

class Captcha {
    /**
     * @param {string} id
     * @param {string} image 
     * @param {Number} length
     */
    constructor(id, image, length) {
        this.id = id;
        this.state = "";

        const challenge = document.querySelector("#CaptchaImage");
        challenge.src = `data:image/png;base64,${image}`;

        const input = document.querySelector("#captchaCode");
        input.addEventListener("input", async () => {
            this.state = input.value;
            if (this.state.length === length) {
                input.disabled = true;
                await this.submit();
            }
        })
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

function init(id) {
    document.addEventListener("DOMContentLoaded", async () => {
        let response = await fetch(`./challenge/${id}`);
        let data = await response.json();
        if (!response.ok) {
            console.error(data.message);
            return
        }

        image = data["instruction_image"][0];

        new Captcha(id, image);
    })
}

class Captcha {
    /**
     * @param {string} id
     * @param {string} image 
     */
    constructor(id, image) {
        this.id = id;

        const challenge = document.querySelector(".AdvancedCaptcha-View img");
        challenge.src = `data:image/png;base64,${image}`;

        const input = document.querySelector("#captcha");
        const submit = document.querySelector("#submit");
        submit.onclick = async () => {
            input.disabled = true;
            await this.submit(input.value);
        }
    }

    // Submit challenge
    submit = async (state) => {
        let config = {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                id: this.id, 
                state: state
            })
        }
        let response = await fetch("./submit", config);
        let data = await response.json();
        if (!response.ok) console.error(data.message);
        else console.log(data);
    }
}
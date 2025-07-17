function init(id) {
    document.addEventListener("DOMContentLoaded", async () => {
        const challenge_frame = document.querySelector("#funcaptcha");

        challenge_frame.onload = async () => {
            const container = challenge_frame.contentWindow;
            const loading = container.document.querySelector(".loading");
            const checkbox = container.document.querySelector(".checkbox");
            const challenge = container.document.querySelector(".challenge");
            const start_button = container.document.querySelector(".start-button");
        
            let response = await fetch(`./${id}/challenge`);
            let data = await response.json();
            if (!response.ok) {
                console.error(data.message);
                return
            }

            loading.style["display"] = "none";
            checkbox.style["display"] = "flex";

            const instruction = data["instruction"];
            const images = data["instruction_image"];

            start_button.addEventListener("click", async () => {
                checkbox.style["display"] = "none";
                challenge.style["display"] = "flex";

                new Captcha(id, challenge, instruction, images);
            })
        }
    })
}

class Captcha {
    /**
     * @param {string} id captcha challenge id
     * @param {string} instruction challenge instruction text
     * @param {string[]} images challenge image choices
     */
    constructor(id, challenge, instruction, images) {
        this.id = id;
        
        // Initialize instruction text
        const instruction_element = challenge.querySelector(".challenge-instruction");
        const regex = /\*([^*]+)\*/g;
        instruction = instruction.replace(regex, '<strong>$1</strong>');
        const instruction_html = `<span role='text'>${instruction} (1 of 1)</span>`;
        instruction_element.innerHTML = instruction_html;

        // Initialize choices
        for (let i = 0; i < 6; i++) {
            let tile = challenge.querySelector(`#tile-${i+1}`);
            tile.style["backgroundImage"] = `url(data:image/png;base64,${images[0]})`;
            tile.onclick = async () => await this.submit(i);
        }
    }

    // Submit challenge
    submit = async (choice) => {
        let config = {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                id: this.id, 
                state: choice
            })
        }
        let response = await fetch(`./${this.id}/submit`, config);
        let data = await response.json();
        if (!response.ok) console.error(data.message);
        else console.log(data);
    }
}
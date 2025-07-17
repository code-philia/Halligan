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
            const instruction_image = data["instruction_image"];
            const images = data["images"];

            start_button.addEventListener("click", async () => {
                checkbox.style["display"] = "none";
                challenge.style["display"] = "flex";

                new Captcha(id, challenge, instruction, instruction_image, images);
            })
        }
    })
}

class Captcha {
    /**
     * @param {string} id captcha challenge id
     * @param {string} instruction challenge instruction text
     * @param {string[]} instruction_image challenge instruction image
     * @param {string[]} images challenge image choices
     */
    constructor(id, challenge, instruction, instruction_images, images) {
        this.id = id;
        this.state = 0;
        this.images = images;
        this.choices = challenge.querySelector(".answer-choices");
        this.answer_img = challenge.querySelector(".answer-image");

        // Initialize instruction text
        const instruction_element = challenge.querySelector(".challenge-instruction");
        const regex = /\*([^*]+)\*/g;
        instruction = instruction.replace(regex, '<strong>$1</strong>');
        const instruction_html = `<span role='text'>${instruction} (1 of 1)</span>`;
        instruction_element.innerHTML = instruction_html;
        
        // Initialize instruction image
        const key_frame_img = challenge.querySelector(".key-frame-image");
        key_frame_img.src = `data:image/png;base64,${instruction_images[0]}`;

        // Initialize choice
        this.answer_img.style["backgroundImage"] = `url(data:image/png;base64,${this.images[this.state]})`;

        // Initialize choice indicators
        for (var i = 0; i < images.length; i++) {
            var choice = document.createElement('div');
            if (i == 0) choice.classList.add("active");
            choice.classList.add("answer-choice");
            choice.id = `choice-${i}`;
            choice.setAttribute('aria-hidden', 'true');
            this.choices.appendChild(choice);
        }

        // Setup prev, next, submit buttons
        const prev_button = challenge.querySelector(".left-arrow");
        const next_button = challenge.querySelector(".right-arrow");
        const submit_button = challenge.querySelector(".submit-button");
        prev_button.onclick = () => this.update_choice(-1);
        next_button.onclick = () => this.update_choice(+1);
        submit_button.onclick = async () => await this.submit();
    }

    update_choice = (change) => {
        let prev = this.choices.querySelector(`#choice-${this.state}`);
        if (change < 0) this.state = (this.state + change + this.images.length) % this.images.length;
        else this.state = (this.state + change) % this.images.length;
        let next = this.choices.querySelector(`#choice-${this.state}`);
        prev.classList.remove("active");
        next.classList.add("active");
        this.answer_img.style["backgroundImage"] = `url(data:image/png;base64,${this.images[this.state]})`;
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
        let response = await fetch(`./${this.id}/submit`, config);
        let data = await response.json();
        if (!response.ok) console.error(data.message);
        else console.log(data);
    }
}
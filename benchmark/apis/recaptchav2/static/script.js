function init(id) {
    document.addEventListener("DOMContentLoaded", async () => {
        const checkbox_frame = document.querySelector("#checkbox");
        const challenge_node = document.querySelector("#challenge");

        checkbox_frame.onload = () => {
            const checkbox = checkbox_frame.contentWindow;
            const checkbox_box = checkbox.document.querySelector('.recaptcha-checkbox.goog-inline-block.rc-anchor-checkbox');
            const checkbox_spinner = checkbox.document.querySelector('.recaptcha-checkbox-spinner');
            const checkbox_border = checkbox.document.querySelector('.recaptcha-checkbox-border');
            
            checkbox_box.onclick = async () => {
                checkbox_box.classList.add('recaptcha-checkbox-loading');
                checkbox_box.classList.add('recaptcha-checkbox-disabled');
                checkbox_border.style.display = 'none';
                checkbox_spinner.style.display = 'block';
                checkbox_spinner.style.opacity = '1';

                let response = await fetch(`./challenge/${id}`);
                let data = await response.json();
                if (!response.ok) {
                    console.error(data.message);
                    return;
                }

                const subtype = data["subtype"];
                const instruction = data["instruction"];
                const images = data["images"];
                
                new Captcha(id, challenge_node, subtype, instruction, images);
            }
        }
    })
}

class Captcha {
    /**
     * @param {string} id captcha challenge id
     * @param {Element} parent parent node of captcha challenge
     * @param {string} subtype challenge type
     * @param {string} instruction challenge instruction text
     * @param {string[]} images challenge image choices
     */
    constructor(id, parent, subtype, instruction, images) {

        const loader = {
            "binary": {
                state: Array(9).fill(false),
                frame: this.load_frame("binary", 400, 580),
                load_challenge: this.load_binary
            },
            "tile": {
                state: Array(16).fill(false),
                frame: this.load_frame("tile", 400, 580),
                load_challenge: this.load_tile
            }
        }[subtype];

        // Inistialize challenge state
        this.id = id;
        this.state = loader.state;
        this.challenge_type = subtype;

        // Initialize challenge frame
        parent.appendChild(loader.frame);

        // Populate frame with instruction and images
        loader.load_challenge(loader.frame, instruction, images);

        console.log(loader.frame.style.height)
        parent.style["width"] = loader.frame.style["width"];
        parent.style["height"] = loader.frame.style["height"];

        // Make frame visible
        const wrapper = document.querySelector('#challenge-wrapper');
        wrapper.classList.toggle('show');
    }

    load_frame = (type, width, height) => {
        const challenge_frame = document.createElement('iframe');
        challenge_frame.src = `./challenge_${type}.html`;
        challenge_frame.frameborder = "0";
        challenge_frame.scrolling = "no";
        challenge_frame.title = "recaptcha challenge expires in two minutes";
        challenge_frame.style = `border: 0px; z-index: 2000000000; position: relative; width: ${width}px; height: ${height}px;`;
        return challenge_frame;
    }

    load_binary = (frame, instruction, images) => {
        const challenge = frame.contentWindow;
        challenge.onload = () => {
            // Load text instruction
            const keyword = challenge.document.querySelector('.rc-keyword');
            keyword.innerText = instruction;

            // Load submit button
            const submit = challenge.document.querySelector("#recaptcha-verify-button");
            submit.onclick = () => this.submit();

            // Load challenge images
            images.forEach((image, i) => {
                const choice = challenge.document.querySelector(`td[tabindex="${i+4}"]`)
                const wrapper_image = choice.querySelector("img")
                wrapper_image.src = `data:image/png;base64,${image}`

                choice.onclick = () => {
                    this.state[i] = !this.state[i];
                    var toggle = this.state[i];
                    choice.classList.toggle("rc-imageselect-tileselected", toggle);
                    if (this.state.filter(x => x === true).length > 0) {
                        submit.innerText = "Verify"
                    } else {
                        submit.innerText = "Skip"
                    }
                }
            })
        }
    }

    load_tile = (frame, instruction, images) => {
        const challenge = frame.contentWindow;
        challenge.onload = () => {
            // Load text instruction
            const keyword = challenge.document.querySelector('.rc-keyword');
            keyword.innerText = instruction;

            // Load submit button
            const submit = challenge.document.querySelector("#recaptcha-verify-button");
            submit.onclick = () => this.submit();

            // Load challenge images
            for (let i = 4; i <= 19; i++) {
                const choice = challenge.document.querySelector(`td[tabindex="${i}"]`);
                const wrapper_image = choice.querySelector("img");
                wrapper_image.src = `data:image/png;base64,${images[0]}`;

                choice.onclick = () => {
                    this.state[i] = !this.state[i];
                    var toggle = this.state[i];
                    choice.classList.toggle("rc-imageselect-tileselected", toggle);
                    if (this.state.filter(x => x === true).length > 0) {
                        submit.innerText = "Verify"
                    } else {
                        submit.innerText = "Skip"
                    }
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
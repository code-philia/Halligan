function init(id) {
    document.addEventListener("DOMContentLoaded", async () => {
        const checkbox_frame = document.querySelector("#checkbox");
        const challenge_node = document.querySelector("#challenge");

        checkbox_frame.onload = () => {
            const checkbox = checkbox_frame.contentWindow;
            const checkbox_box = checkbox.document.querySelector("#checkbox");
            const checkbox_anchor = checkbox.document.querySelector("#anchor");
            const checkbox_spinner = checkbox.document.querySelector(".pulse");
            checkbox_anchor.addEventListener("click", async () => {
                checkbox_box.style.display = "none";
                checkbox_spinner.style.display = "block";

                let response = await fetch(`./challenge/${id}`);
                let data = await response.json();
                if (!response.ok) {
                    console.error(data.message);
                    return
                }

                const subtype = data["subtype"];
                const instruction = data["instruction"];
                const instruction_image = data["instruction_image"];
                const images = data["images"];
                new Captcha(id, challenge_node, subtype, instruction, instruction_image, images);
            })
        }
    })
}

class Captcha {
    /**
     * @param {string} id captcha challenge id
     * @param {Element} parent parent node of captcha challenge
     * @param {string} subtype challenge type
     * @param {string} instruction challenge instruction text
     * @param {string[]} instruction_image challenge instruction image
     * @param {string[]} images challenge image choices
     */
    constructor(id, parent, subtype, instruction, instruction_image, images) {

        const loader = {
            "hcaptcha_type_2": {
                challenge_type: "binary",
                state: this.load_state("binary"),
                frame: this.load_frame("binary", 400, 600),
                load_challenge: this.load_binary
            },
            "hcaptcha_type_3": {
                challenge_type: "binary",
                state: this.load_state("binary"),
                frame: this.load_frame("binary", 400, 600),
                load_challenge: this.load_binary
            },
            "hcaptcha_type_4": {
                challenge_type: "area",
                state: this.load_state("area"),
                frame: this.load_frame("area", 520, 686),
                load_challenge: this.load_area
            },
            "hcaptcha_type_5": {
                challenge_type: "area",
                state: this.load_state("area"),
                frame: this.load_frame("area", 520, 580),
                load_challenge: this.load_area
            }
        }[subtype];

        // Inistialize challenge state
        this.id = id;
        this.state = loader.state;
        this.challenge_type = loader.challenge_type;

        // Initialize challenge frame
        parent.appendChild(loader.frame);

        // Populate frame with instruction and images
        loader.load_challenge(loader.frame, instruction, instruction_image, images);

        console.log(loader.frame.style.height)
        parent.style["width"] = loader.frame.style["width"];
        parent.style["height"] = loader.frame.style["height"];

        // Make frame visible
        const test = document.querySelector("#test");
        test.style["visibility"] = "visible";
        test.style["opacity"] = "1";
    }

    load_state = (type) => {
        return {
            "binary": Array(9).fill(false),
            "area": Array(2).fill(0)
        }[type];
    }

    load_frame = (type, width, height) => {
        const challenge_frame = document.createElement('iframe');
        challenge_frame.src = `./challenge_${type}.html`;
        challenge_frame.frameborder = "0";
        challenge_frame.scrolling = "no";
        challenge_frame.title = "Main content of the hCaptcha challenge";
        challenge_frame.style = `border: 0px; z-index: 2000000000; position: relative; width: ${width}px; height: ${height}px;`;
        return challenge_frame;
    }

    load_binary = (frame, instruction, instruction_image, images) => {
        const challenge = frame.contentWindow;
        challenge.onload = () => {
            // Load text instruction
            const prompt = challenge.document.querySelector(".prompt-text span");
            prompt.innerText = instruction;

            // Load instruction example image
            if (instruction_image.length > 0) {
                const prompt_image_box = challenge.document.querySelector(".challenge-example");
                const prompt_image = prompt_image_box.querySelector(".image .image");
                prompt_image.style["background"] = `url(data:image/png;base64,${instruction_image[0]}) 50% 50% / 120px 120px no-repeat`;
                prompt_image_box.style["display"] = "block";  
            } 

            // Load submit button
            const submit = challenge.document.querySelector(".button-submit");
            const submit_text = submit.querySelector(".text");
            submit.onclick = () => this.submit();

            // Load challenge images
            images.forEach((image, i) => {
                const choice = challenge.document.querySelector(`[aria-label="Challenge Image ${i+1}"]`);
                const wrapper = choice.querySelector(".wrapper");

                const wrapper_image = wrapper.querySelector(".image");
                wrapper_image.style["background"] = `url(data:image/png;base64,${image}) 50% 50% / 120px 120px no-repeat`;

                const badge = wrapper.querySelector(".badge");
                const badge_icon = badge.querySelector(".icon");
                const badge_radial = badge.querySelector(".badge-radial");
                
                choice.onclick = () => {
                    var styles = {
                        [true]: [
                            { transition: "all 0.1s cubic-bezier(0.05, 0.55, 0.5, 0.99) 0s", marginTop: "-50.4px", marginLeft: "-50.4px", width: "100.8px", height: "100.8px",
                              background: `url(data:image/png;base64,${image}) 50% 50% / 100.8px 100.8px no-repeat`
                            },
                            { transition: "all 0.1s cubic-bezier(0.05, 0.55, 0.5, 0.99) 0s", marginTop: "-50.4px", marginLeft: "-50.4px", width: "100.8px", height: "100.8px"},
                            { transition: "all 0.25s cubic-bezier(0.33, 1, 0.68, 1) 0s", opacity: "1" },
                            { transition: "all 0.25s cubic-bezier(0.33, 1, 0.68, 1) 0.05s", opacity: "1" },
                            { transform: "scale(1.5)", opacity: "0" },
                            { backgroundColor: "rgb(0, 131, 143)" }
                        ],
                        [false]: [
                            { transition: "none 0s ease 0s", marginTop: "-60px", marginLeft: "-60px", width: "120px", height: "120px",
                              background: `url(data:image/png;base64,${image}) 50% 50% / 120px 120px no-repeat`
                            },
                            { transition: "none 0s ease 0s", marginTop: "-60px", marginLeft: "-60px", width: "120px", height: "120px" },
                            { transition: "none 0s ease 0s", opacity: "0" },
                            { transition: "none 0s ease 0s", opacity: "0" },
                            { transform: "scale(1)", opacity: "0.5" },
                            { backgroundColor: "rgb(85, 85, 85)" }
                        ]
                    };

                    this.state[i] = !this.state[i];
                    var toggle = this.state[i];
                    var anySelected = this.state.some(selected => selected === true);

                    Object.assign(wrapper_image.style, styles[toggle][0]);
                    Object.assign(wrapper.style, styles[toggle][1]);
                    Object.assign(badge.style, styles[toggle][2]);
                    Object.assign(badge_icon.style, styles[toggle][3]);
                    Object.assign(badge_radial.style, styles[toggle][4]);
                    Object.assign(submit.style, styles[anySelected][5]);

                    submit_text.innerText = (anySelected)? "Verify" : "Skip";
                }
            })
        }
    }

    load_area = (frame, instruction, instruction_image, images) => {
        const challenge = frame.contentWindow;
        challenge.onload = () => {
            // Load text instruction
            const prompt = challenge.document.querySelector(".prompt-text");
            prompt.innerText = instruction;

            // Load instruction example image
            const canvas = challenge.document.querySelector("canvas");
            const prompt_image_box = challenge.document.querySelector(".bounding-box-example");
            const prompt_image = prompt_image_box.querySelectorAll(".example-image");
            instruction_image.forEach((image, i) => {
                prompt_image[i].style["background"] = `url(data:image/png;base64,${image}) 50% 50% / 163.333px 163.333px no-repeat`;
                prompt_image_box.style["display"] = "block";
                prompt_image_box.style["height"] = "106px";
                
                frame.style["height"] = "686px";
                challenge.document.querySelector("body").style["height"] = "686px";
                challenge.document.querySelector(".interface-wrapper").style["height"] = "666px";
                challenge.document.querySelector(".challenge-container").style["height"] = "586px";
                challenge.document.querySelector(".challenge").style["height"] = "586px";
                challenge.document.querySelector(".challenge-view").style["height"] = "586px";
                canvas.style["top"] = "186px";
            })

            // Load submit button
            const submit = challenge.document.querySelector(".button-submit");
            const submit_text = submit.querySelector(".text");
            submit.onclick = () => this.submit();

            // Load challenge images
            const context = canvas.getContext("2d");
            const challenge_image = new Image();
            challenge_image.src = `data:image/png;base64,${images[0]}`;
            challenge_image.onload = () => {
                canvas.style["height"] = 400;
                canvas.height = 400;

                let width, height, marginX, marginY;
                if (challenge_image.height >= challenge_image.width) {
                    marginY = 20;
                    height = canvas.height - marginY * 2;
                    width = challenge_image.width * (height / challenge_image.height);
                    marginX = (canvas.width - width) / 2;
                } else {
                    marginX = 10;
                    width = canvas.width - marginX * 2;
                    height = challenge_image.height * (width / challenge_image.width);
                    marginY = (canvas.height - height) / 2;
                }

                context.fillStyle = "#EBEBEB";
                context.fillRect(0, 0, canvas.width, canvas.height);
                context.drawImage(challenge_image, marginX, marginY, width, height);
                let background = context.getImageData(0, 0, canvas.width, canvas.height);

                canvas.onclick = (event) => {
                    let rect = event.target.getBoundingClientRect();
                    let canvas_x = event.clientX - rect.left;
                    let canvas_y = event.clientY - rect.top;
                    let x = (canvas_x - marginX) / width;
                    let y = (canvas_y - marginY) / height;
  
                    if (x > 0 && x < 1 && y > 0 && y < 1) {
                        context.putImageData(background, 0, 0);
                        this.state[0] = x;
                        this.state[1] = y;
                        context.beginPath();
                        context.arc(canvas_x, canvas_y, 6, 0, 2 * Math.PI, false);
                        context.fillStyle = 'white';
                        context.fill();
                        context.lineWidth = 5;
                        context.strokeStyle = 'black';
                        context.stroke();
                        context.closePath();
                        
                        Object.assign(submit.style, { backgroundColor: "rgb(0, 131, 143)" });
                        submit_text.innerText = "Verify";
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
                state: this.state,
                challenge_type: this.challenge_type 
            })
        }
        let response = await fetch("./submit", config);
        let data = await response.json();
        if (!response.ok) console.error(data.message);
        else console.log(data);
    }
}
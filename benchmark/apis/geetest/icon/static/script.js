function init(id) {
    document.addEventListener("DOMContentLoaded", async () => {
        const challenge_frame = document.querySelector("#geetest_icon");

        challenge_frame.onload = async () => {
            const container = challenge_frame.contentWindow;
            const challenge = container.document.querySelector(".geetest_box");
        
            let response = await fetch(`./challenge/${id}`);
            let data = await response.json();
            if (!response.ok) {
                console.error(data.message);
                return
            }

            const background = challenge.querySelector(".geetest_bg");
            const images = data["images"];
            background.style["backgroundImage"] = `url(data:image/png;base64,${images[0]})`;

            const instruction_images = data["instruction_images"];
            for (var i = 0; i < 3; i++) {
                let instruction = challenge.querySelector(`#geetest_ques_tips_${i+1}`);
                instruction.src = `data:image/png;base64,${instruction_images[i]}`;
            }

            new Captcha(id, container, instruction_images, images);
        }
    })
}

class Captcha {
    /**
     * @param {string} id captcha challenge id
     * @param {string[]} instruction_image challenge instruction image
     * @param {string[]} images challenge image choices
     */
    constructor(id, container, instruction_images, images) {
        this.id = id;
        this.state = []
        this.marks = []
        this.background = container.document.querySelector(".geetest_bg");
        this.window = container.document.querySelector(".geetest_window");
        
        const submit_button = container.document.querySelector(".geetest_submit");
        submit_button.onclick = () => this.submit();

        this.background.onclick = (event) => {
            let rect = event.target.getBoundingClientRect();
            let x = (event.clientX - rect.left) / this.background.offsetWidth;
            let y = (event.clientY - rect.top) / this.background.offsetHeight;
            let index = this.state.length + 1;
            let mark = document.createElement("div");

            mark.classList.add("geetest_square_mark");
            mark.classList.add("geetest_mark_show");
            mark.style["left"] = `${x * 100}%`;
            mark.style["top"] = `${y * 100}%`;
            mark.innerHTML = `<div class='geetest_mark_no'>${index}</div>`;
            mark.onclick = () => {
                for (var i = index - 1; i < this.state.length; i++) this.marks[i].remove();
                this.state.splice(index - 1);
                this.marks.splice(index - 1);
            }

            this.state.push([x, y]);
            this.marks.push(mark);
            this.window.appendChild(mark);
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
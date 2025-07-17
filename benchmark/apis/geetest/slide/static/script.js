function init(id) {
    document.addEventListener("DOMContentLoaded", async () => {
        const challenge_frame = document.querySelector("#geetest_slide");

        challenge_frame.onload = async () => {
            const container = challenge_frame.contentWindow;
            const challenge = container.document.querySelector(".geetest_container");
        
            let response = await fetch(`./challenge/${id}`);
            let data = await response.json();
            if (!response.ok) {
                console.error(data.message);
                return
            }

            const background = challenge.querySelector(".geetest_bg");
            const slice_bg = challenge.querySelector(".geetest_slice_bg");
            const slice = challenge.querySelector(".geetest_slice");
            const instruction_images = data["instruction_image"];
            const images = data["images"];
            const height = data["height"];
            background.style["backgroundImage"] = `url(data:image/png;base64,${instruction_images[0]})`;
            slice_bg.style["backgroundImage"] = `url(data:image/png;base64,${images[0]})`;
            slice.style.top = `${height}px`;

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
        this.track = container.document.querySelector(".geetest_track");
        this.slice = container.document.querySelector(".geetest_slice_bg");
        this.slider = container.document.querySelector(".geetest_btn");
        this.background = container.document.querySelector(".geetest_bg");

        this.id = id;
        this.state = 0;
        this.start_x = 0;
        this.max_distance = this.track.offsetWidth - this.slider.offsetWidth;
        this.is_dragging = false;

        this.slider.onmousedown = this.start_drag;
        this.slider.ontouchstart = this.start_drag;
        document.onmousemove = this.drag;
        document.ontouchmove = this.drag;
        document.onmouseup = this.end_drag;
        document.ontouchend = this.end_drag;
        container.document.onmousemove = this.drag;
        container.document.ontouchmove = this.drag;
        container.document.onmouseup = this.end_drag;
        container.document.ontouchend = this.end_drag;
    }

    start_drag = (event) => {
        this.start_x = event.clientX || event.touches[0].clientX;
        this.is_dragging = true;
    }

    drag = (event) => {
        if (!this.is_dragging) return;
        var current_x = event.clientX || event.touches[0].clientX;
        var distance = current_x - this.start_x

        if (distance < 0 || distance > this.max_distance) distance = Math.min(Math.max(distance, 0), this.max_distance);

        this.state = distance / this.background.offsetWidth;
        this.slider.style["transform"] = `translate(${distance}px, 0px)`;
        this.slice.style["transform"] = `translate(${distance}px, 0px)`;
    }

    end_drag = async (event) => {
        if (!this.is_dragging) return;
        this.is_dragging = false;
        await this.submit();
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
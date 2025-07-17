function init(id) {
    document.addEventListener("DOMContentLoaded", async () => {
        let response = await fetch(`./challenge/${id}`);
        let data = await response.json();
        if (!response.ok) {
            console.error(data.message);
            return
        }

        const instruction_images = data["instruction_image"];
        const background = document.querySelector(".passMod_spin-background");
        background.src = `data:image/png;base64,${instruction_images[0]}`;
        new Captcha(id);
    })
}

class Captcha {
    /**
     * @param {string} id captcha challenge id
     */
    constructor(id) {
        this.track = document.querySelector(".passMod_slide-control");
        this.track_text = document.querySelector(".passMod_slide-tip");
        this.slide = document.querySelector(".passMod_slide-grand");
        this.slider = document.querySelector(".passMod_slide-btn ");
        this.background = document.querySelector(".passMod_spin-background");

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
    }

    start_drag = (event) => {
        this.track_text.style["opacity"] = "0";
        this.start_x = event.clientX || event.touches[0].clientX;
        this.is_dragging = true;
    }

    drag = (event) => {
        if (!this.is_dragging) return;
        var current_x = event.clientX || event.touches[0].clientX;
        var distance = current_x - this.start_x
        if (distance < 0 || distance > this.max_distance) distance = Math.min(Math.max(distance, 0), this.max_distance);
        this.state = distance / this.max_distance * 360;
        this.background.style["transform"] = `rotate(${this.state}deg)`;
        this.slider.style["transform"] = `translate(${distance}px, 0px)`;
        this.slide.style["width"] = `${distance + 45}px`;
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
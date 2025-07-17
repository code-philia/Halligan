function init(id) {
    document.addEventListener("DOMContentLoaded", async () => {
        let response = await fetch(`./challenge/${id}`);
        let data = await response.json();
        if (!response.ok) {
            console.error(data.message);
            return
        }

        image = data["instruction_image"][0];
        swaps = data["swaps"];

        new Captcha(id, image, swaps);
    })
}

class Captcha {
    /**
     * @param {string} id
     * @param {string} image 
     * @param {number[][]} swaps
     */
    constructor(id, image, swaps) {
        this.id = id;
        this.swap_states = this.init_swap_states(swaps);

        // Initialize each tile
        for (let i=0; i < 4; i++) {
            for (let j=0; j < 4; j++) {
                const gridItem = document.querySelector(`#grid-item-${i}-${j}`);
                const rect = gridItem.getBoundingClientRect();
                gridItem.style.backgroundImage = `url(data:image/png;base64,${image})`;
                gridItem.style.backgroundSize = `${rect.width * 4}px ${rect.height * 4}px`;
            }
        }

        // Show background image of each tile
        this.set_swap_state(0);

        this.track = document.querySelector(".CaptchaSlider .Track");
        this.slide = document.querySelector(".CaptchaSlider .Background");
        this.slider = document.querySelector(".CaptchaSlider .Thumb");

        this.index = -1;
        this.drag_x = 0;
        this.start_x = 0;
        this.max_distance = this.track.offsetWidth;
        this.interval = this.max_distance / swaps.length;
        this.is_dragging = false;
        this.slider.onmousedown = this.start_drag;
        this.slider.ontouchstart = this.start_drag;

        document.onmousemove = this.drag;
        document.ontouchmove = this.drag;
        document.onmouseup = this.end_drag;
        document.ontouchend = this.end_drag;
    }

    init_swap_states = (swaps) => {
        let swap_states = [];
        let start_state = [...Array(16).keys()]
        swap_states.push(start_state);

        for (let swap of swaps) {
            let [from, to] = swap;
            let last_state = swap_states[swap_states.length - 1].slice();
            let temp = last_state[to];
            last_state[to] = last_state[from];
            last_state[from] = temp;
            swap_states.push(last_state);
        }
        return swap_states;
    }

    set_swap_state = (index) => {
        let swap_state = this.swap_states[index];

        for (let i=0; i < 4; i++) {
            for (let j=0; j < 4; j++) {
                const gridItem = document.querySelector(`#grid-item-${i}-${j}`);
                const rect = gridItem.getBoundingClientRect();
                let swap_idx = swap_state[i * 4 + j];
                let swap_x = swap_idx % 4;
                let swap_y = Math.floor(swap_idx / 4);
                gridItem.style.backgroundPosition = `-${rect.width * swap_x}px -${rect.height * swap_y}px`;
            }
        }
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
        this.index = Math.floor(distance / this.interval)
        distance = this.index * this.interval; 
        this.set_swap_state(this.index);
        this.slider.style["left"] = `${distance}px`;
        this.slide.style["left"] = `${distance}px`;
    }

    end_drag = async () => {
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
                state: this.index
            })
        }
        let response = await fetch("./submit", config);
        let data = await response.json();
        if (!response.ok) console.error(data.message);
        else console.log(data);
    }
}
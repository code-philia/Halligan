function init(id) {
    document.addEventListener("DOMContentLoaded", async () => {
        const challenge_frame = document.querySelector("#lemin-challenge");

        challenge_frame.onload = async () => {
            const container = challenge_frame.contentWindow;
        
            let response = await fetch(`./challenge/${id}`);
            let data = await response.json();
            if (!response.ok) {
                console.error(data.message);
                return
            }

            const instruction_images = data["instruction_image"];
            const n_holes = data["n_holes"];
            const n_pieces = data["n_pieces"];
            new Captcha(id, container, instruction_images, n_holes, n_pieces);
        }
    })
}

class Captcha {
    /**
     * @param {string} id captcha challenge id
     * @param {string[]} instruction_images
     */
    constructor(id, container, instruction_images, n_holes, n_pieces) {
        const challenge = container.document.querySelector(".captcha-body");
        const background_image = challenge.querySelector("#background-image img");
        background_image.src = `data:image/png;base64,${instruction_images[0]}`;

        const pieces = challenge.querySelector("#pieces");

        for (let i = 0; i < n_pieces; i++) {
            let piece = container.document.createElement("div");
            piece.id = `piece-${i}`;
            piece.style.cssText = `touch-action: none; cursor: move; position: absolute; top: 396.9px; left: ${4.9 + i * 94}px;`;

            let piece_image = container.document.createElement("div");
            piece_image.id = `piece-image-${i}`;
            piece_image.style.cssText = "overflow: hidden; width: 117.6px; height: 117.6px;";

            let image = container.document.createElement("img");
            image.style.cssText = `max-width: none; max-height: none; touch-action: none; width: 1156.4px; height: 392px; margin-top: -4.9px; margin-left: -${396.9 + i * 127.4}px;`;
            image.src = `data:image/png;base64,${instruction_images[0]}`;
            image.width = 1156.4;
            image.height = 392;

            piece_image.appendChild(image);
            piece.appendChild(piece_image);
            piece.onmousedown = this.start_drag;
            piece.ontouchstart = this.start_drag;
            pieces.appendChild(piece);
        }

        this.id = id;
        this.holes = n_holes;
        this.pieces = n_pieces;
        this.state = [];
        this.cell_spacing = 9.8;
        this.drag_pos = [0, 0];
        this.drag_target = null;
        this.grid_bbox = challenge.getBoundingClientRect();
        this.grid_width = this.grid_bbox.width / this.cell_spacing;
        this.grid_height = this.grid_bbox.height / this.cell_spacing;
        this.is_dragging = false;

        container.document.onmousemove = this.drag;
        container.document.ontouchmove = this.drag;
        container.document.onmouseup = this.end_drag;
        container.document.ontouchend = this.end_drag;
    }

    start_drag = (event) => {
        this.is_dragging = true;
        this.drag_target = event.currentTarget;

        event.preventDefault();
    }

    drag = (event) => {
        if (!this.is_dragging) return;
        var offset = 6 * this.cell_spacing;
        var current_x = event.clientX || event.touches[0].clientX;
        var current_y = event.clientY || event.touches[0].clientY;

        var grid_x = Math.round((current_x - this.grid_bbox.left) / this.cell_spacing);
        var grid_y = Math.round((current_y - this.grid_bbox.top) / this.cell_spacing);

        if (grid_x < 0 || grid_x > this.grid_width) grid_x = Math.min(Math.max(grid_x, 0), this.grid_width);
        if (grid_y < 0 || grid_y > this.grid_width) grid_y = Math.min(Math.max(grid_y, 0), this.grid_height);

        this.drag_pos[0] = grid_x;
        this.drag_pos[1] = grid_y;

        this.drag_target.style["left"] = `${grid_x * this.cell_spacing - offset}px`;
        this.drag_target.style["top"] = `${grid_y * this.cell_spacing - offset}px`;

        event.preventDefault();
    }

    end_drag = async (event) => {
        if (!this.is_dragging) return;
        this.is_dragging = false;
        let piece_id = Number(this.drag_target.id.replace("piece-", ""));
        this.state.push([piece_id, ...this.drag_pos]);

        event.preventDefault();

        if (this.state.length == this.holes) await this.submit();
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
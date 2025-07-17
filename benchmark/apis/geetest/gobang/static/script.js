function init(id) {
    document.addEventListener("DOMContentLoaded", async () => {
        const challenge_frame = document.querySelector("#geetest_gobang");

        challenge_frame.onload = async () => {
            const container = challenge_frame.contentWindow;
            const challenge = container.document.querySelector(".geetest_box");
        
            let response = await fetch(`./challenge/${id}`);
            let data = await response.json();
            if (!response.ok) {
                console.error(data.message);
                return
            }

            const grid = data["grid"];
            const images = data["images"];
            new Captcha(id, challenge, grid, images);
        }
    })
}

class Captcha {
    /**
     * @param {string} id
     * @param {Element} challenge
     * @param {number[][]} grid
     * @param {{[key: number]: string}} images
     */
    constructor(id, challenge, grid, images) {
        this.id = id;
        this.grid = grid;
        this.from = null;
        this.to = null;

        for (let i = 0; i < 5; i++) {
            for (let j = 0; j < 5; j++) {
                const image_id = grid[i][j];
                const image = images[image_id];
                const gridItem = challenge.querySelector(`.geetest_item-${i}-${j}`);

                if (image != "") {
                    gridItem.style["backgroundImage"] = `url(data:image/png;base64,${image})`;
                }

                gridItem.onclick = () => {
                    if (this.from && this.from[0] == i && this.from[1] == j) {
                        gridItem.style.border = "";
                        this.from = null;
                    } else if (this.from == null) {
                        gridItem.style.border = "3px solid white";
                        this.from = [i, j];
                    } else if (this.from && this.from[0] >= 0 && this.from[1] >= 0) {
                        this.to = [i, j]
                        this.submit();
                    }
                }
            }
        }
    }

    // Submit challenge
    submit = async () => {
        let [x1, y1] = this.from;
        let [x2, y2] = this.to;        
        let temp = this.grid[x1][y1];
        this.grid[x1][y1] = this.grid[x2][y2];
        this.grid[x2][y2] = temp;

        let config = {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                id: this.id, 
                state: this.grid
            })
        }
        let response = await fetch("./submit", config);
        let data = await response.json();
        if (!response.ok) console.error(data.message);
        else console.log(data);
    }
}
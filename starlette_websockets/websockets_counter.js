document.addEventListener("DOMContentLoaded", () => {
    let websocket = new WebSocket("ws://localhost:8000/counter")
    websocket.onmessage = (event) => {
        const counter = document.getElementById('counter')
        counter.textContent = event.data;
    };
});
// Streamlit component library
const Streamlit = {
    setComponentReady: function() {
        window.parent.postMessage({ type: "streamlit:componentReady", data: {} }, "*");
    },

    setComponentValue: function(value) {
        window.parent.postMessage({ type: "streamlit:setComponentValue", data: value }, "*");
    },

    setFrameHeight: function(height) {
        window.parent.postMessage({ type: "streamlit:setFrameHeight", height: height }, "*");
    },

    componentDidMount: function(callback) {
        window.addEventListener("message", function(event) {
            if (event.data.type === "streamlit:render") {
                callback(event);
            }
        });
    }
};

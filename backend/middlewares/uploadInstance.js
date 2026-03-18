let instance = null;

    module.exports = {
    set: (upload) => { instance = upload; },
    get: () => instance
    };
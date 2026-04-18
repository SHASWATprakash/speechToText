class Processor extends AudioWorkletProcessor {
    process(inputs) {
        const input = inputs[0][0];
        if (!input) return true;

        let volume = 0;
        let buffer = new Int16Array(input.length);

        for (let i = 0; i < input.length; i++) {
            let s = Math.max(-1, Math.min(1, input[i]));
            buffer[i] = s * 32767;
            volume += Math.abs(s);
        }

        volume /= input.length;

        this.port.postMessage({
            buffer: buffer.buffer,
            volume
        });

        return true;
    }
}

registerProcessor("processor", Processor);
import onnx
import onnxruntime as ort
import numpy as np
import soundfile as sf

def save_result(est_source):
    result = []
    for ns in range(2):
        signal = est_source[0, :, ns]
        signal = signal / np.abs(signal).max() * 0.5
        signal = signal[np.newaxis, :]
        # convert numpy array to pcm
        output = (signal * 32768).astype(np.int16).tobytes()
        result.append(output)
        save_file = f'output_spk{ns}.wav'
        sf.write(save_file, np.frombuffer(output, dtype=np.int16), 16000)

onnx_model_path = 'simple_model.onnx'
onnx_model = onnx.load(onnx_model_path)
onnx.checker.check_model(onnx_model)
ort_session = ort.InferenceSession(onnx_model_path)
input_data,sr = sf.read('mix_speech1_16000.wav')
if sr!=16000:raise 'Only supports 16000 Hz'
if input_data.ndim>1:raise 'Only supports 1 channel'
input_data = np.expand_dims(input_data, axis=0).astype(np.float32)
input_name = ort_session.get_inputs()[0].name
outputs = ort_session.run(None, {input_name: input_data})
output_data = outputs[0]
save_result(output_data)
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
import asyncio
import numpy as np
import soundfile as sf
import onnxruntime as ort
import sys
import shutil
from text.uyclean import convert_numbers_in_text


os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

sys.path.append('.')
from text import text_to_sequence
from tts_with_rvc import TTS_RVC

app = FastAPI(title="UY-TTS 在线合成")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
#buinig ga qikilmag 这个是固定的 不要碰  بۇ يەرگە چىقىلمايسىز
TTS_ONNX_PATH = "tts_onnx/model.onnx"

#بۇ بولسا ئايال كىشىنىڭ ئاۋازى
#RVC_MODEL_FILE = "clone_onnx/1.onnx"
#RVC_INDEX_FILE = "clone_onnx/added_IVF1258_Flat_nprobe_1_mi-test_v2.index"
#بۇ بولسا ئەر كىشىنىڭ ئاۋازى
RVC_MODEL_FILE = "clone_onnx\\2.onnx"
RVC_INDEX_FILE = "clone_onnx\\added_2_onnx_v2.index"

RVC_DEVICE = "cpu"
SAMPLING_RATE = 22050
TEMP_DIR = os.path.join(BASE_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)


def tts_synthesize(text, onnx_path, output_wav, sampling_rate=22050):
    try:
        session = ort.InferenceSession(onnx_path)
        text_ids = text_to_sequence(text, ["basic_cleaners"])

        def intersperse(lst, item):
            result = [item] * (len(lst) * 2 + 1)
            result[1::2] = lst
            return result

        text_ids = intersperse(text_ids, 0)
        text_ids = np.array(text_ids, dtype=np.int64).reshape(1, -1)
        text_lengths = np.array([text_ids.shape[1]], dtype=np.int64)

        inputs = {
            'input': text_ids,
            'input_lengths': text_lengths,
            'scales': np.array([0.337, 0.9, 1.0], dtype=np.float32)
        }

        outputs = session.run(None, inputs)
        audio = outputs[0]

        if audio.ndim == 4:
            audio = audio[0, 0, 0, :]
        elif audio.ndim == 3:
            audio = audio[0, 0, :]
        elif audio.ndim == 2:
            audio = audio[0, :]

        audio_int16 = (audio * 32767).astype(np.int16)
        sf.write(output_wav, audio_int16, sampling_rate)
        return True
    except Exception as e:
        print(f"TTS合成失败：{str(e)}")
        return False


def rvc_voice_change(input_audio, output_audio, model_path, index_path, device="cpu",
                     pitch=-6, index_rate=0.5, protect=0.1, rms_mix_rate=0.25):
    try:
        engine = TTS_RVC(
            model_path=model_path,
            index_path=index_path,
            device=device
        )
        output_path = engine.voiceover_file(
            input_path=input_audio,
            pitch=pitch,
            index_rate=index_rate,
            protect=protect,
            rms_mix_rate=rms_mix_rate
        )
        if output_path and os.path.exists(output_path):
            shutil.move(output_path, output_audio)
            return True
        return False
    except Exception as e:
        print(f"RVC变声失败：{str(e)}")
        return False


@app.get("/", response_class=HTMLResponse)
async def home():
    html_path = os.path.join(BASE_DIR, "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/tts")
async def synthesize_speech(text: str = Form(...)):
    if not text.strip():
        raise HTTPException(status_code=400, detail="文本不能为空")

    filename = f"{uuid.uuid4().hex}.wav"
    output_path = os.path.join(TEMP_DIR, filename)
    text = convert_numbers_in_text(text)
    success = await asyncio.to_thread(tts_synthesize, text, TTS_ONNX_PATH, output_path, SAMPLING_RATE)

    if not success:
        raise HTTPException(status_code=500, detail="语音合成失败")

    return {"success": True, "audio_url": f"/audio/{filename}", "filename": filename}


@app.post("/api/voice-change")
async def voice_change(
    file: UploadFile = File(...),
    pitch: int = Form(0),
    index_rate: float = Form(0.5),
    protect: float = Form(0.1),
    rms_mix_rate: float = Form(0.25)
):
    if not file.filename.endswith('.wav'):
        raise HTTPException(status_code=400, detail="仅支持WAV格式音频")

    input_filename = f"{uuid.uuid4().hex}_input.wav"
    output_filename = f"{uuid.uuid4().hex}_voice_changed.wav"
    input_path = os.path.join(TEMP_DIR, input_filename)
    output_path = os.path.join(TEMP_DIR, output_filename)

    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    success = await asyncio.to_thread(
        rvc_voice_change,
        input_path, output_path,
        RVC_MODEL_FILE, RVC_INDEX_FILE,
        RVC_DEVICE, pitch, index_rate, protect, rms_mix_rate
    )

    if os.path.exists(input_path):
        os.remove(input_path)

    if not success:
        raise HTTPException(status_code=500, detail="变声处理失败")

    return {"success": True, "audio_url": f"/audio/{output_filename}", "filename": output_filename}


@app.post("/api/tts-and-voice-change")
async def tts_and_voice_change(
    text: str = Form(None),
    file: UploadFile = File(None),
    pitch: int = Form(0),
    index_rate: float = Form(0.5),
    protect: float = Form(0.1),
    rms_mix_rate: float = Form(0.25)
):
    # 如果有音频文件，则对音频变声；否则对文本合成后变声
    temp_input_path = None
    output_filename = f"{uuid.uuid4().hex}_tts_voice_changed.wav"
    output_path = os.path.join(TEMP_DIR, output_filename)

    try:
        if file and file.filename:
            # 有音频文件：保存后直接变声
            if not file.filename.endswith('.wav'):
                raise HTTPException(status_code=400, detail="仅支持WAV格式音频")
            
            temp_input_path = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}_input.wav")
            with open(temp_input_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            input_path = temp_input_path
        elif text:
            # 无音频：先TTS合成
            text = convert_numbers_in_text(text)
            temp_input_path = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}_tts.wav")
            success = await asyncio.to_thread(
                tts_synthesize, text, TTS_ONNX_PATH, temp_input_path, SAMPLING_RATE
            )
            if not success:
                raise HTTPException(status_code=500, detail="语音合成失败")
            input_path = temp_input_path
        else:
            raise HTTPException(status_code=400, detail="请提供文本或音频文件")

        # 执行变声
        success = await asyncio.to_thread(
            rvc_voice_change,
            input_path, output_path,
            RVC_MODEL_FILE, RVC_INDEX_FILE,
            RVC_DEVICE, pitch, index_rate, protect, rms_mix_rate
        )

        if not success:
            raise HTTPException(status_code=500, detail="变声处理失败")

        return {"success": True, "audio_url": f"/audio/{output_filename}", "filename": output_filename}
    finally:
        # 清理临时输入文件
        if temp_input_path and os.path.exists(temp_input_path):
            os.remove(temp_input_path)


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    file_path = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="音频文件不存在")
    return FileResponse(file_path, media_type="audio/wav")


@app.delete("/audio/{filename}")
async def delete_audio(filename: str):
    file_path = os.path.join(TEMP_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return {"success": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

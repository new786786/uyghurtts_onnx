from fastapi import FastAPI, HTTPException, Form, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
import asyncio
import json
import io
import re
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
#from tts_with_rvc import TTS_RVC

app = FastAPI(title="UY-TTS ئاقما ئاۋاز بىرىكتۈرۈش")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# ======================== 模型路径 ========================
TTS_ONNX_PATH = os.path.join(BASE_DIR, "tts_onnx", "xjsdn.onnx")
RVC_MODEL_FILE = os.path.join(BASE_DIR, "clone_onnx", "2.onnx")
RVC_INDEX_FILE = os.path.join(BASE_DIR, "clone_onnx", "added_2_onnx_v2.index")
RVC_DEVICE = "cpu"
SAMPLING_RATE = 24000
TEMP_DIR = os.path.join(BASE_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# ======================== 启动时加载模型（只加载一次） ========================
print("正在加载 TTS ONNX 模型...")
tts_session = ort.InferenceSession(TTS_ONNX_PATH)
print("TTS 模型加载完成")

# ======================== 默认标点停顿配置(ms) ========================
DEFAULT_PAUSES = {
    "،": 350, ",": 350,
    "؛": 450, ";": 450,
    "؟": 550, "?": 550,
    "!": 550,
    ".": 550,
    ":": 300, "：": 300,
    "…": 600,
    "\n": 500,
}


# ======================== 工具函数 ========================

def intersperse(lst, item):
    result = [item] * (len(lst) * 2 + 1)
    result[1::2] = lst
    return result


def tts_synthesize_audio(text):
    """合成文本为 numpy int16 音频数组（使用全局 session）"""
    text_ids = text_to_sequence(text, ["basic_cleaners"])
    text_ids = intersperse(text_ids, 0)
    text_ids_np = np.array(text_ids, dtype=np.int64).reshape(1, -1)
    text_lengths = np.array([text_ids_np.shape[1]], dtype=np.int64)

    inputs = {
        "input": text_ids_np,
        "input_lengths": text_lengths,
        #"scales": np.array([0.337, 0.9, 1.0], dtype=np.float32),
        "scales": np.array([0.667, 1.0, 0.8], dtype=np.float32),
    }

    outputs = tts_session.run(None, inputs)
    audio = outputs[0]

    if audio.ndim == 4:
        audio = audio[0, 0, 0, :]
    elif audio.ndim == 3:
        audio = audio[0, 0, :]
    elif audio.ndim == 2:
        audio = audio[0, :]

    return (audio * 32767).astype(np.int16)


def tts_synthesize_to_file(text, output_wav):
    """合成文本并保存为 WAV 文件"""
    try:
        text = convert_numbers_in_text(text)
        audio = tts_synthesize_audio(text)
        sf.write(output_wav, audio, SAMPLING_RATE)
        return True
    except Exception as e:
        print(f"TTS合成失败：{e}")
        return False


def generate_silence(duration_ms):
    """生成指定时长的静音"""
    n = int(duration_ms / 1000.0 * SAMPLING_RATE)
    return np.zeros(n, dtype=np.int16)


def audio_to_wav_bytes(audio_int16):
    """numpy 音频转 WAV 字节"""
    buf = io.BytesIO()
    sf.write(buf, audio_int16, SAMPLING_RATE, format="WAV", subtype="PCM_16")
    buf.seek(0)
    return buf.read()


def split_text_with_pauses(text, pause_config):
    """
    按标点符号分段，返回 [(段落文本, 停顿毫秒), ...]
    保留标点在段落末尾，用于正确合成语调
    """
    punct_set = set(pause_config.keys()) - {"\n"}
    segments = []
    current_chars = []

    for ch in text:
        if ch == "\n":
            seg = "".join(current_chars).strip()
            if seg:
                segments.append((seg, pause_config.get("\n", 500)))
            current_chars = []
        elif ch in punct_set:
            current_chars.append(ch)
            seg = "".join(current_chars).strip()
            if seg:
                segments.append((seg, pause_config.get(ch, 300)))
            current_chars = []
        else:
            current_chars.append(ch)

    remaining = "".join(current_chars).strip()
    if remaining:
        segments.append((remaining, 0))

    return segments


def rvc_voice_change(input_audio, output_audio, pitch=-6, index_rate=0.5, protect=0.1, rms_mix_rate=0.25):
    """RVC 变声"""
    try:
        engine = TTS_RVC(model_path=RVC_MODEL_FILE, index_path=RVC_INDEX_FILE, device=RVC_DEVICE)
        output_path = engine.voiceover_file(
            input_path=input_audio, pitch=pitch,
            index_rate=index_rate, protect=protect, rms_mix_rate=rms_mix_rate,
        )
        if output_path and os.path.exists(output_path):
            shutil.move(output_path, output_audio)
            return True
        return False
    except Exception as e:
        print(f"RVC变声失败：{e}")
        return False


# ======================== 页面路由 ========================

@app.get("/", response_class=HTMLResponse)
async def home():
    html_path = os.path.join(BASE_DIR, "templates", "new.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


# ======================== REST API ========================

@app.post("/api/tts")
async def api_tts(text: str = Form(...)):
    if not text.strip():
        raise HTTPException(status_code=400, detail="文本不能为空")

    filename = f"{uuid.uuid4().hex}.wav"
    output_path = os.path.join(TEMP_DIR, filename)
    success = await asyncio.to_thread(tts_synthesize_to_file, text, output_path)

    if not success:
        raise HTTPException(status_code=500, detail="语音合成失败")
    return {"success": True, "audio_url": f"/audio/{filename}", "filename": filename}


@app.post("/api/tts-long")
async def api_tts_long(
    text: str = Form(...),
    pauses: str = Form(None),
):
    """长文本合成：分段合成 + 自定义标点停顿，返回完整 WAV"""
    if not text.strip():
        raise HTTPException(status_code=400, detail="文本不能为空")

    pause_config = dict(DEFAULT_PAUSES)
    if pauses:
        try:
            user_pauses = json.loads(pauses)
            pause_config.update({k: int(v) for k, v in user_pauses.items()})
        except Exception:
            pass

    text = convert_numbers_in_text(text)
    segments = split_text_with_pauses(text, pause_config)

    if not segments:
        raise HTTPException(status_code=400, detail="无有效文本段")

    def synthesize_all():
        all_audio = []
        for seg_text, pause_ms in segments:
            try:
                audio = tts_synthesize_audio(seg_text)
                all_audio.append(audio)
                if pause_ms > 0:
                    all_audio.append(generate_silence(pause_ms))
            except Exception as e:
                print(f"段落合成失败: {seg_text[:30]}... -> {e}")
                continue
        if not all_audio:
            return None
        combined = np.concatenate(all_audio)
        filename = f"{uuid.uuid4().hex}.wav"
        path = os.path.join(TEMP_DIR, filename)
        sf.write(path, combined, SAMPLING_RATE)
        return filename

    filename = await asyncio.to_thread(synthesize_all)
    if not filename:
        raise HTTPException(status_code=500, detail="合成失败")

    return {"success": True, "audio_url": f"/audio/{filename}", "filename": filename}


@app.post("/api/voice-change")
async def api_voice_change(
    file: UploadFile = File(...),
    pitch: int = Form(0),
    index_rate: float = Form(0.5),
    protect: float = Form(0.1),
    rms_mix_rate: float = Form(0.25),
):
    if not file.filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="仅支持WAV格式")

    input_fn = f"{uuid.uuid4().hex}_input.wav"
    output_fn = f"{uuid.uuid4().hex}_vc.wav"
    input_path = os.path.join(TEMP_DIR, input_fn)
    output_path = os.path.join(TEMP_DIR, output_fn)

    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    success = await asyncio.to_thread(rvc_voice_change, input_path, output_path, pitch, index_rate, protect, rms_mix_rate)

    if os.path.exists(input_path):
        os.remove(input_path)

    if not success:
        raise HTTPException(status_code=500, detail="变声处理失败")
    return {"success": True, "audio_url": f"/audio/{output_fn}", "filename": output_fn}


@app.post("/api/tts-and-voice-change")
async def api_tts_and_vc(
    text: str = Form(None),
    file: UploadFile = File(None),
    pitch: int = Form(0),
    index_rate: float = Form(0.5),
    protect: float = Form(0.1),
    rms_mix_rate: float = Form(0.25),
):
    temp_input = None
    output_fn = f"{uuid.uuid4().hex}_tts_vc.wav"
    output_path = os.path.join(TEMP_DIR, output_fn)

    try:
        if file and file.filename:
            if not file.filename.endswith(".wav"):
                raise HTTPException(status_code=400, detail="仅支持WAV格式")
            temp_input = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}_in.wav")
            with open(temp_input, "wb") as f:
                shutil.copyfileobj(file.file, f)
        elif text:
            temp_input = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}_tts.wav")
            success = await asyncio.to_thread(tts_synthesize_to_file, text, temp_input)
            if not success:
                raise HTTPException(status_code=500, detail="语音合成失败")
        else:
            raise HTTPException(status_code=400, detail="请提供文本或音频")

        success = await asyncio.to_thread(rvc_voice_change, temp_input, output_path, pitch, index_rate, protect, rms_mix_rate)
        if not success:
            raise HTTPException(status_code=500, detail="变声失败")

        return {"success": True, "audio_url": f"/audio/{output_fn}", "filename": output_fn}
    finally:
        if temp_input and os.path.exists(temp_input):
            os.remove(temp_input)


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    file_path = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path, media_type="audio/wav")


@app.delete("/audio/{filename}")
async def delete_audio(filename: str):
    file_path = os.path.join(TEMP_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return {"success": True}


# ======================== WebSocket 流式合成 ========================

@app.websocket("/ws/tts-stream")
async def ws_tts_stream(websocket: WebSocket):
    """
    WebSocket 流式 TTS：
    1. 客户端发送 JSON: { text, pauses: {...} }
    2. 服务端逐段合成，每完成一段立即发送:
       - JSON {"type":"start", "total": N}
       - JSON {"type":"progress", "index": i, "total": N, "text": "..."}
       - Binary WAV 数据
       - ...重复...
       - JSON {"type":"done"}
    3. 客户端收到 Binary 即可解码播放，实现边合成边播放
    """
    await websocket.accept()
    try:
        raw = await websocket.receive_text()
        config = json.loads(raw)

        text = config.get("text", "").strip()
        if not text:
            await websocket.send_json({"type": "error", "message": "تېكىسىت كىرگۈزۈڭ"})
            await websocket.close()
            return

        user_pauses = config.get("pauses", {})
        pause_config = dict(DEFAULT_PAUSES)
        if user_pauses:
            pause_config.update({k: int(v) for k, v in user_pauses.items()})

        text = convert_numbers_in_text(text)
        segments = split_text_with_pauses(text, pause_config)

        if not segments:
            await websocket.send_json({"type": "error", "message": "بۆلۈنىدىغان تېكىسىت يوق"})
            await websocket.close()
            return

        total = len(segments)
        await websocket.send_json({"type": "start", "total": total})

        for i, (seg_text, pause_ms) in enumerate(segments):
            await websocket.send_json({
                "type": "progress",
                "index": i,
                "total": total,
                "text": seg_text,
            })

            try:
                audio = await asyncio.to_thread(tts_synthesize_audio, seg_text)
            except Exception as e:
                await websocket.send_json({"type": "segment_error", "index": i, "message": str(e)})
                continue

            if pause_ms > 0:
                silence = generate_silence(pause_ms)
                audio = np.concatenate([audio, silence])

            wav_bytes = await asyncio.to_thread(audio_to_wav_bytes, audio)
            await websocket.send_bytes(wav_bytes)

        await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        pass
    except json.JSONDecodeError:
        try:
            await websocket.send_json({"type": "error", "message": "JSON 格式错误"})
        except Exception:
            pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


# ======================== 启动 ========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)

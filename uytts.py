import numpy as np
import onnxruntime as ort
import soundfile as sf
import json
import os
import sys
from scipy.signal import resample
from tts_with_rvc import TTS_RVC

# ===================== 全局配置 =====================
# 1. TTS合成配置
TTS_ONNX_PATH = "tts_onnx\\model.onnx"  # TTS模型路径
SAMPLING_RATE = 22050  # TTS采样率
TEXT = """
بۈگۈن، شىمالىي شىنجاڭنىڭ كۆپ قىسىم جايلىرى ۋە جەنۇبىي شىنجاڭنىڭ غەربىدىكى تاغلىق رايونلار، خوتەن ۋىلايىتىنىڭ جەنۇبىدىكى تاغلىق رايونلار، ئاقسۇ ۋىلايىتىنىڭ غەربىدىكى شىمالىي تاغلىق رايونلار، قومۇل شەھىرىنىڭ شىمالى قاتارلىق جايلارنىڭ قىسمەن رايونلىرىدا ئازراق يامغۇر ياغىدۇ. تاغلىق رايوندىكى قىسمەن رايونلاردا ئوتتۇراھال يامغۇر ياكى قار ياغىدۇ.
بۈگۈن كۈندۈزى ئۈرۈمچى شەھىرىنىڭ كۆپ قىسىم رايونلىرىدا ئوتتۇراھال يامغۇر يېغىپ بۇلۇتلۇق بولىدۇ، جەنۇبىي شەھەر ئەتراپى ۋە تاغلىق رايونلاردا ئوتتۇراھال ۋە قاتتىق يامغۇر ياغىدۇ. يامغۇردىن كېيىن، ھاۋا ئوچۇق بولىدۇ.
"""
TEMP_WAV = "temp_tts_output.wav"  # TTS临时输出文件
FINAL_OUTPUT_WAV = "final_voice_changed.wav"  # 最终变声输出文件

# 2. RVC变声配置
RVC_MODEL_FILE = "clone_onnx\\2\\best_kelong.onnx"  # RVC模型路径
RVC_INDEX_FILE = "clone_onnx\\2\\added_IVF1076_Flat_nprobe_1_kelong202655_v2.index"  # RVC索引文件（无则留空）
RVC_DEVICE = "cpu"  # 有NVIDIA显卡改为"cuda:0"
# RVC参数
RVC_PITCH = -12  # 音高调整（0不变，正数升高，负数降低）
RVC_INDEX_RATE = 0.35  # 音色相似度（0.3-0.9）
RVC_PROTECT = 0.1  # 清辅音保护（0.3-0.5）
RVC_RMS_MIX_RATE = 0.25  # 音量包络混合率

# ===================== 环境配置 ====================
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"


# ===================== TTS语音合成函数 =====================
def tts_synthesize(text, onnx_path, output_wav, sampling_rate=22050):
    """
    基于ONNX的TTS语音合成
    :param text: 待合成文本
    :param onnx_path: TTS模型路径
    :param output_wav: 合成音频输出路径
    :param sampling_rate: 采样率
    :return: 合成成功返回True，失败返回False
    """
    try:
        # 导入文本处理函数
        sys.path.append('.')
        from text import text_to_sequence

        # 初始化ONNX会话
        session = ort.InferenceSession(onnx_path)

        # 文本转序列
        text_ids = text_to_sequence(text, ["basic_cleaners"])

        # 添加空白符（提升合成效果）
        def intersperse(lst, item):
            result = [item] * (len(lst) * 2 + 1)
            result[1::2] = lst
            return result

        text_ids = intersperse(text_ids, 0)

        # 整理输入数据格式
        text_ids = np.array(text_ids, dtype=np.int64).reshape(1, -1)
        text_lengths = np.array([text_ids.shape[1]], dtype=np.int64)

        # 准备输入字典
        inputs = {
            'input': text_ids,
            'input_lengths': text_lengths,
            'scales': np.array([0.337, 0.9, 1.0], dtype=np.float32)  # noise_scale, noise_scale_w, length_scale
        }

        # 执行推理
        print("正在进行语音合成...")
        outputs = session.run(None, inputs)
        audio = outputs[0]

        # 调整音频形状
        if audio.ndim == 4:
            audio = audio[0, 0, 0, :]
        elif audio.ndim == 3:
            audio = audio[0, 0, :]
        elif audio.ndim == 2:
            audio = audio[0, :]

        # 音频归一化并保存
        print(f"TTS合成音频范围: min={audio.min():.6f}, max={audio.max():.6f}")
        if audio.dtype in [np.float32, np.float64]:
            audio_int16 = (audio * 32767).astype(np.int16)
            sf.write(output_wav, audio_int16, sampling_rate)
            print(f"TTS合成完成，临时文件保存至: {output_wav}")
            return True
        else:
            print("错误：音频数据类型不支持")
            return False
    except Exception as e:
        print(f"TTS合成失败：{str(e)}")
        return False


# ===================== RVC变声函数 =====================
def rvc_voice_change(input_audio, output_audio, model_path, index_path, device="cpu",
                     pitch=6, index_rate=0.9, protect=0.5, rms_mix_rate=0.25):
    """
    RVC变声处理
    :param input_audio: 输入音频路径
    :param output_audio: 输出音频路径
    :param model_path: RVC模型路径
    :param index_path: RVC索引文件路径
    :param device: 运行设备（cpu/cuda:0）
    :param pitch: 音高调整
    :param index_rate: 音色相似度
    :param protect: 清辅音保护
    :param rms_mix_rate: 音量包络混合率
    :return: 变声成功返回输出路径，失败返回None
    """
    try:
        # 初始化RVC引擎
        print("初始化克隆引擎...")
        engine = TTS_RVC(
            model_path=model_path,
            index_path=index_path,
            device=device
        )

        # 执行变声
        print("正在进行变声处理...")
        output_path = engine.voiceover_file(
            input_path=input_audio,
            pitch=pitch,
            index_rate=index_rate,
            protect=protect,
            rms_mix_rate=rms_mix_rate
        )

        # 重命名为指定的最终输出文件（可选，也可直接使用engine返回的路径）
        if output_path and os.path.exists(output_path):
            os.rename(output_path, output_audio)
            print(f"变声完成，最终文件保存至: {output_audio}")
            return output_audio
        else:
            print("RVC变声失败：未生成输出文件")
            return None
    except Exception as e:
        print(f"变声失败：{str(e)}")
        return None


# ===================== 主流程 =====================
if __name__ == "__main__":
    # 步骤1：TTS合成语音
    tts_success = tts_synthesize(TEXT, TTS_ONNX_PATH, TEMP_WAV, SAMPLING_RATE)
    if not tts_success:
        sys.exit("程序终止：TTS语音合成失败")

    # 步骤2：RVC变声处理
    final_output = rvc_voice_change(
        input_audio=TEMP_WAV,
        output_audio=FINAL_OUTPUT_WAV,
        model_path=RVC_MODEL_FILE,
        index_path=RVC_INDEX_FILE,
        device=RVC_DEVICE,
        pitch=RVC_PITCH,
        index_rate=RVC_INDEX_RATE,
        protect=RVC_PROTECT,
        rms_mix_rate=RVC_RMS_MIX_RATE
    )

    # 步骤3：清理临时文件（可选）
    if os.path.exists(TEMP_WAV):
        os.remove(TEMP_WAV)
        print(f"已清理临时文件：{TEMP_WAV}")

    # 最终结果提示
    if final_output:
        print(f"\n✅ 全部流程完成！最终音频文件：{final_output}")
    else:
        print("\n❌ 流程失败：变声未完成")
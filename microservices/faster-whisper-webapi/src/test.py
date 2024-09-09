import whisper

print("modelをロードします")
model = whisper.load_model("large-v2")
print("ロードしました")

result = model.transcribe("../input/soramo_toberuhazu(vocal).wav", verbose=True, language="ja")

print(result)
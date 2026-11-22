from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("gpt2")
samples = {
    "en": "I like to eat an apple every morning.",
    "ko": "나는 매일 아침 사과를 먹는 것을 좋아해요.",
    "code": "for i in range(10): print(i)",
}

for name, text in samples.items():
    ids = tok(text)["input_ids"]
    pieces = tok.convert_ids_to_tokens(ids)
    back = tok.decode(ids)
    print(f"[{name}] 글자 수={len(text)}, 토큰 수={len(ids)}")
    print("  조각:", pieces)
    print("  왕복 일치:", back == text)

print("vocab_size:", tok.vocab_size)
print("eos_token:", tok.eos_token)
print("pad_token:", tok.pad_token)

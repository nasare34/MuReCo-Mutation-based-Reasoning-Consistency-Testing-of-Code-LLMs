"""Model backends.

* HFModel: any HuggingFace chat model, greedy decoding, batched (Colab GPU).
* OpenAICompatModel: any OpenAI-compatible endpoint (OpenAI, vLLM, Ollama...).
* OracleModel / CorruptingOracle: *test doubles only*, used to validate the
  pipeline (a perfect model must yield 0% inconsistency; injected errors must
  be detected). They are never reported as model results.
"""
import random


class HFModel:
    def __init__(self, name, max_new_tokens=512, batch_size=8, dtype="auto", load_in_4bit=False):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.name = name
        self.max_new_tokens = max_new_tokens
        self.batch_size = batch_size
        self.tok = AutoTokenizer.from_pretrained(name, padding_side="left")
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        kw = {"device_map": "auto"}
        if load_in_4bit:
            from transformers import BitsAndBytesConfig
            kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16)
        else:
            kw["torch_dtype"] = torch.float16 if dtype == "auto" else getattr(torch, dtype)
        self.model = AutoModelForCausalLM.from_pretrained(name, **kw).eval()
        self.torch = torch

    def _chat(self, prompt):
        return self.tok.apply_chat_template([{"role": "user", "content": prompt}],
                                            tokenize=False, add_generation_prompt=True)

    def generate(self, prompts):
        outs = []
        for i in range(0, len(prompts), self.batch_size):
            chunk = [self._chat(p) for p in prompts[i:i + self.batch_size]]
            enc = self.tok(chunk, return_tensors="pt", padding=True, add_special_tokens=False).to(self.model.device)
            with self.torch.no_grad():
                gen = self.model.generate(**enc, max_new_tokens=self.max_new_tokens, do_sample=False,
                                          temperature=None, top_p=None, top_k=None,
                                          pad_token_id=self.tok.pad_token_id)
            for row in gen[:, enc["input_ids"].shape[1]:]:
                outs.append(self.tok.decode(row, skip_special_tokens=True))
        return outs


class OpenAICompatModel:
    def __init__(self, name, base_url=None, api_key=None, max_new_tokens=512):
        from openai import OpenAI
        self.name = name
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.max_new_tokens = max_new_tokens

    def generate(self, prompts):
        outs = []
        for p in prompts:
            r = self.client.chat.completions.create(model=self.name, temperature=0,
                                                    max_tokens=self.max_new_tokens,
                                                    messages=[{"role": "user", "content": p}])
            outs.append(r.choices[0].message.content or "")
        return outs


class OracleModel:
    """Test double: answers every MuReCo prompt with the ground truth."""
    name = "oracle (test double)"

    def __init__(self, answers):
        self.answers = answers          # prompt -> ground-truth answer text

    def generate(self, prompts):
        return [self.answers[p] for p in prompts]


class CorruptingOracle(OracleModel):
    """Test double: ground truth, but corrupts one trace value with
    probability p on mutated variants (output left correct), so we can
    check that MuReCo detects 'right answer, wrong reasoning'."""
    name = "corrupting oracle (test double)"

    def __init__(self, answers, corrupt, p=0.3, seed=0):
        super().__init__(answers)
        self.corrupt = corrupt          # prompt -> corrupted answer text
        self.p = p
        self.rng = random.Random(seed)

    def generate(self, prompts):
        return [self.corrupt[p] if p in self.corrupt and self.rng.random() < self.p else self.answers[p]
                for p in prompts]

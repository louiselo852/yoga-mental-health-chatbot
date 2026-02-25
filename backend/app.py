from peft import PeftModel
from fastapi import FastAPI, Request
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

app = FastAPI()

tokenizer = AutoTokenizer.from_pretrained("../tinyllama/tokenizer_folder", 
local_files_only=True)
base_model = AutoModelForCausalLM.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
model = PeftModel.from_pretrained(base_model, "../tinyllama/final_model", 
local_files_only=True)
class Query(BaseModel):
    question: str

@app.post("/generate")
async def generate_text(query: Query):
    inputs = tokenizer(f"### Question:\n{query.question}\n\n### Answer:", return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=150, temperature=0.7, top_p=0.95, do_sample=True, pad_token_id=tokenizer.eos_token_id)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return {"answer": response}

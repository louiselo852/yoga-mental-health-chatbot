from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel, PeftConfig
import torch
import time
import logging

logging.basicConfig(level=logging.INFO)

# Load PEFT config to find base model path
peft_path = "/Users/sapan/Desktop/Mental Health LLM/tinyllama/final_model"
peft_config = PeftConfig.from_pretrained(peft_path)

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    peft_config.base_model_name_or_path,
    torch_dtype=torch.float32  # Change to torch.float16 if CUDA available and you want
)

# Load adapter on base model
model = PeftModel.from_pretrained(base_model, peft_path)
model.eval()

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(peft_config.base_model_name_or_path)

# Initialize FastAPI app
app = FastAPI()

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Restrict to your frontend origin for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for request validation
class QuestionRequest(BaseModel):
    question: str

@app.post("/chat")
async def ask_question(req: QuestionRequest):
    logging.info(f"Received question: {req.question}")
    start_time = time.time()

    input_text = req.question
    inputs = tokenizer(input_text, return_tensors="pt")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=100)

    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)

    elapsed = time.time() - start_time
    logging.info(f"Generated answer in {elapsed:.2f} seconds")

    return {"answer": answer}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=5100, reload=True)

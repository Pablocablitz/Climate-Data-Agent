import transformers
import torch
import json
from utils.utils import Utilities

class LargeLanguageModelProcessor():
    def __init__(self):
        self.llm = "meta-llama/Meta-Llama-3-8B-Instruct"
        self.pipeline = transformers.pipeline(
            "text-generation",
            model=self.llm,
            device=0 if torch.cuda.is_available() else -1,  # Use GPU if available
            model_kwargs={"torch_dtype": torch.float16 if torch.cuda.is_available() else torch.bfloat16},
        )
    def generate_response(self, system_prompt):
        """
        get Response on your input prompt and system prompt
        """

        messages = [
            {"role": "system", "content": system_prompt},
        ]
        # Generate the response
        outputs = self.pipeline(
        messages,
        max_new_tokens = 4000,
        do_sample = True,
        temperature = 0.5,
        top_p=0.95,
        )

        # Extract the generated text
        response = outputs[0]["generated_text"][-1]
        text_response = response["content"]
        
        return text_response


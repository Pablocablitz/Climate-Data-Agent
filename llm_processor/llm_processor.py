import transformers
import torch
import json

class LargeLanguageModelProcessor():
    def __init__(self):
        self.llm = "meta-llama/Meta-Llama-3-8B-Instruct"
        self.pipeline = transformers.pipeline(
            "text-generation",
            model=self.llm,
            device=0 if torch.cuda.is_available() else -1,  # Use GPU if available
            model_kwargs={"torch_dtype": torch.float16 if torch.cuda.is_available() else torch.bfloat16},
        )
    def generate_response(self, system_prompt, user_message):
        """
        get Response on your input prompt and system prompt
        """
        llm_input = system_prompt.format(prompt = user_message)
        # print(system_prompt)
        messages = [
            {"role": "system", "content": llm_input},
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
        
        return self.cleaned_dict_output(text_response)

    def cleaned_dict_output(response):
        """
        Cleans a JSON string by removing any content before the first `{` and after the last `}`.

        Args:
        response (str): The raw JSON response string.

        Returns:
        dict: A dictionary parsed from the cleaned JSON string.
        """
        # Find the first '{' and last '}'
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            print("No JSON object found in the response.")
            return None
        
        # Extract the JSON string
        json_str = response[start_idx:end_idx + 1]
        
        # Replace single quotes with double quotes for valid JSON
        json_str = json_str.replace("'", '"')
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return None
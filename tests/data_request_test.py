import yaml



def load_config_file(file_path: str) -> dict:
    """
    Load YAML file.

    Args:
        file_path (str): Path to the YAML file.

    Returns:
        dict: Dictionary containing configuration information.
    """
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def load_request_format():
    request_format = load_config_file("/home/eouser/programming/Climate-Data-Agent/data_handler/request_format.yaml")
    return request_format
    
# request_format = load_request_format()

def load_variables():
    variables = load_config_file("yaml/variables.yaml") 
    return variables

variables = load_variables()
product = ["Temperature"]
# print(request_format)

def construct_product_agent_instruction(variables):
    product_list = [product['name'] for product in variables.get(product[0], [])]
    print(product_list)
    instruction_format = f"'{product}':\n- {product_list}"
    return instruction_format

instruction = construct_product_agent_instruction(variables)
print(instruction)
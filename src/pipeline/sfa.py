from primitive.sanitizer import *
from parser.response_parser import *
import json



class SFAPipeline:
    def __init__(self,
                 project_name,
                 all_c_files,
                 inference_model_name,
                 inference_key_str):
        self.project_name = project_name
        self.all_c_files = all_c_files
        self.inference_model_name = inference_model_name
        self.inference_key_str = inference_key_str
        self.detection_result = []
        self.buggy_traces = []
        self.ts_analyzer = TSAnalyzer(self.all_c_files)
        pass
    

    def start_detection(self):
        return
        print("-----------------------------------------------------------")
        print("Start analyzing", self.project_name)
        print("-----------------------------------------------------------")

        log_dir_path = str(
            Path(__file__).resolve().parent.parent
            / ("log/sfa/" + self.project_name)
        )
        if not os.path.exists(log_dir_path):
            os.makedirs(log_dir_path)

        # Load the source code from the Java file
        detection_scopes = self.extract_detection_sfa_scopes()
        return
    
    
    def extract_detection_sfa_scopes(self):
        print("Start extracting detection scopes")
        target_function_ids = {}
        for function_id in self.ts_analyzer.ts_parser.functionRawDataDic:
            function_root_node = self.ts_analyzer.environment[function_id].parse_tree.root_node
            function_code = self.ts_analyzer.environment[function_id].function_code
            all_call_sites = self.ts_analyzer.find_nodes_by_type(function_root_node, "call_expression")
            is_target = False
            for call_site in all_call_sites:
                if function_code[call_site.start_byte:call_site.end_byte].find("BN_secure_new") != -1:
                    is_target = True
                if function_code[call_site.start_byte:call_site.end_byte].find("BN_free") != -1:
                    is_target = False
            if is_target:
                target_function_ids[function_id] = self.ts_analyzer.environment[function_id].function_name
        print("Finish extracting detection scopes")
        return target_function_ids
    
    
    def start_run_sfa_check(self, function_code: str):
        prompt = """
        Task: If a function BN_secure_new() is called, i.e., `p = BN_secure_new();`, then we have invoke BN_free(p) after the last use of p. 
        Otherwise, please report a resource leak bug.
        Please check the function body. If it violate the above rule, please report it as a resource bug.
        Here is the function:
        {function_code}
        Please think step by step and give the answer in the following format:
        Answer: [Your explanation]
        Yes/No.
        Specifically, the second line should contain Yes if there is a bug. Otherwise, it should contain No.
        """
        response, input_token_cost, output_token_cost = self.model.infer(prompt.replace("{function_code}", function_code), False)
        print(response)
        return response

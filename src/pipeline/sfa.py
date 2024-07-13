from analyzer.sanitizer import *
from parser.response_parser import *
from model.detector import *
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

        self.all_c_obfuscated_files = {}

        for c_file_path in self.all_c_files:
            # self.all_c_obfuscated_files[c_file_path] = obfuscate(self.all_c_files[c_file_path])
            self.all_c_obfuscated_files[c_file_path] = self.all_c_files[c_file_path]
        self.ts_analyzer = TSAnalyzer(self.all_c_obfuscated_files)
        pass
    

    def start_detection(self):
        print("-----------------------------------------------------------")
        print("Start analyzing", self.project_name)
        print("-----------------------------------------------------------")

        log_dir_path = str(
            Path(__file__).resolve().parent.parent
            / ("log/initial_detection/" + self.inference_model_name + "/" + self.project_name)
        )
        if not os.path.exists(log_dir_path):
            os.makedirs(log_dir_path)

        # Load the source code from the Java file
        single_detector = Detector(self.ts_analyzer, self.inference_model_name, self.inference_key_str, None)
        detection_scopes = single_detector.extract_detection_sfa_scopes()
        
        with open(log_dir_path + "/analysis_result.json", "w") as f:
            json.dump(detection_scopes, f, indent=4)
        
        # analysis_result = {}
        # for function_id in detection_scopes:
        #     print(single_detector.ts_analyzer.environment[function_id].function_name)
        #     response = single_detector.start_run_sfa_check(single_detector.ts_analyzer.environment[function_id].function_code)
        #     analysis_result[function_id] = {
        #         "function_name": single_detector.ts_analyzer.environment[function_id].function_name,
        #         "function_code": single_detector.ts_analyzer.environment[function_id].function_code,
        #         "response": response
        #     }
        
        # with open(log_dir_path + "/analysis_result.json", "w") as f:
        #     json.dump(analysis_result, f, indent=4)
        return
    
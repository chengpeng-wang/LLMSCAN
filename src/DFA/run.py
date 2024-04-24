import concurrent.futures
import shutil
import os
import re
import time
from DFA import DFA
from typing import List
from pathlib import Path
from typing import Tuple
import json
from config import config
from datetime import datetime
import multiprocessing


def transform_function_split_cluster_files(file_cluster: List[str]) -> None:
    file_lines_dic = {}
    main_file = None
    for file_path in file_cluster:
        is_main_file = False
        trim_file_path = file_path.replace(".c", "")
        if trim_file_path.endswith("a"):
            main_file = file_path
            is_main_file = True
        with open(file_path, "r") as file:
            lines = file.readlines()
        transformed_lines = []
        if is_main_file:
            for line in lines:
                transformed_lines.append(line)
        else:
            for line in lines:
                if "#include" in line:
                    continue
                transformed_lines.append(line)
        file_lines_dic[file_path] = transformed_lines

    new_file_path = main_file.replace(".c", "")[0:-1] + ".c"
    new_lines = file_lines_dic[main_file]
    for file_path in file_lines_dic:
        if file_path == main_file:
            continue
        new_lines.extend(file_lines_dic[file_path])
    with open(new_file_path, "w") as file:
        for new_line in new_lines:
            file.write(new_line)
    return


class BatchRun:
    def __init__(
        self,
        src_spec_file: str,
        sink_spec_file: str,
        propagator_spec_file: str,
        validator_spec_file: str,
        project_name: str,
        online_model_name: str,
        offline_model_path: str,
        intra_reflexion: bool,
        is_path_sensitivity: bool,
        validate_reflexion: bool,
        is_solving_refine: bool,
        solving_refine_number: int,
        is_online: bool,
    ):
        self.src_spec_file = src_spec_file
        self.sink_spec_file = sink_spec_file
        self.propagator_spec_file = propagator_spec_file
        self.validator_spec_file = validator_spec_file
        self.project_name = project_name
        self.simplified_project_name = self.project_name + "_simplified"
        self.all_c_files = []
        self.analyzed_c_files = []

        self.online_model_name = online_model_name
        self.offline_model_path = offline_model_path

        self.intra_reflexion = intra_reflexion
        self.is_path_sensitivity = is_path_sensitivity
        self.validate_reflexion = validate_reflexion
        self.is_solving_refine = is_solving_refine
        self.solving_refine_number = solving_refine_number
        self.is_online = is_online

        self.batch_run_statistics = {}
        return

    def batch_transform_projects(self, main_test: str) -> None:
        cwd = Path(__file__).resolve().parent.parent.parent.absolute()
        full_project_name = cwd / "benchmark/C/" / self.project_name
        new_full_project_name = cwd / "benchmark/C/" / self.simplified_project_name

        if os.path.exists(new_full_project_name):
            shutil.rmtree(new_full_project_name)
        shutil.copytree(full_project_name, new_full_project_name)

        cluster_list = []
        history = set([])
        for root, dirs, files in os.walk(new_full_project_name):
            for file in files:
                if file.endswith(".c") and file.startswith("CWE"):
                    if not re.search(r"_\d+[a-z]$", file.replace(".c", "")):
                        continue
                    file_path = os.path.join(root, file)
                    match_str = file.replace(".c", "")[0:-1]
                    if file_path in history:
                        continue
                    cluster = [file_path]
                    history.add(file_path)

                    for root2, dirs2, files2 in os.walk(new_full_project_name):
                        for file2 in files2:
                            if file2 in history or "_base.c" in file2:
                                continue
                            full_path2 = os.path.join(root2, file2)
                            if file2.startswith(match_str) and (
                                full_path2 not in history
                            ):
                                cluster.append(full_path2)
                                history.add(full_path2)
                    cluster_list.append(cluster)
        for file_cluster in cluster_list:
            transform_function_split_cluster_files(file_cluster)

        for root, dirs, files in os.walk(new_full_project_name):
            for file in files:
                if file.endswith(".c") and file.startswith("CWE"):
                    if re.search(r"_\d+$", file.replace(".c", "")):
                        self.all_c_files.append(os.path.join(root, file))

        # Select typical test cases for analysis
        for full_c_file_path in self.all_c_files:
            if main_test in full_c_file_path:
                if re.search(r"_\d+$", full_c_file_path.replace(".c", "")):
                    self.analyzed_c_files.append(full_c_file_path)
            else:
                if "_01.c" in full_c_file_path:
                    self.analyzed_c_files.append(full_c_file_path)
        return

    @staticmethod
    def is_labeled(function_str: str, line_number: int):
        split_strs = function_str.split("\n")
        line_number = min(len(split_strs) - 1, line_number + 2)
        while 0 <= line_number <= len(split_strs) - 1:
            if "POTENTIAL FLAW:" in split_strs[line_number]:
                return True
            if "FIX:" in split_strs[line_number]:
                return False
            line_number = line_number - 1
        return False

    @staticmethod
    def examineBugReport(DFAEngine: DFA) -> Tuple[int, int, int, int, int, int]:
        positive_num = 1
        negative_num = 0
        for function_id in DFAEngine.environment.analyzed_functions:
            name = DFAEngine.environment.analyzed_functions[function_id].function_name
            if name == "good":
                negative_num += len(
                    DFAEngine.environment.analyzed_functions[
                        function_id
                    ].line_to_call_site_info
                )

        TPs = []
        FPs = []
        for function_src_id in DFAEngine.bugs:
            for bug_trace in DFAEngine.bugs[function_src_id]:
                isFP = False
                for function_id, local_value in bug_trace:
                    function_name = DFAEngine.environment.analyzed_functions[
                        function_id
                    ].function_name
                    if "good" in function_name or "Good" in function_name:
                        FPs.append(bug_trace)
                        isFP = True
                        break
                if not isFP:
                    (function_id_start, local_value_start) = bug_trace[0]
                    (function_id_end, local_value_end) = bug_trace[-1]
                    start_function = DFAEngine.environment.analyzed_functions[
                        function_id_start
                    ].original_function
                    end_function = DFAEngine.environment.analyzed_functions[
                        function_id_start
                    ].original_function

                    if BatchRun.is_labeled(
                        start_function, local_value_start.line_number
                    ) and BatchRun.is_labeled(
                        end_function, local_value_end.line_number
                    ):
                        TPs.append(bug_trace)
                    else:
                        FPs.append(bug_trace)
        TP_num = len(TPs)
        FP_num = len(FPs)

        path_insensitive_TPs = []
        path_insensitive_FPs = []
        for function_src_id in DFAEngine.bug_candidates:
            for bug_trace in DFAEngine.bug_candidates[function_src_id]:
                isFP = False
                for function_id, local_value in bug_trace:
                    function_name = DFAEngine.environment.analyzed_functions[
                        function_id
                    ].function_name
                    if "Good" in function_name or "good" in function_name:
                        path_insensitive_FPs.append(bug_trace)
                        isFP = True
                        break
                if not isFP:
                    (function_id_start, local_value_start) = bug_trace[0]
                    (function_id_end, local_value_end) = bug_trace[-1]
                    start_function = DFAEngine.environment.analyzed_functions[
                        function_id_start
                    ].original_function
                    end_function = DFAEngine.environment.analyzed_functions[
                        function_id_start
                    ].original_function
                    if BatchRun.is_labeled(
                        start_function, local_value_start.line_number
                    ) and BatchRun.is_labeled(
                        end_function, local_value_end.line_number
                    ):
                        path_insensitive_TPs.append(bug_trace)
                    else:
                        path_insensitive_FPs.append(bug_trace)
        path_insensitive_TP_num = len(path_insensitive_TPs)
        path_insensitive_FP_num = len(path_insensitive_FPs)
        return (
            TP_num,
            FP_num,
            path_insensitive_TP_num,
            path_insensitive_FP_num,
            positive_num,
            negative_num,
        )

    def startBatchRun(self, main_test: str) -> None:
        self.batch_transform_projects(main_test)
        total_input_token_cost = 0
        total_output_token_cost = 0
        total_time_cost = 0
        analysis_result = {}

        DFA_num = 0

        total_TP_num = 0
        total_FP_num = 0
        total_path_insensitive_TP_num = 0
        total_path_insensitive_FP_num = 0

        for c_file in self.analyzed_c_files:
            # CWE369_Divide_by_Zero__float_connect_socket_66, array parameter
            # CWE369_Divide_by_Zero__float_connect_socket_21
            # CWE369_Divide_by_Zero__float_connect_socket_61
            # CWE369_Divide_by_Zero__float_connect_socket_07
            # CWE369_Divide_by_Zero__float_connect_socket_68
            # CWE369_Divide_by_Zero__float_connect_socket_64
            # CWE369_Divide_by_Zero__float_connect_socket_63
            if "CWE369_Divide_by_Zero__float_connect_socket_66" not in c_file:
                continue

            # log_dir_path = str(Path(__file__).resolve().parent / "../../log/date/2023-11-28/")
            # proj_name = c_file[c_file.rfind("/") + 1:].replace(".c", "")
            # print(proj_name)
            # is_analyzed = False
            # for root, dirs, files in os.walk(log_dir_path):
            #     for d in dirs:
            #         if proj_name in d:
            #             is_analyzed = True
            #             break
            #     if is_analyzed:
            #         break
            # if is_analyzed:
            #     continue

            single_start_time = time.time()
            DFAEngine = DFA(
                c_file,
                self.src_spec_file,
                self.sink_spec_file,
                self.propagator_spec_file,
                self.validator_spec_file,
                self.online_model_name,
                self.offline_model_path,
                self.intra_reflexion,
                self.is_path_sensitivity,
                self.validate_reflexion,
                self.is_solving_refine,
                self.solving_refine_number,
                self.is_online,
                config.keys[0],
            )

            print("Start to analyze the case ", DFA_num)
            print(c_file)
            DFAEngine.analyze()
            DFAEngine.validate()
            DFAEngine.report()
            single_end_time = time.time()
            single_time_cost = single_end_time - single_start_time
            total_time_cost += single_time_cost

            (
                TP_num,
                FP_num,
                path_insensitive_TP_num,
                path_insensitive_FP_num,
                positive_num,
                negative_num,
            ) = BatchRun.examineBugReport(DFAEngine)
            input_token_cost, output_token_cost = DFAEngine.compute_total_token_cost()
            total_input_token_cost += input_token_cost
            total_output_token_cost += output_token_cost
            analysis_result[c_file] = {
                "input_token_cost": input_token_cost,
                "output_token_cost": output_token_cost,
                "TP_num": TP_num,
                "FP_num": FP_num,
                "path_insensitive_TP_num": path_insensitive_TP_num,
                "path_insensitive_FP_num": path_insensitive_FP_num,
                "positive_num": positive_num,
                "negative_num": negative_num,
                "single time cost": single_time_cost,
            }
            print(analysis_result[c_file])

            DFA_num += 1

            total_TP_num += TP_num
            total_FP_num += FP_num
            total_path_insensitive_TP_num += path_insensitive_TP_num
            total_path_insensitive_FP_num += path_insensitive_FP_num
            break

        if total_TP_num + total_FP_num > 0:
            precision = total_TP_num * 1.0 / (total_TP_num + total_FP_num)
        else:
            precision = 0
        recall = total_TP_num * 1.0 / DFA_num

        if total_path_insensitive_TP_num + total_path_insensitive_FP_num > 0:
            insensitive_precision = (
                total_path_insensitive_TP_num
                * 1.0
                / (total_path_insensitive_TP_num + total_path_insensitive_FP_num)
            )
        else:
            insensitive_precision = 0
        insensitive_recall = total_path_insensitive_TP_num * 1.0 / DFA_num

        financial_cost = (
            0.0010 * total_input_token_cost * 1.0 / 1000
            + 0.0020 * total_input_token_cost * 1.0 / 1000
        ) / 10

        self.batch_run_statistics = {
            "token cost": {
                "input": total_input_token_cost,
                "output": total_output_token_cost,
            },
            "financial cost": financial_cost,
            "total time cost": total_time_cost,
            "report": analysis_result,
            "precision": precision,
            "recall": recall,
            "insensitive_precision": insensitive_precision,
            "insensitive_recall": insensitive_recall,
            "total_TP_num": total_TP_num,
            "total_FP_num": total_FP_num,
            "total_path_insensitive_TP_num": total_path_insensitive_TP_num,
            "total_path_insensitive_FP_num": total_path_insensitive_FP_num,
            "Case number": DFA_num,
        }

        log_dir_path = str(Path(__file__).resolve().parent / "../../log/")
        current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        with open(
            log_dir_path + "/summary_report_" + current_time + ".json", "w"
        ) as file:
            json.dump(self.batch_run_statistics, file, indent=4)
        return


if __name__ == "__main__":
    online_model_name = "gpt-3.5-turbo-1106"
    offline_model_path = "/home/chengpeng/LMFlow/output_models/finetuned_CodeLlama-7b-Instruct-hf_dbz_src"
    intra_reflexion = False
    is_path_sensitivity = True
    validate_reflexion = False
    is_solving_refine = True
    solving_refine_number = 5
    is_online = True

    project_name = "juliet-test-suite-DBZ"
    main_test = "CWE369_Divide_by_Zero__float_connect_socket"
    src_spec = "spec/dbz_source.json"
    sink_spec = "spec/dbz_sink.json"
    propagator_spec = "flow/eq_flow_propagator.json"
    validator_spec = "flow/eq_flow_validator.json"

    batch_run = BatchRun(
        src_spec,
        sink_spec,
        propagator_spec,
        validator_spec,
        project_name,
        online_model_name,
        offline_model_path,
        intra_reflexion,
        is_path_sensitivity,
        validate_reflexion,
        is_solving_refine,
        solving_refine_number,
        is_online,
    )

    batch_run.startBatchRun(main_test)

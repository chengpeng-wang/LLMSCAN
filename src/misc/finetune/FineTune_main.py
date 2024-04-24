from finetune.dbz_src_data import *

if __name__ == "__main__":
    fine_tune_data_size = 4000
    produce_response_data(fine_tune_data_size)
    prepare_fine_tune_dbz_src_data()

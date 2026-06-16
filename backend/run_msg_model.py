#run_msg_model.py
import os
import importlib.util
import time
import tempfile # For inserting logs in runtime - PENDING

def solve_message_scenario(scenario_path, output_path):
    """
    Solves a MESSAGEix scenario and saves the results to an Excel file.
    Input: scenario_path (str): Path to the input Excel file containing the MESSAGEix scenario data.
           output_path (str): Path where the solved scenario Excel file will be saved.
    Output: dict with keys "success" (bool) and "objective_value" (float or None)
    """
    start_time = time.time()

    # PATH injection first
    spec = importlib.util.find_spec("gamspy_base")
    if spec and spec.origin:
        gams_dir = os.path.dirname(spec.origin)
        os.environ["PATH"] = gams_dir + os.pathsep + os.environ.get("PATH", "")
        os.environ["GAMS_PATH"] = gams_dir
        os.environ["GAMSDIR"] = gams_dir
    
    with tempfile.TemporaryDirectory() as temp_dir:
        log_path = os.path.join(temp_dir, "gams_output.log")

    import ixmp
    import message_ix
    
    mp = None
    try:
        mp = ixmp.Platform()
        print("mp connected:", mp)

        # Create a clean throwaway scenario — no cloning from existing
        scenario = message_ix.Scenario(
            mp,
            model="__temp__",
            scenario="__temp__",
            version="new",
            annotation="throwaway"
        )
        print("Scenario object created")

        print("Reading scenario from:", scenario_path)
        # Read all data in from Excel and commit it
        scenario.read_excel(
            str(scenario_path),
            add_units=True,
            commit_steps=True,   # commits as it reads, no manual commit needed
            init_items=True
        )
        print("Scenario read from Excel and committed to database")

        # Solve
        case_name = f"temp__{scenario.version}"
        scenario.solve(case=case_name)
        
        obj_val = scenario.var("OBJ")["lvl"]
        scenario.to_excel(str(output_path))

        end_time = time.time()
        execution_time = round((end_time - start_time), 2)
        return {"error_flag": 0, "objective_value": obj_val, "agent_execution_time": execution_time}

    except Exception as e:
        print("Error in solve_message_scenario:", e)
        end_time = time.time()
        execution_time = round((end_time - start_time), 2)
        return {"error_flag": 1, "objective_value": None, "agent_execution_time": execution_time}
    
    finally:
        if mp is not None:
            mp.close_db()



# res= solve_message_scenario(r"D:\\lums-python-programming\\thesis\\message-ix\\westeros_baseline.xlsx", r"D:\\lums-python-programming\\thesis\\message-ix\\westeros_baseline_solved.xlsx")
# if res:
#     b=res.get("error_flag", 1)
#     r=res.get("objective_value", None)
#     if b == 0:
#         print("Model solved successfully! Objective value:", r)
#     else:    
#         print("Model solving failed.")
# else:
#     print("Model not solved.")
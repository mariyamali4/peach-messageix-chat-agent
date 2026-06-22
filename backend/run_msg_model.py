#run_msg_model.py
import os
import importlib.util
import time

from pathlib import Path
import jpype

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
    else:
        print("WARNING: gamspy_base not found. GAMS path not set.")


    # JVM detection 
    if not os.environ.get("JAVA_HOME"):
        try:
            jvm_path = jpype.getDefaultJVMPath()
            os.environ["JAVA_HOME"] = os.path.dirname(os.path.dirname(jvm_path))
            print(f"JAVA_HOME set to: {os.environ['JAVA_HOME']}")
        except Exception as e:
            print(f"JVM detection failed: {e}")

    # HSQLDB path — self-contained inside /tmp/ 
    # /tmp/ is writable on Streamlit Cloud.
    ixmp_db_path = Path("/tmp/ixmp_db/default")
    ixmp_db_path.parent.mkdir(parents=True, exist_ok=True)


    import ixmp
    import message_ix
    
    mp = None
    try:
        mp = ixmp.Platform(
            backend="jdbc",
            driver="hsqldb",
            path=str(ixmp_db_path)
        )
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

        os.makedirs(os.path.dirname(output_path), exist_ok=True)  # making sure the output directory exists
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